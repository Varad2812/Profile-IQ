from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")

class GenericResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ModuleScoresOut(BaseModel):
    face_score: float
    text_score: float
    behavior_score: float
    network_score: float
    consistency_score: float
    identity_score: float
    # Face metadata
    face_age: Optional[int] = 0
    face_gender: Optional[str] = "unknown"
    face_emotion: Optional[str] = "unknown"
    face_flags: Optional[str] = ""
    face_source: Optional[str] = "mock"
    # Text analysis metadata
    text_classification: Optional[str] = "unknown"
    text_scam_prob:      Optional[float] = 0.0
    text_ai_prob:        Optional[float] = 0.0
    text_flags:          Optional[str] = ""
    text_scam_keywords:  Optional[str] = ""
    text_source:         Optional[str] = "mock"
    # Behavior analysis metadata
    behavior_anomaly_score:  Optional[float] = 0.0
    behavior_flags:          Optional[str] = ""
    behavior_source:         Optional[str] = "mock"
    # Profile understanding metadata
    profile_type:            Optional[str] = "unknown"
    profile_entities:        Optional[str] = ""
    profile_summary:         Optional[str] = ""
    profile_type_confidence: Optional[float] = 0.0
    platform:                Optional[str] = "unknown"
    # Cross-platform identity metadata
    identity_matches:        Optional[int] = 0
    identity_face_matches:   Optional[int] = 0
    identity_risk_flags:     Optional[str] = ""
    identity_platforms:      Optional[str] = ""

    class Config:
        orm_mode = True


class EvidenceLogOut(BaseModel):
    id: int
    log_type: str
    module: str
    message: str

    class Config:
        orm_mode = True


class AnalysisCreate(BaseModel):
    profile_url: str


class OcrDataOut(BaseModel):
    platform:      Optional[str]   = "unknown"
    username:      Optional[str]   = ""
    bio:           Optional[str]   = ""
    followers:     Optional[str]   = ""
    following:     Optional[str]   = ""
    posts:         Optional[str]   = ""
    confidence:    Optional[float] = 0.0
    raw_text:      Optional[str]   = ""
    ocr_available: Optional[bool]  = False
    ocr_status:    Optional[str]   = "ready"   # ready | unavailable | error
    error:         Optional[str]   = None


class AnalysisOut(BaseModel):
    id: int
    profile_url: str
    input_type: Optional[str] = "url"
    profile_image_b64: Optional[str] = ""
    trust_score: float
    confidence: float
    risk_level: str
    summary: str
    created_at: datetime
    module_scores: Optional[ModuleScoresOut] = None
    evidence_logs: Optional[List[EvidenceLogOut]] = []
    ocr_data: Optional[OcrDataOut] = None

    class Config:
        orm_mode = True


class AdminStats(BaseModel):
    total_users: int
    total_analyses: int
    avg_trust_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
