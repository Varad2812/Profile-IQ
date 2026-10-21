import os
import re
import base64
import logging
import asyncio
import tempfile
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db, Analysis, ModuleScores, EvidenceLog, User
from models.schemas import AnalysisOut, OcrDataOut, GenericResponse
from utils.auth import get_current_user
from utils.limiter import limiter
from services.analyzer import analyze_profile
from services.image_processor import process_screenshot
from services.ocr_service import extract_profile_data
from services.text_analysis import analyze_text
from services.instagram_profile import (
    InstagramProfileError,
    fetch_instagram_profile,
    get_session_status,
    has_saved_session,
    is_instagram_profile_url,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE  = 10 * 1024 * 1024   # 10 MB
_URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _err(status: int, message: str):
    raise HTTPException(
        status_code=status,
        detail={"success": False, "message": message, "error_code": status},
    )


def _build_ocr_data(analysis: Analysis) -> OcrDataOut:
    return OcrDataOut(
        platform=analysis.ocr_platform or "unknown",
        username=analysis.ocr_username or "",
        bio=analysis.ocr_bio or "",
        followers=analysis.ocr_followers or "",
        following=analysis.ocr_following or "",
        posts=analysis.ocr_posts or "",
        confidence=analysis.ocr_confidence or 0.0,
        raw_text=analysis.ocr_raw_text or "",
        ocr_available=bool(analysis.ocr_platform and analysis.ocr_platform != "unknown"),
        error=analysis.ocr_error or None,
    )


def _to_response(analysis: Analysis) -> AnalysisOut:
    out = AnalysisOut.from_orm(analysis)
    out.ocr_data = _build_ocr_data(analysis)
    if out.module_scores and out.ocr_data:
        out.module_scores.platform = out.ocr_data.platform or "unknown"
    return out


def _save_analysis(db, current_user, profile_url, input_type,
                   profile_image_b64, result, ocr: dict = None):
    try:
        ms  = result["module_scores"]
        ocr = ocr or {}

        analysis = Analysis(
            user_id=current_user.id,
            profile_url=profile_url,
            input_type=input_type,
            profile_image_b64=profile_image_b64,
            trust_score=result["trust_score"],
            confidence=result["confidence"],
            risk_level=result["risk_level"],
            summary=result["summary"],
            ocr_platform=ocr.get("platform", "unknown"),
            ocr_username=ocr.get("username", ""),
            ocr_bio=ocr.get("bio", ""),
            ocr_followers=ocr.get("followers", ""),
            ocr_following=ocr.get("following", ""),
            ocr_posts=ocr.get("posts", ""),
            ocr_confidence=ocr.get("confidence", 0.0),
            ocr_raw_text=ocr.get("raw_text", ""),
            ocr_error=ocr.get("error", ""),
        )
        db.add(analysis)
        db.flush()

        db.add(ModuleScores(
            analysis_id=analysis.id,
            face_score=ms["face_score"],
            text_score=ms["text_score"],
            behavior_score=ms["behavior_score"],
            network_score=ms["network_score"],
            consistency_score=ms["consistency_score"],
            identity_score=ms["identity_score"],
            face_age=ms["face_age"],
            face_gender=ms["face_gender"],
            face_emotion=ms["face_emotion"],
            face_flags=ms["face_flags"],
            face_source=ms["face_source"],
            text_classification=ms.get("text_classification", "unknown"),
            text_scam_prob=ms.get("text_scam_prob", 0.0),
            text_ai_prob=ms.get("text_ai_prob", 0.0),
            text_flags=ms.get("text_flags", ""),
            text_scam_keywords=ms.get("text_scam_keywords", ""),
            text_source=ms.get("text_source", "mock"),
            behavior_anomaly_score=ms.get("behavior_anomaly_score", 0.0),
            behavior_flags=ms.get("behavior_flags", ""),
            behavior_source=ms.get("behavior_source", "mock"),
            profile_type=ms.get("profile_type", "unknown"),
            profile_entities=ms.get("profile_entities", ""),
            profile_summary=ms.get("profile_summary", ""),
            profile_type_confidence=ms.get("profile_type_confidence", 0.0),
            identity_matches=ms.get("identity_matches", 0),
            identity_face_matches=ms.get("identity_face_matches", 0),
            identity_risk_flags=ms.get("identity_risk_flags", ""),
            identity_platforms=ms.get("identity_platforms", ""),
        ))

        for log in result["evidence_logs"]:
            db.add(EvidenceLog(analysis_id=analysis.id, **log))

        db.commit()
        db.refresh(analysis)
        logger.info(f"[ANALYZE] DB save success for ID={analysis.id}")
        return analysis
    except Exception as e:
        db.rollback()
        logger.error(f"[ANALYZE] DB save failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": f"Database persistence failed: {str(e)}", "error_code": 500}
        )


