# ProfileIQ – Profile Verification System

AI-powered full-stack web app for verifying social media profiles.

## Tech Stack
- **Frontend**: React (Vite) + TailwindCSS v4 + Framer Motion + Zustand + Recharts
- **Backend**: Python FastAPI + SQLite + JWT Auth

## Project Structure
```
C_fraud-detector/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py          # POST /auth/register, POST /auth/login
│   │   ├── analysis.py      # POST /analyze, GET /analysis/:id, GET /history
│   │   └── admin.py         # GET /admin/stats, /admin/users, /admin/analyses
│   ├── models/
│   │   ├── database.py      # SQLAlchemy models + DB init
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   └── analyzer.py      # Mock AI analysis pipeline
│   └── utils/
│       └── auth.py          # JWT + password hashing
└── frontend/
    └── src/
        ├── pages/           # Landing, Login, Register, Dashboard, Analyze, History, Admin
        ├── components/
        │   ├── layout/      # Sidebar, Topbar, AppLayout
        │   └── ui/          # StatCard, RiskBadge, TrustGauge
        ├── store/           # Zustand auth store
        └── lib/             # Axios API client
```

## Prerequisites
- **Python**: 3.11 (Required for compatibility with ML packages)
- **Node.js**: v18+ 
- **Tesseract OCR**: (Optional) Required for screenshot analysis. [Download Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- **Environment**: Set `PROFILEIQ_SECRET_KEY` for stable JWT tokens outside local development.

## Quick Start

### Backend
1. **Navigate to backend directory**:
   ```powershell
   cd backend
   ```
2. **Setup & Activate Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. **Run Server**:
   ```powershell
   uvicorn main:app --reload --port 8001
   ```

### Frontend
1. **Navigate to frontend directory**:
   ```powershell
   cd frontend
   ```
2. **Setup**:
   ```bash
   npm install --legacy-peer-deps
   npm run dev
   ```

## Standardized API Contract
All API responses follow the format:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

## Creating an Admin User
Register through the UI, then run the utility script:
```powershell
.\venv\Scripts\python.exe -m utils.make_admin --email admin@example.com
```

## API Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Create account |
| POST | /auth/login | No | Get JWT token |
| POST | /analyze | Yes | Analyze profile URL |
| GET | /analysis/:id | Yes | Get single analysis |
| GET | /history | Yes | Get user's history |
| GET | /admin/stats | Admin | Platform statistics |
| GET | /admin/users | Admin | All users |
| GET | /admin/analyses | Admin | All analyses |


