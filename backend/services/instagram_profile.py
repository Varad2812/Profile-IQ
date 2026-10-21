"""
Limited Instagram profile extraction for user-submitted URLs.

This module reuses a manually-created Playwright storage state. It is designed
for one profile at a time, with a small cache and conservative delays so URL
analysis can use real public profile signals without becoming bulk scraping.
"""

import json
import logging
import random
import re
import asyncio
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception as exc:
        logger.warning("[Instagram] Could not set Windows event loop policy: %s", exc)

BASE_DIR = Path(__file__).resolve().parents[1]
AUTH_DIR = BASE_DIR / ".instagram_auth"
STATE_PATH = AUTH_DIR / "state.json"
CACHE_PATH = AUTH_DIR / "profile_cache.json"
CACHE_TTL = timedelta(hours=6)
MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 5.0

_USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
_COUNT_RE = re.compile(
    r"(?P<followers>[\d,.]+[KMB]?)\s+Followers,\s+"
    r"(?P<following>[\d,.]+[KMB]?)\s+Following,\s+"
    r"(?P<posts>[\d,.]+[KMB]?)\s+Posts",
    re.IGNORECASE,
)
_VISIBLE_COUNT_RE = re.compile(
    r"(?P<posts>[\d,.]+[KMB]?)\s+posts?\s+"
    r"(?P<followers>[\d,.]+[KMB]?)\s+followers?\s+"
    r"(?P<following>[\d,.]+[KMB]?)\s+following",
    re.IGNORECASE,
)
_BLOCKED_PATHS = {
    "accounts",
    "about",
    "api",
    "developer",
    "direct",
    "explore",
    "legal",
    "p",
    "reel",
    "reels",
    "stories",
}


class InstagramProfileError(RuntimeError):
    """Raised when Instagram profile extraction cannot run or complete."""


def is_instagram_profile_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host not in {"instagram.com", "m.instagram.com"}:
        return False

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) != 1:
        return False
    username = parts[0]
    return username.lower() not in _BLOCKED_PATHS and bool(_USERNAME_RE.match(username))


def extract_username(url: str) -> str:
    parsed = urlparse(url.strip())
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        raise InstagramProfileError("Instagram profile URL is missing a username.")
    username = parts[0].strip("@")
    if not _USERNAME_RE.match(username) or username.lower() in _BLOCKED_PATHS:
        raise InstagramProfileError("Only direct Instagram profile URLs are supported.")
    return username


def has_saved_session() -> bool:
    return STATE_PATH.exists()


def get_session_status() -> Dict[str, Any]:
    return {
        "session_available": has_saved_session(),
        "state_path": str(STATE_PATH),
        "cache_path": str(CACHE_PATH),
    }


def _load_cache() -> Dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[Instagram] Could not read cache: %s", exc)
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cached(username: str) -> Dict[str, Any] | None:
    cache = _load_cache()
    item = cache.get(username.lower())
    if not item:
        return None
    try:
        fetched_at = datetime.fromisoformat(item["fetched_at"])
    except Exception:
        return None
    if datetime.utcnow() - fetched_at > CACHE_TTL:
        return None
    profile = item.get("profile") or {}
    profile["from_cache"] = True
    return profile


def _put_cache(username: str, profile: Dict[str, Any]) -> None:
    cache = _load_cache()
    cache[username.lower()] = {
        "fetched_at": datetime.utcnow().isoformat(),
        "profile": profile,
    }
    _save_cache(cache)


def _parse_count(value: str) -> int:
    if value is None:
        return 0
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    multiplier = 1
    suffix = text[-1].upper()
    if suffix in {"K", "M", "B"}:
        text = text[:-1]
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suffix]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return 0


def _text_or_empty(page, selector: str) -> str:
    try:
        value = page.locator(selector).first.inner_text(timeout=1500)
        return (value or "").strip()
    except Exception:
        return ""


