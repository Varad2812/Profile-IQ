"""
OCR Service — ProfileIQ
Extracts text from profile screenshots using Tesseract OCR + OpenCV preprocessing.
Detects platform, username, bio, and follower metadata from raw text.

Gracefully degrades if Tesseract is not installed.
"""

import re
import logging
import unicodedata
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ── Tesseract setup ────────────────────────────────────────────────────────────

_TESSERACT_AVAILABLE = False
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\a\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]

try:
    import pytesseract

    # Try to find tesseract binary
    import shutil
    tess_path = shutil.which("tesseract")
    if not tess_path:
        for p in _TESSERACT_PATHS:
            import os
            if os.path.exists(p):
                tess_path = p
                break

    if tess_path:
        pytesseract.pytesseract.tesseract_cmd = tess_path
        # Quick smoke test
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
        logger.info(f"[OCR] Tesseract found at: {tess_path}")
    else:
        logger.warning("[OCR] Tesseract binary not found. OCR will be disabled.")
except Exception as e:
    logger.warning(f"[OCR] Tesseract unavailable: {e}")


# ── Platform detection rules ───────────────────────────────────────────────────

_PLATFORM_RULES = {
    "instagram": {
        "keywords": ["followers", "following", "posts", "instagram", "reels", "story", "highlights"],
        "strong":   ["posts", "reels", "highlights"],
        "weight":   1.0,
    },
    "twitter": {
        "keywords": ["tweets", "followers", "following", "twitter", "retweets", "likes", "replies", "x.com"],
        "strong":   ["tweets", "retweets", "x.com"],
        "weight":   1.0,
    },
    "linkedin": {
        "keywords": ["connections", "experience", "education", "linkedin", "skills", "endorsements", "connect", "message"],
        "strong":   ["connections", "experience", "endorsements"],
        "weight":   1.0,
    },
    "facebook": {
        "keywords": ["friends", "facebook", "timeline", "add friend", "like", "share", "groups"],
        "strong":   ["add friend", "timeline"],
        "weight":   1.0,
    },
    "tiktok": {
        "keywords": ["tiktok", "likes", "following", "followers", "videos", "fyp"],
        "strong":   ["tiktok", "fyp"],
        "weight":   1.0,
    },
}


def _detect_platform(text: str) -> dict:
    lower = text.lower()
    scores = {}

    for platform, rules in _PLATFORM_RULES.items():
        score = 0.0
        matched_keywords = [kw for kw in rules["keywords"] if kw in lower]
        matched_strong   = [kw for kw in rules["strong"]   if kw in lower]

        score += len(matched_keywords) * 0.15
        score += len(matched_strong)   * 0.30
        scores[platform] = min(score, 1.0)

    if not scores or max(scores.values()) < 0.15:
        return {"platform": "unknown", "confidence": 0.0}

    best = max(scores, key=scores.get)
    return {"platform": best, "confidence": round(scores[best], 2)}


# ── Username extraction ────────────────────────────────────────────────────────

