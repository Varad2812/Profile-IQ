"""
Image Processor — ProfileIQ
Handles uploaded screenshot images:
- Loads image from bytes
- Detects and crops the largest face region
- Returns cropped face as temp file path for face_analysis module
"""

import logging
import tempfile
import os
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Haar cascade path bundled with OpenCV
_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def _bytes_to_cv2(image_bytes: bytes):
    """Convert raw bytes to OpenCV image array."""
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _detect_and_crop_face(img) -> tuple:
    """
    Detect faces using Haar cascade.
    Returns (cropped_face_img, face_count, confidence_proxy).
    confidence_proxy = face_area / total_image_area (larger = more prominent face).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(_CASCADE_PATH)

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    if len(faces) == 0:
        return None, 0, 0.0

    # Pick largest face by area
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]

    # Add 15% padding around face
    pad_x = int(w * 0.15)
    pad_y = int(h * 0.15)
    ih, iw = img.shape[:2]
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(iw, x + w + pad_x)
    y2 = min(ih, y + h + pad_y)

    cropped = img[y1:y2, x1:x2]
    face_area = w * h
    img_area = iw * ih
    confidence_proxy = round(face_area / img_area, 3) if img_area > 0 else 0.0

    return cropped, len(faces), confidence_proxy


def process_screenshot(image_bytes: bytes) -> dict:
    """
    Main entry point for screenshot pipeline.

    Args:
        image_bytes: raw bytes of uploaded image file

    Returns:
        {
            "temp_path": str | None,   # path to cropped face temp file
            "face_count": int,
            "confidence_proxy": float,
            "flags": list[str],
            "success": bool,
        }
    """
    flags = []
    tmp_path = None

    try:
        img = _bytes_to_cv2(image_bytes)
        if img is None:
            logger.warning("[ImageProcessor] Could not decode image bytes")
            return {"temp_path": None, "face_count": 0, "confidence_proxy": 0.0,
                    "flags": ["invalid_image_format"], "success": False}

        h, w = img.shape[:2]
        if h < 50 or w < 50:
            flags.append("image_too_small")
            return {"temp_path": None, "face_count": 0, "confidence_proxy": 0.0,
                    "flags": flags, "success": False}

        cropped, face_count, conf_proxy = _detect_and_crop_face(img)

        if face_count == 0 or cropped is None:
            flags.append("no_face_detected")
            # Fall back to full image for DeepFace to try
            cropped = img

        if face_count > 1:
            flags.append("multiple_faces")

        # Check cropped face resolution
        ch, cw = cropped.shape[:2]
        if ch < 60 or cw < 60:
            flags.append("low_resolution")

        # Save cropped face to temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(tmp.name, cropped)
        tmp.close()
        tmp_path = tmp.name

        return {
            "temp_path": tmp_path,
            "face_count": face_count,
            "confidence_proxy": conf_proxy,
            "flags": flags,
            "success": True,
        }

    except Exception as e:
        logger.error(f"[ImageProcessor] Error: {e}")
        return {"temp_path": None, "face_count": 0, "confidence_proxy": 0.0,
                "flags": ["processing_error"], "success": False}
