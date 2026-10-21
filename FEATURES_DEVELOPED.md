# ProfileIQ - Recently Developed Features & Enhancements

This document details the features, enhancements, and bug fixes that have been recently implemented in **ProfileIQ** (the C_fraud-detector platform). 

---

## 1. Instagram Profile URL Scraping & Session Automation
Instead of relying solely on manually uploaded screenshots, users can now enter a **Profile URL** (or username) directly into the UI to retrieve and analyze profile metrics dynamically.

### How It Works
* **Playwright Automation**: In the backend, a headless Chromium browser instance controlled by Playwright is spawned. It visits the Instagram profile page directly, extracting metadata, raw DOM text, post counts, follower counts, following counts, and profile images.
* **Persistent Authentication State**: Instagram restricts scraping behind a login wall. To circumvent this safely without hardcoding credentials, we added a helper script to capture and reuse session details.
* **Pre-normalization**: The frontend auto-detects and prepends `https://` if missing (e.g. `instagram.com/username` becomes `https://instagram.com/username`), making inputs resilient.

### How to Run & Configure Session Cookies
To prevent hitting login walls:
1. Run the login helper script from the repository root:
   ```bash
   .\.venv\Scripts\python.exe backend\utils\instagram_login.py
   ```
2. A visible browser window will open. Log into Instagram manually.
3. Once logged in and redirected to the home feed or profile, return to the terminal and press **Enter**.
4. The script saves your session cookies securely to `backend/.instagram_auth/state.json`.
5. Playwright will automatically load this state for all subsequent analysis requests.

---

## 2. Context-Aware AI Profile Classification
We resolved classification errors where normal profiles were erroneously flagged with high-profile labels, and conversely, where public figures were falling back to unrecognized categories.

### Highlights
* **"Public Figure" Classification**: Added support for identifying verified creators, celebrities, and professional athletes based on semantic analysis of their bios, follower-to-following ratios, and public recognition.
* **Follower-Count Sanity Checks (Guards)**:
  * Overrides the neural model's embedding classification if common sense contradicts it.
  * An account must have **at least 100,000 followers** to be classified as a **Public Figure**.
  * An account must have **at least 10,000 followers** to be classified as an **Influencer**.
  * If a low-follower account matches these templates, it is safely demoted to **Individual** or **Business** appropriately.
* **NER Token Cleaning**: Improved Entity Extraction by fixing WordPiece token issues. Previously, names were extracted as fragmented subwords (e.g. `##oh`, `##fit Sharma`). The cleaner now strips tokenization artifacts to deliver polished entities (e.g., `Rohit Sharma`).

---

## 3. Smart Behavioral Analysis Scaling
Previously, the anomaly detection engine flagged celebrities (e.g., accounts with millions of followers) as suspicious anomalies because the training set lacked representation for mega-tier accounts.

### Tweaks & Tuning
* **IsolationForest Celebrity Training Data**: Upgraded synthetic training datasets to include profiles with 5,000,000 to 100,000,000 followers. This ensures the ML model learns that extremely large follower counts are completely normal for public figures.
* **Context-Aware Ratio Flagging**: The system previously flagged anyone with a high follower-to-following ratio as `extremely_high_follower_ratio`. This rule now automatically skips accounts with **1M+ followers**, preventing false positive alerts on authentic public figures.

---

## 4. UI & UX Enhancements
We polished the interface to accommodate the new URL workflow and clarify risk levels.

* **Rebranded Trust Levels**: Re-designed the Trust Gauge label threshold mapping to make the assessment clearer:
  * **Score 70% - 100%**: Now displays **Low Risk** (previously "Authentic").
  * **Score 45% - 69%**: Now displays **Medium Risk** (previously "Suspicious").
  * **Score 0% - 44%**: Now displays **High Risk** (previously "Fake").
* **Unified Source Attribution**: Added dynamic badges to distinguish data sources. The profile detail page now tags inputs with either `OCR` (from screenshots) or `Browser` (from URL scrapes).
* **Extended UI Styles**: Integrated the `public_figure` status theme with a custom badge (icon: 🌟, pink glow layout) in `ProfileIntelligenceSection.jsx`.
* **Improved Error Resiliency**: Error handlers now capture and display detailed server responses or toast notifications to the user rather than failing silently or with generic warnings.