def _attr_or_empty(page, selector: str, attr: str) -> str:
    try:
        value = page.locator(selector).first.get_attribute(attr, timeout=1500)
        return (value or "").strip()
    except Exception:
        return ""


def _extract_from_meta(description: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    match = _COUNT_RE.search(description or "")
    if match:
        data["followers"] = _parse_count(match.group("followers"))
        data["following"] = _parse_count(match.group("following"))
        data["posts"] = _parse_count(match.group("posts"))

    if " - " in description:
        maybe_bio = description.split(" - ", 1)[1].strip()
        if maybe_bio.lower().startswith("see instagram photos"):
            maybe_bio = ""
        data["bio"] = maybe_bio[:500]
    return data


def _extract_from_header(header_text: str, username: str) -> Dict[str, Any]:
    lines = [line.strip() for line in (header_text or "").splitlines() if line.strip()]
    data: Dict[str, Any] = {}

    joined = " ".join(lines)
    match = _VISIBLE_COUNT_RE.search(joined)
    if match:
        data["posts"] = _parse_count(match.group("posts"))
        data["followers"] = _parse_count(match.group("followers"))
        data["following"] = _parse_count(match.group("following"))

    bio_lines = []
    skip_next_name = False
    for line in lines:
        low = line.lower()
        if low == username.lower():
            skip_next_name = True
            continue
        if skip_next_name:
            data["display_name"] = line
            skip_next_name = False
            continue
        if any(token in low for token in (" posts", " followers", " following")):
            continue
        if low in {"follow", "following", "message", "contact"}:
            continue
        if low.startswith("http") or "." in low and " " not in low:
            continue
        bio_lines.append(line)

    if bio_lines:
        data["bio"] = " ".join(bio_lines).strip()[:500]
    return data


def fetch_instagram_profile(url: str, use_cache: bool = True) -> Dict[str, Any]:
    username = extract_username(url)
    if use_cache:
        cached = _cached(username)
        if cached:
            return cached

    if not STATE_PATH.exists():
        raise InstagramProfileError(
            "Instagram session is not configured. Run the login helper once to save a browser session."
        )

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise InstagramProfileError(
            "Playwright is not installed. Install backend requirements and run `python -m playwright install chromium`."
        ) from exc

    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    time.sleep(delay)

    profile_url = f"https://www.instagram.com/{username}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STATE_PATH), viewport={"width": 1280, "height": 900})
        page = context.new_page()
        try:
            page.goto(profile_url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(2500)

            if "accounts/login" in page.url:
                raise InstagramProfileError(
                    "Saved Instagram session has expired. Run the login helper again."
                )

            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except PlaywrightTimeoutError:
                logger.info("[Instagram] Network idle timed out; continuing with loaded DOM.")

            description = _attr_or_empty(page, "meta[name='description']", "content")
            og_description = _attr_or_empty(page, "meta[property='og:description']", "content")
            title = _text_or_empty(page, "title")
            profile_image_url = _attr_or_empty(page, "meta[property='og:image']", "content")

            meta_data = _extract_from_meta(description or og_description)
            header_text = _text_or_empty(page, "header")
            visible_data = _extract_from_header(header_text, username)
            data = {**meta_data, **visible_data}
            display_name = data.get("display_name", "")
            if "(@" in title:
                display_name = display_name or title.split("(@", 1)[0].strip()

            profile = {
                "platform": "instagram",
                "username": username,
                "display_name": display_name,
                "bio": data.get("bio", ""),
                "followers": data.get("followers", 0),
                "following": data.get("following", 0),
                "posts": data.get("posts", 0),
                "profile_image_url": profile_image_url,
                "raw_text": "\n".join(filter(None, [header_text, title, description, og_description])),
                "confidence": 0.9 if data else 0.55,
                "ocr_available": True,
                "source": "playwright_instagram",
                "from_cache": False,
            }
            _put_cache(username, profile)
            return profile
        finally:
            context.close()
            browser.close()
