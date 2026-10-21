# ProfileIQ — Complete Setup Guide

> AI-powered social media profile verification system.  
> Send this guide along with the project zip to your teammate.

---

## 📋 Prerequisites

Install these **before** starting:

| Tool | Version | Download Link |
|------|---------|---------------|
| **Python** | 3.11 (required) | https://www.python.org/downloads/release/python-3110/ |
| **Node.js** | v18 or later | https://nodejs.org/ |
| **Git** | Latest | https://git-scm.com/downloads |
| **Tesseract OCR** | Latest (optional) | https://github.com/UB-Mannheim/tesseract/wiki |

> [!IMPORTANT]
> Python **3.11** is required. Other versions (3.12, 3.13, 3.14) may cause compatibility issues with TensorFlow and DeepFace.
> When installing Python, make sure to check **"Add Python to PATH"**.

> [!NOTE]
> Tesseract OCR is optional — it's only needed for the **Screenshot Analysis** feature. URL-based analysis works without it.

---

## 🚀 Quick Start (Step by Step)

### Step 1: Extract the Zip

Extract the zip file to any folder, e.g. `C:\Users\YourName\Projects\ProfileIQ`.

### Step 2: Set Up the Backend

Open **PowerShell** or **Terminal** and run:

```powershell
# Navigate to the project root
cd C:\Users\YourName\Projects\ProfileIQ

# Create a Python virtual environment
py -3.11 -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1
```

> [!TIP]
> If you get an "execution policy" error on Windows, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Now install dependencies:

```powershell
# Install all Python packages (this takes a few minutes)
pip install -r backend\requirements.txt

# Install Playwright browser (needed for Instagram profile extraction)
python -m playwright install chromium
```

### Step 3: Set Up the Frontend

Open a **second terminal**:

```powershell
cd C:\Users\YourName\Projects\ProfileIQ\frontend

# Install Node.js packages
npm install --legacy-peer-deps
```

### Step 4: Start the Servers

**Terminal 1 — Backend** (keep running):
```powershell
cd C:\Users\YourName\Projects\ProfileIQ\backend
..\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
```

**Terminal 2 — Frontend** (keep running):
```powershell
cd C:\Users\YourName\Projects\ProfileIQ\frontend
npm run dev
```

### Step 5: Open the App

Open your browser and go to: **http://localhost:5173**

1. Click **Register** to create an account
2. Log in with your new account
3. Go to **Analyze** to start verifying profiles

---

## 📸 Instagram Session Setup (For Full URL Analysis)

URL-based Instagram analysis requires a one-time browser login to save a session cookie. **Without this, Instagram URL analysis will still work but with limited data** (cross-platform checks, avatar-based face analysis only).

### How to Set Up Instagram Session

1. Make sure the virtual environment is active:
   ```powershell
   cd C:\Users\YourName\Projects\ProfileIQ
   .\.venv\Scripts\Activate.ps1
   ```

2. Run the login helper script:
   ```powershell
   python backend\utils\instagram_login.py
   ```

3. A **Chromium browser window** will open automatically showing the Instagram login page.

4. **Log in to Instagram manually** with any account (your personal account works fine).

5. Wait for the feed/home page to load, then **switch back to the terminal** and press **Enter**.

6. The script saves the session to `backend/.instagram_auth/state.json`.

7. Done! You can now analyze Instagram profiles with full data extraction.

> [!WARNING]
> - The session expires after some time. If you get "session expired" errors, just run the login script again.
> - **DO NOT share** the `state.json` file — it contains your Instagram session cookies.
> - Use a secondary/test Instagram account if you prefer not to use your personal one.

### What Happens Without Instagram Session?

| Feature | With Session | Without Session |
|---------|-------------|-----------------|
| Profile bio & metadata | ✅ Full extraction | ❌ Not available |
| Follower/following/post counts | ✅ Real data | ❌ Not available |
| Profile photo analysis | ✅ Real photo | ⚠️ Avatar placeholder |
| Cross-platform identity checks | ✅ Works | ✅ Works |
| Face analysis | ✅ Real photo | ⚠️ Generic avatar |
| Text/behavior analysis | ✅ Full | ⚠️ Limited (no bio data) |

---

## 🗂️ Project Structure

