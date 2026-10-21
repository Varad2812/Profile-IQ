"""
Face Analysis Module — ProfileIQ
Real AI-based face analysis using DeepFace + OpenCV.
Replaces mock face_score with actual image analysis.
"""

import logging
import tempfile
import os
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Image fetching
# ---------------------------------------------------------------------------

def _fetch_image_to_temp(image_url: str) -> str | None:
    """Download image from URL to a temp file. Returns path or None on failure."""
    try:
        import requests
        resp = requests.get(image_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        suffix = ".jpg"
        if "png" in resp.headers.get("Content-Type", ""):
            suffix = ".png"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.warning(f"[FaceAnalysis] Image fetch failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Image quality check (OpenCV)
# ---------------------------------------------------------------------------

def _check_image_quality(img_path: str) -> dict:
    """
    Returns:
        resolution_ok: bool — image is at least 100x100
        blur_score: float  — Laplacian variance (higher = sharper)
        is_blurry: bool    — blur_score < 80
    """
    try:
        import cv2
        img = cv2.imread(img_path)
        if img is None:
            return {"resolution_ok": False, "blur_score": 0.0, "is_blurry": True}
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        return {
            "resolution_ok": h >= 100 and w >= 100,
            "blur_score": round(blur_score, 2),
            "is_blurry": blur_score < 80.0,
        }
    except Exception as e:
        logger.warning(f"[FaceAnalysis] Quality check failed: {e}")
        return {"resolution_ok": False, "blur_score": 0.0, "is_blurry": True}


# ---------------------------------------------------------------------------
# Core DeepFace analysis
# ---------------------------------------------------------------------------

def _run_deepface(img_path: str) -> dict:
    """
    Runs DeepFace.detect_faces + analyze on the image.
    Returns raw results or empty dict on failure.
    """
    try:
        from deepface import DeepFace

        # Detect faces — returns list of face regions
        faces = DeepFace.extract_faces(
            img_path=img_path,
            detector_backend="ssd",
            enforce_detection=False,
        )

        if not faces:
            return {"faces_found": 0}

        # Filter faces with confidence > 0.5
        confident_faces = [f for f in faces if f.get("confidence", 0) > 0.5]
        face_count = len(confident_faces)
        
        if face_count == 0:
            return {"faces_found": 0}
            
        best_confidence = max((f.get("confidence", 0) for f in confident_faces), default=0.0)

        # Analyze best face for attributes
        analysis = DeepFace.analyze(
            img_path=img_path,
            actions=["age", "gender", "emotion"],
            detector_backend="ssd",
            enforce_detection=False,
            silent=True,
        )

        # analyze() returns list or dict depending on version
        result = analysis[0] if isinstance(analysis, list) else analysis

        dominant_emotion = result.get("dominant_emotion", "unknown")
        dominant_gender = result.get("dominant_gender", result.get("gender", "unknown"))
        age = result.get("age", 0)

        # Normalize gender output (DeepFace returns "Man"/"Woman" or dict)
        if isinstance(dominant_gender, dict):
            dominant_gender = max(dominant_gender, key=dominant_gender.get)

        return {
            "faces_found": face_count,
            "best_confidence": round(float(best_confidence), 3),
            "age": int(age),
            "gender": str(dominant_gender),
            "dominant_emotion": str(dominant_emotion),
            "emotion_scores": result.get("emotion", {}),
        }

    except Exception as e:
        logger.warning(f"[FaceAnalysis] DeepFace failed: {e}")
        return {"faces_found": 0, "error": str(e)}


# ---------------------------------------------------------------------------
# Authenticity scoring heuristics
# ---------------------------------------------------------------------------

def _compute_face_score(deepface_result: dict, quality: dict) -> tuple[int, list[str]]:
    """
    Compute 0–100 authenticity score from heuristics.

    Scoring breakdown:
      +30  face detected
      +20  high detection confidence (> 0.75)
      +20  image is clear (not blurry) and sufficient resolution
      +10  emotion variety (not stuck on neutral)
      +10  single face (not multiple — reduces suspicion)
      -20  multiple faces detected
      -10  low resolution
      -10  blurry image
      -15  no face detected at all
    """
    flags = []
    score = 0

    faces_found = deepface_result.get("faces_found", 0)
    confidence = deepface_result.get("best_confidence", 0.0)
    emotion = deepface_result.get("dominant_emotion", "neutral")
    emotion_scores = deepface_result.get("emotion_scores", {})

    # Face detection
    if faces_found == 0:
        flags.append("no_face_detected")
        score += 10  # base fallback
    elif faces_found == 1:
        score += 30
        if confidence > 0.75:
            score += 20
        elif confidence > 0.5:
            score += 10
    else:
        # Multiple faces — suspicious for a profile photo
        score += 20
        flags.append("multiple_faces")
        score -= 20

    # Image quality
    if not quality.get("resolution_ok"):
        flags.append("low_resolution")
        score -= 10
    else:
        score += 10

    if quality.get("is_blurry"):
        flags.append("blurry_image")
        score -= 10
    else:
        score += 10

    # Emotion variety — neutral-only is suspicious (stock/AI images tend to be neutral)
    if emotion_scores:
        neutral_pct = emotion_scores.get("neutral", 0)
        if neutral_pct > 90:
            flags.append("neutral_only_emotion")
        else:
            score += 10
    elif emotion == "neutral":
        pass  # no bonus, no penalty
    else:
        score += 10  # non-neutral emotion detected — more likely real

    # Clamp to 0–100
    score = max(0, min(100, score))
    return score, flags


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_face(image_url: str) -> dict:
    """
    URL pipeline: download image then analyze.
    """
    img_path = None
    try:
        img_path = _fetch_image_to_temp(image_url)
        if not img_path:
            return _fallback("image_fetch_failed")
        return _analyze_from_path(img_path)
    except Exception as e:
        logger.error(f"[FaceAnalysis] Unexpected error: {e}")
        return _fallback("analysis_error")
    finally:
        _cleanup(img_path)


def analyze_face_from_path(img_path: str, extra_flags: list = None) -> dict:
    """
    Screenshot pipeline: image already saved to disk by image_processor.
    Caller is responsible for deleting the file after use.
    """
    try:
        result = _analyze_from_path(img_path)
        if extra_flags:
            result["flags"] = list(set(result["flags"] + extra_flags))
        return result
    except Exception as e:
        logger.error(f"[FaceAnalysis] Unexpected error: {e}")
        return _fallback("analysis_error")


def _analyze_from_path(img_path: str) -> dict:
    """Shared core: quality check + DeepFace + scoring."""
    quality = _check_image_quality(img_path)
    deepface_result = _run_deepface(img_path)
    face_score, flags = _compute_face_score(deepface_result, quality)
    return {
        "face_score": face_score,
        "age": deepface_result.get("age", 0),
        "gender": deepface_result.get("gender", "unknown"),
        "emotion": deepface_result.get("dominant_emotion", "unknown"),
        "confidence": deepface_result.get("best_confidence", 0.0),
        "flags": flags,
        "source": "deepface",
    }


def _cleanup(path):
    if path and os.path.exists(path):
        try:
            os.unlink(path)
        except Exception:
            pass


def _fallback(reason: str) -> dict:
    """Safe fallback when analysis cannot complete."""
    logger.warning(f"[FaceAnalysis] Using fallback score. Reason: {reason}")
    return {
        "face_score": 25,
        "age": 0,
        "gender": "unknown",
        "emotion": "unknown",
        "confidence": 0.0,
        "flags": [reason],
        "source": "fallback",
    }
