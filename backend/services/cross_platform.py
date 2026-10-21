"""
Cross-Platform Identity Verification Module — ProfileIQ
Verifies identity consistency using OSINT (Google search) and Face Comparison.

Improvements:
  - Retry + exponential backoff on Google search
  - Direct URL fallback when Google is rate-limited
  - Per-call timeout to prevent blocking the API thread
  - In-memory LRU cache to avoid repeated hits for the same username
"""

import logging
import os
import re
import time
import tempfile
import requests
from functools import lru_cache
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

PLATFORMS_CONFIG = {
    "instagram": {"domain": "instagram.com",  "label": "Instagram",   "url_pattern": "https://instagram.com/{username}"},
    "twitter":   {"domain": "twitter.com",    "label": "Twitter / X", "url_pattern": "https://twitter.com/{username}"},
    "linkedin":  {"domain": "linkedin.com",   "label": "LinkedIn",    "url_pattern": "https://linkedin.com/in/{username}"},
    "facebook":  {"domain": "facebook.com",   "label": "Facebook",    "url_pattern": "https://facebook.com/{username}"},
    "tiktok":    {"domain": "tiktok.com",     "label": "TikTok",      "url_pattern": "https://tiktok.com/@{username}"},
}

_REQUEST_TIMEOUT = 5   # seconds per HTTP request
_SEARCH_TIMEOUT  = 10  # seconds for the whole Google search block
_MAX_RETRIES     = 2   # max attempts for heavy external calls


# ── In-memory cache (username → result dict) ──────────────────────────────────

_cache: dict = {}
_CACHE_TTL = 3600  # 1 hour


def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        logger.info(f"[CrossPlatform] Cache hit for '{key}'")
        return entry["data"]
    return None


def _cache_set(key: str, data: dict):
    _cache[key] = {"data": data, "ts": time.time()}


# ── HTTP helpers ──────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
}


def _fetch_page(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning(f"[CrossPlatform] Failed to fetch {url}: {e}")
        return None


def _check_url_exists(url: str, username: str = None) -> bool:
    """
    Check if a profile URL exists on the target platform.
    Avoids false positives from ban/redirect pages (like TikTok in India) and login walls.
    """
    try:
        # Check platform-specific behaviors
        if "tiktok.com" in url:
            resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT, allow_redirects=True)
            if resp.status_code != 200:
                return False
            # Check redirect to India ban/about page
            if "/in/about" in resp.url:
                logger.info(f"[CrossPlatform] TikTok profile redirected to ban page: {resp.url}")
                return False
            if username and f"@{username.lower()}" not in resp.url.lower():
                logger.info(f"[CrossPlatform] TikTok profile redirected away from username: {resp.url}")
                return False
            if "govt. of india decided to block" in resp.text.lower():
                logger.info("[CrossPlatform] TikTok profile blocked by Indian government notice page")
                return False
            return True

        if "instagram.com" in url:
            # Direct probing to Instagram always hits a login wall or httpErrorPage,
            # returning 200 OK for both valid and invalid profiles. We must treat direct probe
            # as unverifyable (False) to avoid 100% false positives.
            logger.info("[CrossPlatform] Direct probe for Instagram is blocked by login wall; returning False")
            return False

        if "twitter.com" in url or "x.com" in url:
            # Direct probing to Twitter hits a JS-disabled login/info wall (returning 200 OK
            # for both valid and invalid usernames). We must treat direct probe as unverifyable (False).
            logger.info("[CrossPlatform] Direct probe for Twitter/X is blocked by JS/login wall; returning False")
            return False

        # Facebook (400) and LinkedIn (999) block direct requests, return False
        resp = requests.head(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT, allow_redirects=True)
        return resp.status_code == 200
    except Exception as e:
        logger.warning(f"[CrossPlatform] Direct probe failed for {url}: {e}")
        return False


# ── Google search with retry + backoff ───────────────────────────────────────

def _google_search_with_retry(query: str, num_results: int = 15) -> List[str]:
    """
    Attempt Google search up to 3 times with exponential backoff (1s, 2s, 4s).
    Returns list of URLs or empty list on failure.
    """
    from googlesearch import search as gsearch

    delays = [1, 2, 4]
    for attempt, delay in enumerate(delays, 1):
        try:
            deadline = time.time() + _SEARCH_TIMEOUT
            results = []
            for url in gsearch(query, num_results=num_results, sleep_interval=1):
                results.append(url)
                if time.time() > deadline:
                    logger.warning("[CrossPlatform] Search timeout reached, using partial results")
                    break
            logger.info(f"[CrossPlatform] Google search returned {len(results)} results (attempt {attempt})")
            return results
        except Exception as e:
            logger.warning(f"[CrossPlatform] Google search attempt {attempt} failed: {e}")
            if attempt < len(delays):
                time.sleep(delay)

    logger.error("[CrossPlatform] All Google search attempts failed")
    return []


# ── Direct URL fallback ───────────────────────────────────────────────────────