```
ProfileIQ/
├── backend/                    # Python FastAPI server (port 8001)
│   ├── main.py                 # App entry point
│   ├── requirements.txt        # Python dependencies
│   ├── routes/
│   │   ├── auth.py             # Login & registration
│   │   ├── analysis.py         # Profile analysis endpoints
│   │   └── admin.py            # Admin dashboard
│   ├── models/
│   │   ├── database.py         # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic validation schemas
│   ├── services/
│   │   ├── analyzer.py         # Main analysis pipeline
│   │   ├── face_analysis.py    # DeepFace face verification
│   │   ├── text_analysis.py    # NLP text classification (BART)
│   │   ├── behavior_analysis.py # IsolationForest anomaly detection
│   │   ├── profile_understanding.py # Profile type classifier (SentenceTransformer + NER)
│   │   ├── cross_platform.py   # Cross-platform identity verification
│   │   ├── instagram_profile.py # Instagram data extraction (Playwright)
│   │   ├── ocr_service.py      # Screenshot OCR (Tesseract)
│   │   └── image_processor.py  # Image preprocessing
│   └── utils/
│       ├── auth.py             # JWT token & password helpers
│       ├── instagram_login.py  # One-time Instagram login script
│       ├── make_admin.py       # Promote user to admin
│       └── limiter.py          # Rate limiting
├── frontend/                   # React + Vite app (port 5173)
│   ├── src/
│   │   ├── pages/              # Landing, Login, Register, Dashboard, Analyze, History, Admin
│   │   ├── components/         # UI components (TrustGauge, RiskBadge, ModuleCard, etc.)
│   │   ├── store/              # Zustand auth state
│   │   └── lib/                # Axios API client
│   ├── package.json
│   └── vite.config.js          # Dev server proxy config
├── start_backend.bat           # One-click backend start
├── start_frontend.bat          # One-click frontend start
├── SETUP_GUIDE.md              # This file
└── README.md                   # Project overview
```

---

## 🔧 Common Commands Reference

### Start/Stop Servers

```powershell
# Start backend (from project root)
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn main:app --reload --port 8001

# Start frontend (from project root)
cd frontend
npm run dev

# Or use the batch scripts (double-click in File Explorer):
start_backend.bat
start_frontend.bat
```

### Create Admin User

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
python -m utils.make_admin --email your@email.com
```

### Instagram Session Setup

```powershell
.\.venv\Scripts\Activate.ps1
python backend\utils\instagram_login.py
```

### Reset Database

```powershell
# Delete the database file to start fresh
del backend\profileiq_v2.db
# Restart the backend — it auto-creates a new database
```

---

## 🛠️ Troubleshooting

### "Module not found" errors when starting backend
Make sure the virtual environment is activated:
```powershell
.\.venv\Scripts\Activate.ps1
```

### TensorFlow/DeepFace errors
These require Python 3.11 specifically. Check your version:
```powershell
python --version
```

### "Execution policy" error on Windows
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Frontend can't connect to backend
- Make sure the backend is running on port **8001**
- Check that `frontend/vite.config.js` has the proxy set to `http://localhost:8001`

### "Rate limit exceeded" error
The API limits to 5 analysis requests per minute. Wait 60 seconds and try again.

### Instagram session expired
Re-run the login script:
```powershell
python backend\utils\instagram_login.py
```

### Playwright not installed
```powershell
pip install playwright
python -m playwright install chromium
```

### Tesseract OCR not found (screenshot analysis)
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki  
Make sure it's added to your system PATH.

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Get JWT token |
| POST | `/analyze` | Yes | Analyze profile via URL |
| POST | `/analyze/screenshot` | Yes | Analyze profile via screenshot |
| GET | `/analysis/:id` | Yes | Get single analysis result |
| GET | `/history` | Yes | Get user's analysis history |
| GET | `/instagram/session-status` | Yes | Check Instagram session |
| GET | `/admin/stats` | Admin | Platform statistics |
| GET | `/admin/users` | Admin | All users list |
| GET | `/admin/analyses` | Admin | All analyses list |

---

## ⚠️ Files to EXCLUDE from the Zip

Before zipping, delete these folders/files to reduce size:

```
.venv/                      # ~3-5 GB (teammate will recreate)
backend/venv/               # Old venv (if exists)
frontend/node_modules/      # ~200 MB (teammate will npm install)
frontend/dist/              # Build output
backend/__pycache__/        # Python cache
backend/**/__pycache__/     # Nested Python caches
backend/.instagram_auth/    # YOUR session cookies (private!)
backend/*.db                # Database files
backend/*.log               # Log files
.git/                       # Git history (optional)
```

You can run this PowerShell command to create a clean zip:

```powershell
# From the project root folder
$exclude = @('.venv', 'venv', 'node_modules', 'dist', '__pycache__', '.instagram_auth', '.git')
Get-ChildItem -Recurse | Where-Object {
    $path = $_.FullName
    -not ($exclude | Where-Object { $path -like "*\$_*" })
} | Compress-Archive -DestinationPath "..\ProfileIQ.zip" -Force
```

Or just manually delete those folders before zipping.
