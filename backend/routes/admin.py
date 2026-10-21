from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from models.database import get_db, User, Analysis
from models.schemas import AdminStats, GenericResponse
from utils.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=GenericResponse[AdminStats])
def get_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar()
    total_analyses = db.query(func.count(Analysis.id)).scalar()
    avg_trust = db.query(func.avg(Analysis.trust_score)).scalar() or 0.0
    high_risk = db.query(func.count(Analysis.id)).filter(Analysis.risk_level == "high").scalar()
    medium_risk = db.query(func.count(Analysis.id)).filter(Analysis.risk_level == "medium").scalar()
    low_risk = db.query(func.count(Analysis.id)).filter(Analysis.risk_level == "low").scalar()

    stats = AdminStats(
        total_users=total_users,
        total_analyses=total_analyses,
        avg_trust_score=round(avg_trust, 1),
        high_risk_count=high_risk,
        medium_risk_count=medium_risk,
        low_risk_count=low_risk,
    )
    return {"success": True, "data": stats}


@router.get("/users", response_model=GenericResponse[List[dict]])
def get_all_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).all()
    data = [{"id": u.id, "email": u.email, "role": u.role} for u in users]
    return {"success": True, "data": data}


@router.get("/analyses", response_model=GenericResponse[List[dict]])
def get_all_analyses(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(50).all()
    data = [
        {
            "id": a.id,
            "user_id": a.user_id,
            "profile_url": a.profile_url,
            "trust_score": a.trust_score,
            "risk_level": a.risk_level,
            "created_at": a.created_at,
        }
        for a in analyses
    ]
    return {"success": True, "data": data}
