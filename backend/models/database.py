from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./profileiq_v2.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    analyses = relationship("Analysis", back_populates="user")


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    profile_url = Column(String, nullable=False)
    input_type = Column(String, default="url")        # "url" | "screenshot"
    profile_image_b64 = Column(Text, default="")      # base64 preview image
    trust_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    risk_level = Column(String, default="unknown")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="analyses")
    module_scores = relationship("ModuleScores", back_populates="analysis", uselist=False)
    evidence_logs = relationship("EvidenceLog", back_populates="analysis")
    # OCR extracted data (screenshot pipeline only)
    ocr_platform   = Column(String, default="unknown")
    ocr_username   = Column(String, default="")
    ocr_bio        = Column(Text,   default="")
    ocr_followers  = Column(String, default="")
    ocr_following  = Column(String, default="")
    ocr_posts      = Column(String, default="")
    ocr_confidence = Column(Float,  default=0.0)
    ocr_raw_text   = Column(Text,   default="")
    ocr_error      = Column(String, default="")


class ModuleScores(Base):
    __tablename__ = "module_scores"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    face_score = Column(Float, default=0.0)
    text_score = Column(Float, default=0.0)
    behavior_score = Column(Float, default=0.0)
    network_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    identity_score = Column(Float, default=0.0)
    # Face metadata from real AI analysis
    face_age = Column(Integer, default=0)
    face_gender = Column(String, default="unknown")
    face_emotion = Column(String, default="unknown")
    face_flags = Column(String, default="")   # comma-separated flag list
    face_source = Column(String, default="mock")  # "deepface" | "fallback" | "mock"
    # Text analysis metadata
    text_classification  = Column(String, default="unknown")  # normal|suspicious|scam
    text_scam_prob       = Column(Float,  default=0.0)
    text_ai_prob         = Column(Float,  default=0.0)
    text_flags           = Column(String, default="")   # comma-separated
    text_scam_keywords   = Column(Text,   default="")   # comma-separated matched keywords
    text_source          = Column(String, default="mock")  # nlp|heuristic|fallback
    # Behavior analysis metadata
    behavior_anomaly_score  = Column(Float,  default=0.0)
    behavior_flags          = Column(String, default="")
    behavior_source         = Column(String, default="mock")
    # Profile understanding metadata
    profile_type            = Column(String, default="unknown")
    profile_entities        = Column(Text,   default="")
    profile_summary         = Column(Text,   default="")
    profile_type_confidence = Column(Float,  default=0.0)
    # Cross-platform identity metadata
    identity_matches        = Column(Integer, default=0)
    identity_face_matches   = Column(Integer, default=0)
    identity_risk_flags     = Column(String,  default="")
    identity_platforms      = Column(String,  default="")
    analysis = relationship("Analysis", back_populates="module_scores")


class EvidenceLog(Base):
    __tablename__ = "evidence_logs"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    log_type = Column(String, default="info")   # critical | warning | positive
    module = Column(String, default="")
    message = Column(Text, default="")
    analysis = relationship("Analysis", back_populates="evidence_logs")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
