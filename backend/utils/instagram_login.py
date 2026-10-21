"""
One-time Instagram login helper.

Run from the repo root:
    .\\.venv\\Scripts\\python.exe backend\\utils\\instagram_login.py

A visible Chromium window opens. Log into Instagram manually. In an interactive
terminal you can press Enter after login; in non-interactive runners this script
waits until a logged-in Instagram session cookie is present and saves it.
"""

from pathlib import Path
import sys
import time

from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parents[1]
AUTH_DIR = BASE_DIR / ".instagram_auth"
STATE_PATH = AUTH_DIR / "state.json"
LOGIN_WAIT_SECONDS = 300


def _has_instagram_session(context) -> bool:
    cookies = context.cookies("https://www.instagram.com")
    return any(cookie.get("name") == "sessionid" and cookie.get("value") for cookie in cookies)


def _wait_for_login(context, page) -> None:
    deadline = time.time() + LOGIN_WAIT_SECONDS
    while time.time() < deadline:
        if _has_instagram_session(context):
            return
        page.wait_for_timeout(1000)
    raise TimeoutError("Timed out waiting for Instagram login.")


def main() -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")

        print("Log into Instagram in the opened browser window.")
        if sys.stdin.isatty():
            print("After the feed or profile page loads, return here and press Enter.")
            try:
                input()
            except EOFError:
                print(f"Input is unavailable; waiting up to {LOGIN_WAIT_SECONDS // 60} minutes for login to complete...")
                _wait_for_login(context, page)
            if not _has_instagram_session(context):
                raise RuntimeError("Instagram session cookie was not found. Please confirm login completed.")
        else:
            print(f"Waiting up to {LOGIN_WAIT_SECONDS // 60} minutes for login to complete...")
            _wait_for_login(context, page)

        context.storage_state(path=str(STATE_PATH))
        print(f"Saved Instagram session to: {STATE_PATH}")
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