# ── URL-based analysis ────────────────────────────────────────────────────────

def _extract_username_from_url(url: str) -> str:
    """Extract username from a social media profile URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        if parts:
            # Handle /in/username for LinkedIn
            if parts[0].lower() == "in" and len(parts) > 1:
                return parts[1].strip("@")
            return parts[-1].strip("@")
    except Exception:
        pass
    return ""


def _fetch_profile_image_b64(image_url: str) -> str:
    """Download a profile image URL and return as data-URI base64."""
    if not image_url:
        return ""
    try:
        import requests
        resp = requests.get(image_url, timeout=5, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0"
        })
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            ct = resp.headers["content-type"].split(";")[0]
            b64 = base64.b64encode(resp.content[:200_000]).decode()
            return f"data:{ct};base64,{b64}"
    except Exception as e:
        logger.debug(f"[Route] Profile image fetch failed: {e}")
    return ""


@router.post("/analyze", response_model=GenericResponse[AnalysisOut])
@limiter.limit("5/minute")
async def analyze_via_url(
    request: Request,
    profile_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    url = profile_url.strip()
    if not url:
        _err(400, "profile_url is required")

    # Auto-prepend https:// if user omitted the protocol
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if not _URL_RE.match(url):
        _err(400, "Invalid URL format. Please enter a valid profile URL (e.g. https://instagram.com/username)")

    logger.info(f"[Route] URL analysis requested by user={current_user.id} url={url}")

    profile_data = {}
    extraction_logs = []
    profile_image_b64 = ""

    if "instagram.com" in url.lower():
        if not is_instagram_profile_url(url):
            _err(400, "Only direct Instagram profile URLs are supported, for example https://instagram.com/username")

        if not has_saved_session():
            # Gracefully degrade: proceed without Instagram data instead of blocking
            logger.warning("[Route] No Instagram session — proceeding with limited analysis")
            extraction_logs.append({
                "log_type": "warning",
                "module": "Profile Extraction",
                "message": (
                    "Instagram login session is not configured — analysis is based on "
                    "limited public signals. For full results, set up the Instagram "
                    "session and try again."
                ),
            })
            # Extract username from URL for cross-platform checks
            username = _extract_username_from_url(url)
            if username:
                profile_data = {
                    "platform": "instagram",
                    "username": username,
                }
        else:
            try:
                profile_data = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: fetch_instagram_profile(url)
                )
                source_note = "cached" if profile_data.get("from_cache") else "logged-in browser session"
                extraction_logs.append({
                    "log_type": "positive",
                    "module": "Profile Extraction",
                    "message": f"Instagram public profile metadata extracted using {source_note}",
                })
            except InstagramProfileError as e:
                logger.warning(f"[Route] Instagram extraction unavailable: {e}")
                extraction_logs.append({
                    "log_type": "warning",
                    "module": "Profile Extraction",
                    "message": f"Instagram data extraction unavailable: {e}. Analysis continues with limited data.",
                })
                username = _extract_username_from_url(url)
                if username:
                    profile_data = {"platform": "instagram", "username": username}
            except Exception as e:
                logger.exception("[Route] Instagram extraction failed")
                extraction_logs.append({
                    "log_type": "warning",
                    "module": "Profile Extraction",
                    "message": f"Instagram extraction failed: {e}. Analysis continues with limited data.",
                })
                username = _extract_username_from_url(url)
                if username:
                    profile_data = {"platform": "instagram", "username": username}
    else:
        # Non-Instagram URL: extract username for cross-platform enrichment
        username = _extract_username_from_url(url)
        if username:
            profile_data["username"] = username

    # Try to get a profile image b64 for the result card
    img_url = profile_data.get("profile_image_url", "")
    if img_url:
        profile_image_b64 = await asyncio.get_event_loop().run_in_executor(
            None, lambda: _fetch_profile_image_b64(img_url)
        )

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: analyze_profile(
            profile_url=url,
            image_path=None,
            bio=profile_data.get("bio", ""),
            ocr_data=profile_data,
        )
    )

    result["evidence_logs"].extend(extraction_logs)
    
    analysis = _save_analysis(db, current_user, url, "url", profile_image_b64, result, profile_data)
    return {"success": True, "data": _to_response(analysis)}


@router.get("/instagram/session-status", response_model=GenericResponse[dict])
def instagram_session_status(
    current_user: User = Depends(get_current_user),
):
    return {"success": True, "data": get_session_status()}


# ── Screenshot-based analysis ─────────────────────────────────────────────────

@router.post("/analyze/screenshot", response_model=GenericResponse[AnalysisOut])
@limiter.limit("5/minute")
async def analyze_via_screenshot(
    request: Request,
    file: UploadFile = File(...),
    profile_url: str = Form(default="screenshot_upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        _err(400, f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, WEBP")

    image_bytes = await file.read()

    if len(image_bytes) > MAX_FILE_SIZE:
        _err(400, "File too large. Max 10 MB.")
    if len(image_bytes) < 1000:
        _err(400, "File too small or empty.")

    ext = "jpeg" if "jpeg" in file.content_type or "jpg" in file.content_type else "png"
    profile_image_b64 = f"data:image/{ext};base64," + base64.b64encode(image_bytes[:200_000]).decode()

    logger.info(f"[Route] Screenshot analysis requested by user={current_user.id}")

    # ── Run OCR in thread pool (non-blocking) ─────────────────────────────
    ocr_result: dict = {}
    try:
        ocr_result = await asyncio.get_event_loop().run_in_executor(
            None, extract_profile_data, image_bytes
        )
        logger.info(f"[Route] OCR done: platform={ocr_result.get('platform')} user={ocr_result.get('username')!r}")

        if not ocr_result.get("ocr_available") and ocr_result.get("error"):
            logger.warning(f"[Route] OCR unavailable: {ocr_result['error']}")
            ocr_result["ocr_status"] = "unavailable"

        if ocr_result.get("username") and profile_url == "screenshot_upload":
            platform = ocr_result.get("platform", "unknown")
            profile_url = f"{platform}:{ocr_result['username']}"

    except Exception as e:
        logger.error(f"[Route] OCR error (non-fatal): {e}")
        ocr_result = {
            "error": str(e),
            "ocr_status": "unavailable",
            "ocr_available": False,
        }

    # ── Face processing ───────────────────────────────────────────────────
    proc = process_screenshot(image_bytes)
    tmp_path = proc.get("temp_path")

    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: analyze_profile(
                profile_url=profile_url,
                image_path=tmp_path,
                bio=ocr_result.get("bio", ""),
                ocr_data=ocr_result,
            ),
        )

        extra_flags = proc.get("flags", [])
        if extra_flags:
            existing = result["module_scores"]["face_flags"]
            result["module_scores"]["face_flags"] = ",".join(filter(None, [existing] + extra_flags))

        # Append OCR-derived evidence logs
        if ocr_result.get("platform") and ocr_result["platform"] != "unknown":
            result["evidence_logs"].append({
                "log_type": "positive",
                "module": "Text Analysis",
                "message": (
                    f"Platform detected as {ocr_result['platform'].title()} "
                    f"with {int(ocr_result.get('confidence', 0) * 100)}% confidence"
                ),
            })
        if ocr_result.get("username"):
            result["evidence_logs"].append({
                "log_type": "positive",
                "module": "Identity Verification",
                "message": f"Username extracted from screenshot: @{ocr_result['username']}",
            })
        if ocr_result.get("ocr_status") == "unavailable":
            result["evidence_logs"].append({
                "log_type": "warning",
                "module": "Text Analysis",
                "message": "OCR unavailable — install Tesseract for full text extraction",
            })

        analysis = _save_analysis(
            db, current_user, profile_url, "screenshot",
            profile_image_b64, result, ocr_result,
        )
        return {"success": True, "data": _to_response(analysis)}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Single analysis ───────────────────────────────────────────────────────────

@router.get("/analysis/{analysis_id}", response_model=GenericResponse[AnalysisOut])
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        _err(404, "Analysis not found")
    if analysis.user_id != current_user.id and current_user.role != "admin":
        _err(403, "Access denied")
    return {"success": True, "data": _to_response(analysis)}


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history", response_model=GenericResponse[List[AnalysisOut]])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .outerjoin(ModuleScores) # Ensure it works even if scores missing
        .order_by(Analysis.created_at.desc())
        .all()
    )
    return {"success": True, "data": [_to_response(a) for a in analyses]}