def _direct_url_fallback(username: str) -> List[dict]:
    """
    When Google search fails, probe platform URLs directly.
    Returns list of result dicts (same shape as Google-derived results).
    """
    results = []
    for p_id, cfg in PLATFORMS_CONFIG.items():
        url = cfg["url_pattern"].format(username=username)
        if _check_url_exists(url, username=username):
            logger.info(f"[CrossPlatform] Direct URL confirmed: {url}")
            results.append({
                "platform": p_id,
                "url": url,
                "username_similarity": 1.0,
                "found_username": username,
                "face_match": False,
                "confidence": 0.5,
                "source": "direct_url",
            })
    return results


# ── Profile meta extraction ───────────────────────────────────────────────────

def _extract_profile_meta(html: str) -> Dict:
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    meta = {"image_url": None, "bio": ""}
    try:
        og_image = soup.find("meta", property="og:image")
        if og_image:
            meta["image_url"] = og_image.get("content")
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            meta["bio"] = og_desc.get("content", "")
    except Exception as e:
        logger.warning(f"[CrossPlatform] Meta extraction failed: {e}")
    return meta


# ── Main pipeline ─────────────────────────────────────────────────────────────

def verify_identity(username: str, original_image_path: str = None) -> Dict:
    if not username:
        return {
            "cross_platform_score": 0,
            "matched_profiles": [],
            "face_matches_count": 0,
            "risk_flags": ["no_username_provided"],
        }

    # Check cache first
    cache_key = f"{username}:{bool(original_image_path)}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    results = []
    google_failed = False

    # ── 1. Google search with retry ───────────────────────────────────────
    try:
        query = (
            f'"{username}" '
            f'(site:instagram.com OR site:twitter.com OR site:linkedin.com '
            f'OR site:facebook.com OR site:tiktok.com)'
        )
        urls = _google_search_with_retry(query)

        for url in urls:
            platform = "unknown"
            for p_id, cfg in PLATFORMS_CONFIG.items():
                if cfg["domain"] in url:
                    platform = p_id
                    break
            if platform == "unknown":
                continue

            res = {
                "platform": platform,
                "url": url,
                "username_similarity": 0.0,
                "face_match": False,
                "confidence": 0.0,
                "source": "google",
            }
            found_match = re.search(r"/([^/?#]+)", url.split(PLATFORMS_CONFIG[platform]["domain"])[-1])
            if found_match:
                found_user = found_match.group(1).lstrip("@").rstrip("/")
                sim = fuzz.ratio(username.lower(), found_user.lower()) / 100.0
                res["username_similarity"] = round(sim, 2)
                res["found_username"] = found_user
            results.append(res)

    except Exception as e:
        logger.error(f"[CrossPlatform] Search block failed: {e}")
        google_failed = True

    # ── 2. Direct URL fallback if Google failed or returned nothing ───────
    if google_failed or not results:
        logger.info(f"[CrossPlatform] Using direct URL fallback for '{username}'")
        results = _direct_url_fallback(username)

    # ── 3. Deduplicate (one per platform, highest similarity) ─────────────
    unique: dict = {}
    for r in results:
        p = r["platform"]
        if p not in unique or r["username_similarity"] > unique[p]["username_similarity"]:
            unique[p] = r
    final_matches = list(unique.values())

    # ── 4. Face comparison (top 2 candidates only) ────────────────────────
    face_matches_count = 0
    if original_image_path and os.path.exists(original_image_path):
        try:
            from deepface import DeepFace
            from services.face_analysis import _fetch_image_to_temp

            top_candidates = sorted(
                final_matches, key=lambda x: x["username_similarity"], reverse=True
            )[:2]

            for match in top_candidates:
                html = _fetch_page(match["url"])
                meta = _extract_profile_meta(html)
                if not meta.get("image_url"):
                    continue

                match_img = _fetch_image_to_temp(meta["image_url"])
                if not match_img:
                    continue
                try:
                    v = DeepFace.verify(
                        img1_path=original_image_path,
                        img2_path=match_img,
                        detector_backend="ssd",
                        enforce_detection=False,
                        silent=True,
                    )
                    if v.get("verified"):
                        match["face_match"] = True
                        face_matches_count += 1
                except Exception as e:
                    logger.warning(f"[CrossPlatform] DeepFace verify error: {e}")
                finally:
                    if os.path.exists(match_img):
                        os.unlink(match_img)
        except Exception as e:
            logger.error(f"[CrossPlatform] Face verification block failed: {e}")

    # ── 5. Scoring ────────────────────────────────────────────────────────
    score = 0
    risk_flags = []

    if not final_matches:
        score = 15
        risk_flags.append("no_cross_platform_presence")
    else:
        score += min(len(final_matches) * 20, 60)
        avg_sim = sum(m["username_similarity"] for m in final_matches) / len(final_matches)
        if avg_sim < 0.6:
            risk_flags.append("low_username_consistency")
            score -= 10
        if face_matches_count > 0:
            score += 30
        elif original_image_path:
            risk_flags.append("no_identity_validation")
            score -= 5

    result = {
        "cross_platform_score": max(5, min(100, score)),
        "matched_profiles": final_matches,
        "face_matches_count": face_matches_count,
        "risk_flags": risk_flags,
    }

    _cache_set(cache_key, result)
    return result