def _extract_username(text: str, platform: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # @handle pattern — works for all platforms
    at_match = re.search(r"@([\w._]{2,30})", text)
    if at_match:
        return at_match.group(1)

    # Instagram / Twitter: username often on first 1–3 non-empty lines
    if platform in ("instagram", "twitter", "tiktok"):
        for line in lines[:5]:
            # Skip lines that look like counts or UI labels
            if re.search(r"\d{1,3}[KkMm]?\s*(followers|following|posts|tweets|likes)", line, re.I):
                continue
            if len(line) < 3 or len(line) > 40:
                continue
            # Likely a username/display name
            cleaned = re.sub(r"[^a-zA-Z0-9._\- ]", "", line).strip()
            if cleaned:
                return cleaned.split()[0]  # first word = username

    # LinkedIn: name is usually the first prominent line
    if platform == "linkedin":
        for line in lines[:4]:
            if len(line) > 3 and not re.search(r"\d", line):
                return line

    return ""


# ── Bio extraction ─────────────────────────────────────────────────────────────

def _extract_bio(text: str, username: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Skip lines that are counts, labels, or the username itself
    skip_patterns = [
        r"^\d+[\.,]?\d*\s*[KkMm]?$",                          # pure numbers
        r"\d+\s*(followers|following|posts|tweets|connections)", # stat lines
        r"^(followers|following|posts|tweets|likes|views)$",    # label-only
        r"^@",                                                   # @handle line
    ]

    bio_lines = []
    found_username = False

    for line in lines:
        # Skip the username line itself
        if username and username.lower() in line.lower():
            found_username = True
            continue

        skip = any(re.search(p, line, re.I) for p in skip_patterns)
        if skip:
            continue

        if len(line) > 3:
            bio_lines.append(line)
            if len(bio_lines) >= 3:
                break

    return " | ".join(bio_lines[:3]) if bio_lines else ""


# ── Follower/count extraction ──────────────────────────────────────────────────

def _extract_counts(text: str) -> dict:
    counts = {"followers": "", "following": "", "posts": ""}

    patterns = {
        "followers": r"([\d,\.]+\s*[KkMm]?)\s*[Ff]ollowers",
        "following": r"([\d,\.]+\s*[KkMm]?)\s*[Ff]ollowing",
        "posts":     r"([\d,\.]+\s*[KkMm]?)\s*[Pp]osts",
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, text)
        if m:
            counts[key] = m.group(1).strip()

    return counts


# ── Text cleaning ──────────────────────────────────────────────────────────────

def _clean_text(raw: str) -> str:
    # Normalize unicode (remove combining chars, keep printable)
    normalized = unicodedata.normalize("NFKD", raw)
    # Remove non-printable except newlines/spaces
    cleaned = re.sub(r"[^\x20-\x7E\n]", " ", normalized)
    # Collapse multiple spaces/newlines
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ── Image preprocessing ────────────────────────────────────────────────────────

def _preprocess_for_ocr(image_bytes: bytes) -> Optional[Image.Image]:
    """
    OpenCV preprocessing pipeline for better OCR accuracy:
    1. Decode bytes → BGR
    2. Upscale if small
    3. Convert to grayscale
    4. Adaptive threshold (handles uneven lighting)
    5. Denoise
    6. Return as PIL Image
    """
    try:
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        h, w = img.shape[:2]

        # Upscale small images for better OCR
        if w < 800:
            scale = 800 / w
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold — handles dark/light backgrounds
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31,
            C=10,
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, h=10)

        return Image.fromarray(denoised)

    except Exception as e:
        logger.warning(f"[OCR] Preprocessing failed: {e}")
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_profile_data(image_bytes: bytes) -> dict:
    """
    Main OCR entry point.

    Args:
        image_bytes: raw bytes of uploaded screenshot

    Returns:
    {
        "platform":   str,    # instagram | twitter | linkedin | facebook | tiktok | unknown
        "username":   str,
        "bio":        str,
        "followers":  str,
        "following":  str,
        "posts":      str,
        "confidence": float,  # platform detection confidence
        "raw_text":   str,
        "ocr_available": bool,
        "error":      str | None,
    }
    """
    base = {
        "platform": "unknown", "username": "", "bio": "",
        "followers": "", "following": "", "posts": "",
        "confidence": 0.0, "raw_text": "", "ocr_available": _TESSERACT_AVAILABLE,
        "ocr_status": "ready" if _TESSERACT_AVAILABLE else "unavailable",
        "error": None,
    }

    if not _TESSERACT_AVAILABLE:
        logger.warning("[OCR] extract_profile_data called but Tesseract is not available")
        base["error"] = "Tesseract OCR not installed. Install from https://github.com/UB-Mannheim/tesseract/wiki"
        return base

    try:
        # 1. Preprocess image
        pil_img = _preprocess_for_ocr(image_bytes)
        if pil_img is None:
            base["error"] = "Image preprocessing failed"
            return base

        # 2. Run OCR
        import pytesseract
        raw_text = pytesseract.image_to_string(
            pil_img,
            config="--psm 6 --oem 3",   # psm 6 = uniform block of text
        )

        if not raw_text.strip():
            base["error"] = "No text extracted from image"
            return base

        # 3. Clean text
        clean = _clean_text(raw_text)

        # 4. Platform detection
        platform_result = _detect_platform(clean)
        platform   = platform_result["platform"]
        confidence = platform_result["confidence"]

        # 5. Extract structured fields
        username = _extract_username(clean, platform)
        bio      = _extract_bio(clean, username)
        counts   = _extract_counts(clean)

        logger.info(f"[OCR] Platform={platform} ({confidence}) | User={username!r} | Bio={bio[:40]!r}")

        return {
            "platform":      platform,
            "username":      username,
            "bio":           bio,
            "followers":     counts["followers"],
            "following":     counts["following"],
            "posts":         counts["posts"],
            "confidence":    confidence,
            "raw_text":      clean[:2000],   # cap stored raw text
            "ocr_available": True,
            "ocr_status":    "ready",
            "error":         None,
        }

    except Exception as e:
        logger.error(f"[OCR] Unexpected error: {e}")
        base["error"] = f"OCR failed: {str(e)}"
        base["ocr_status"] = "error"
        return base
