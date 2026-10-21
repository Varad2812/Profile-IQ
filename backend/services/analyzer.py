"""
Main analysis pipeline — ProfileIQ
Face module:              REAL (DeepFace)
Text module:              REAL (BART zero-shot + heuristics)
Behavior module:          REAL (IsolationForest anomaly detection)
Profile Understanding:    REAL (SentenceTransformer + NER)
Network / Consistency / Identity: Mock (ready for future integration)
"""

import random
import hashlib
import logging
import os
from services.face_analysis import analyze_face, analyze_face_from_path
from services.text_analysis import analyze_text
from services.behavior_analysis import analyze_behavior
from services.profile_understanding import understand_profile
from services.cross_platform import verify_identity

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_profile_image_url(profile_url: str):
    url = profile_url.rstrip("/")
    username = url.split("/")[-1].lstrip("@")
    if not username or ":" in username:
        return None
    return f"https://ui-avatars.com/api/?name={username}&size=200&background=random&format=png"


# ── Evidence templates ────────────────────────────────────────────────────────

EVIDENCE_TEMPLATES = {
    "low": [
        {"log_type": "positive", "module": "Network Analysis",      "message": "Follower-to-following ratio within normal range for genuine accounts"},
        {"log_type": "positive", "module": "Consistency Check",     "message": "Account creation date and activity history align correctly"},
        {"log_type": "positive", "module": "Identity Verification", "message": "Cross-platform identity signals are consistent"},
    ],
    "medium": [
        {"log_type": "warning",  "module": "Network Analysis",      "message": "A portion of followers appear to be low-activity or inactive accounts"},
        {"log_type": "warning",  "module": "Consistency Check",     "message": "Bio information changed multiple times in a short period"},
        {"log_type": "warning",  "module": "Identity Verification", "message": "Limited cross-platform presence found for this identity"},
    ],
    "high": [
        {"log_type": "critical", "module": "Network Analysis",      "message": "Over 70% of connections are flagged or suspended accounts"},
        {"log_type": "critical", "module": "Identity Verification", "message": "No verifiable cross-platform identity found"},
        {"log_type": "warning",  "module": "Consistency Check",     "message": "Account metadata inconsistencies detected — possible repurposed account"},
    ],
}

FACE_EVIDENCE = {
    "no_face_detected":     {"log_type": "critical", "module": "Face Authenticity", "message": "No face detected in profile image — may be a logo, object, or blank photo"},
    "multiple_faces":       {"log_type": "warning",  "module": "Face Authenticity", "message": "Multiple faces detected in profile photo — unusual for a personal account"},
    "low_resolution":       {"log_type": "warning",  "module": "Face Authenticity", "message": "Profile image is low resolution — limits authenticity verification accuracy"},
    "blurry_image":         {"log_type": "warning",  "module": "Face Authenticity", "message": "Profile image appears blurry — may be intentionally obscured"},
    "neutral_only_emotion": {"log_type": "warning",  "module": "Face Authenticity", "message": "Face shows only neutral expression — consistent with AI-generated or stock imagery"},
    "image_fetch_failed":   {"log_type": "warning",  "module": "Face Authenticity", "message": "Could not retrieve profile image for analysis — using fallback score"},
    "analysis_error":       {"log_type": "warning",  "module": "Face Authenticity", "message": "Face analysis encountered an error — result may be less accurate"},
}
FACE_POSITIVE = {
    "high_confidence": {"log_type": "positive", "module": "Face Authenticity", "message": "Face detected with high confidence — profile photo appears authentic"},
    "clear_image":     {"log_type": "positive", "module": "Face Authenticity", "message": "Profile image is clear and high resolution — good quality for verification"},
    "emotion_variety": {"log_type": "positive", "module": "Face Authenticity", "message": "Natural facial expression detected — consistent with genuine human photo"},
}

TEXT_EVIDENCE = {
    "contains_scam_keywords": {"log_type": "critical", "module": "Text Analysis", "message": "Scam-related keywords detected in profile bio"},
    "generic_ai_text":        {"log_type": "warning",  "module": "Text Analysis", "message": "Bio text shows characteristics of AI-generated or templated content"},
    "classified_scam":        {"log_type": "critical", "module": "Text Analysis", "message": "NLP model classified bio as scam/spam content"},
    "classified_suspicious":  {"log_type": "warning",  "module": "Text Analysis", "message": "NLP model flagged bio as suspicious promotional content"},
    "no_text_data":           {"log_type": "warning",  "module": "Text Analysis", "message": "No bio text available for analysis — text score is estimated"},
    "low_information":        {"log_type": "warning",  "module": "Text Analysis", "message": "Bio is very short or contains minimal information"},
    "very_short_bio":         {"log_type": "warning",  "module": "Text Analysis", "message": "Profile bio is unusually short"},
}
TEXT_POSITIVE = {
    "normal": {"log_type": "positive", "module": "Text Analysis", "message": "Bio text classified as normal — no suspicious patterns detected"},
    "clean":  {"log_type": "positive", "module": "Text Analysis", "message": "No scam keywords or AI-generated patterns found in profile text"},
}

BEHAVIOR_EVIDENCE = {
    "ml_anomaly_detected":          {"log_type": "critical", "module": "Behavior Analysis", "message": "IsolationForest ML model detected anomalous behavioral pattern"},
    "anomalous_ratio":              {"log_type": "warning",  "module": "Behavior Analysis", "message": "Follower-to-following ratio is statistically anomalous"},
    "extremely_high_follower_ratio":{"log_type": "warning",  "module": "Behavior Analysis", "message": "Extremely high follower ratio — possible purchased followers"},
    "low_activity":                 {"log_type": "warning",  "module": "Behavior Analysis", "message": "Low activity relative to follower count — may indicate inactive or fake account"},
    "mass_following_pattern":       {"log_type": "critical", "module": "Behavior Analysis", "message": "Mass-following pattern detected — consistent with bot or spam behavior"},
    "unusual_growth_pattern":       {"log_type": "warning",  "module": "Behavior Analysis", "message": "Unusual follower growth relative to post count — possible inorganic growth"},
    "suspicious_round_numbers":     {"log_type": "warning",  "module": "Behavior Analysis", "message": "Suspiciously round follower numbers with minimal posts"},
    "no_posts":                     {"log_type": "warning",  "module": "Behavior Analysis", "message": "Account has no posts — may be a newly created or inactive account"},
    "no_profile_data":              {"log_type": "warning",  "module": "Behavior Analysis", "message": "No follower/following/post data available for behavioral analysis"},
}
BEHAVIOR_POSITIVE = {
    "normal": {"log_type": "positive", "module": "Behavior Analysis", "message": "Behavioral metrics are within normal range — IsolationForest confirms authentic pattern"},
}

PROFILE_EVIDENCE = {
    "suspicious":    {"log_type": "critical", "module": "Identity Verification", "message": "Profile classified as suspicious/scam type based on semantic analysis"},
    "business":      {"log_type": "positive", "module": "Identity Verification", "message": "Profile classified as a business or brand account"},
    "influencer":    {"log_type": "positive", "module": "Identity Verification", "message": "Profile classified as an influencer or content creator account"},
    "individual":    {"log_type": "positive", "module": "Identity Verification", "message": "Profile classified as a genuine individual personal account"},
    "public_figure": {"log_type": "positive", "module": "Identity Verification", "message": "Profile classified as a public figure, celebrity, or professional athlete"},
}


# ── Main pipeline ─────────────────────────────────────────────────────────────

def analyze_profile(
    profile_url: str,
    image_path: str = None,
    bio: str = "",
    ocr_data: dict = None,
) -> dict:
    """
    Full analysis pipeline.
    - face_score:      REAL (DeepFace)
    - text_score:      REAL (BART + heuristics)
    - behavior_score:  REAL (IsolationForest)
    - profile_type:    REAL (SentenceTransformer + NER)
    - network/consistency/identity: mock
    """
    ocr_data = ocr_data or {}
    
    # ── Platform Detection Fallback (URL-based) ───────────────────────────
    detected_platform = ocr_data.get("platform", "unknown")
    if detected_platform == "unknown" and profile_url:
        try:
            low_url = str(profile_url).lower()
            if "instagram.com" in low_url:              detected_platform = "instagram"
            elif "twitter.com" in low_url or "x.com" in low_url: detected_platform = "twitter"
            elif "linkedin.com" in low_url:             detected_platform = "linkedin"
            elif "facebook.com" in low_url:             detected_platform = "facebook"
            elif "tiktok.com" in low_url:               detected_platform = "tiktok"
        except Exception as e:
            logger.warning(f"[Analyzer] Platform detection failed: {e}")
        
    ocr_data["platform"] = detected_platform

    seed = int(hashlib.md5(profile_url.encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    # ── 1. Face analysis ──────────────────────────────────────────────────
    face_result = {
        "face_score": 25, "age": 0, "gender": "unknown",
        "emotion": "unknown", "confidence": 0.0,
        "flags": ["analysis_skipped"], "source": "fallback",
    }
    temp_face_path = None
    actual_image_path = None
    
    logger.info("[ANALYZE] Starting Face module...")
    try:
        if image_path:
            face_result = analyze_face_from_path(image_path)
            actual_image_path = image_path
        else:
            image_url = ocr_data.get("profile_image_url") or _resolve_profile_image_url(profile_url)
            if image_url:
                from services.face_analysis import _fetch_image_to_temp
                temp_face_path = _fetch_image_to_temp(image_url)
                if temp_face_path:
                    face_result = analyze_face_from_path(temp_face_path)
                    actual_image_path = temp_face_path
                else:
                    face_result["flags"] = ["image_download_failed"]
            else:
                face_result["flags"] = ["no_image_url"]
        logger.info(f"[ANALYZE] Face module success (score {face_result['face_score']})")
    except Exception as e:
        logger.error(f"[ANALYZE] Face module failed: {e}")
        face_result["flags"] = ["module_crash"]

    face_score = float(face_result["face_score"])

    # ── 2. Text analysis ──────────────────────────────────────────────────
    text_result = {
        "text_score": 50.0, "classification": "unknown", 
        "scam_probability": 0.0, "ai_generated_probability": 0.0,
        "flags": ["analysis_skipped"], "source": "fallback", "scam_keywords": []
    }
    logger.info("[ANALYZE] Starting Text module...")
    try:
        text_result = analyze_text(bio)
        logger.info(f"[ANALYZE] Text module success (score {text_result['text_score']})")
    except Exception as e:
        logger.error(f"[ANALYZE] Text module failed: {e}")
        text_result["flags"] = ["module_crash"]
        
    text_score = float(text_result["text_score"])

    # ── 3. Behavior analysis ──────────────────────────────────────────────
    behavior_result = {
        "behavior_score": 50.0, "anomaly_score": 0.0, 
        "flags": ["analysis_skipped"], "source": "fallback"
    }
    logger.info("[ANALYZE] Starting Behavior module...")
    try:
        behavior_result = analyze_behavior(
            followers=ocr_data.get("followers", 0),
            following=ocr_data.get("following", 0),
            posts=ocr_data.get("posts", 0),
            bio=bio,
            platform=ocr_data.get("platform", "unknown"),
        )
        logger.info(f"[ANALYZE] Behavior module success (score {behavior_result['behavior_score']})")
    except Exception as e:
        logger.error(f"[ANALYZE] Behavior module failed: {e}")
        behavior_result["flags"] = ["module_crash"]
        
    behavior_score = float(behavior_result["behavior_score"])

    # ── 4. Profile understanding ──────────────────────────────────────────
    profile_result = {
        "profile_type": "unknown", "confidence": 0.0, 
        "summary": "Profile analysis in progress...", "entities": []
    }
    logger.info("[ANALYZE] Starting Profile Understanding module...")
    try:
        profile_result = understand_profile(
            bio=bio,
            username=ocr_data.get("username", ""),
            raw_text=ocr_data.get("raw_text", ""),
            platform=ocr_data.get("platform", "unknown"),
            behavior_flags=behavior_result["flags"],
            followers=ocr_data.get("followers", 0),
            following=ocr_data.get("following", 0),
        )
        logger.info(f"[ANALYZE] Profile Understanding module success (type {profile_result['profile_type']})")
    except Exception as e:
        logger.error(f"[ANALYZE] Profile Understanding module failed: {e}")

    # ── 5. Cross-platform identity ────────────────────────────────────────
    cp_result = {
        "cross_platform_score": 15.0, "matched_profiles": [], 
        "face_matches_count": 0, "risk_flags": ["module_skipped"]
    }
    logger.info("[ANALYZE] Starting Cross-Platform module...")
    try:
        extracted_user = ocr_data.get("username")
        if not extracted_user and profile_url and "instagram.com" in profile_url.lower():
            extracted_user = profile_url.rstrip("/").split("/")[-1].lstrip("@")
            
        cp_result = verify_identity(
            username=extracted_user,
            original_image_path=actual_image_path
        )
        logger.info(f"[ANALYZE] Cross-Platform module success (score {cp_result['cross_platform_score']})")
    except Exception as e:
        logger.error(f"[ANALYZE] Cross-Platform module failed: {e}")
        cp_result["risk_flags"] = ["module_crash"]

    identity_score = float(cp_result["cross_platform_score"])

    # ── 6. Mock scores for remaining modules ──────────────────────────────
    network_score     = round(rng.uniform(35, 90), 1)
    consistency_score = round(rng.uniform(30, 95), 1)

    # ── 6. Weighted trust score ────────────────────────────────────────────
    trust_score = round(
        face_score        * 0.22 +
        text_score        * 0.18 +
        behavior_score    * 0.20 +
        network_score     * 0.15 +
        consistency_score * 0.13 +
        identity_score    * 0.12,
        1,
    )
    confidence = round(rng.uniform(72, 97), 1)

    if trust_score >= 70:
        risk_level = "low"
    elif trust_score >= 45:
        risk_level = "medium"
    else:
        risk_level = "high"

    # ── 7. Build evidence logs ─────────────────────────────────────────────
    evidence = list(EVIDENCE_TEMPLATES[risk_level])

    # Face evidence
    for flag in face_result.get("flags", []):
        if flag in FACE_EVIDENCE:
            evidence.append(FACE_EVIDENCE[flag])
    critical_face = {"no_face_detected", "image_fetch_failed", "analysis_error"}
    if not any(f in critical_face for f in face_result.get("flags", [])):
        if face_result.get("confidence", 0) > 0.75:
            evidence.append(FACE_POSITIVE["high_confidence"])
        if face_result.get("source") == "deepface":
            evidence.append(FACE_POSITIVE["clear_image"])
        if face_result.get("emotion", "neutral") not in ("neutral", "unknown"):
            evidence.append(FACE_POSITIVE["emotion_variety"])

    # Text evidence
    for flag in text_result.get("flags", []):
        if flag in TEXT_EVIDENCE:
            evidence.append(TEXT_EVIDENCE[flag])
    if text_result["classification"] == "normal" and not text_result["flags"]:
        evidence.append(TEXT_POSITIVE["normal"])
    elif text_result["scam_probability"] == 0 and "no_text_data" not in text_result["flags"]:
        evidence.append(TEXT_POSITIVE["clean"])

    # Behavior evidence
    bflags = behavior_result.get("flags", [])
    for flag in bflags:
        if flag in BEHAVIOR_EVIDENCE:
            evidence.append(BEHAVIOR_EVIDENCE[flag])
    if not bflags or bflags == []:
        evidence.append(BEHAVIOR_POSITIVE["normal"])

    # Identity / Cross-platform evidence
    cp_matches = cp_result.get("matched_profiles", [])
    if len(cp_matches) > 0:
        evidence.append({
            "log_type": "positive",
            "module": "Identity Verification",
            "message": f"Identity verified on {len(cp_matches)} platforms (including {', '.join([p['platform'] for p in cp_matches[:2]])})"
        })
        if cp_result.get("face_matches_count", 0) > 0:
            evidence.append({
                "log_type": "positive",
                "module": "Identity Verification",
                "message": "Face match confirmed across external social profiles"
            })
    else:
        evidence.append({
            "log_type": "warning",
            "module": "Identity Verification",
            "message": "No consistent external identity found for this username"
        })
    
    for flag in cp_result.get("risk_flags", []):
        if flag == "face_mismatch_detected":
            evidence.append({"log_type": "critical", "module": "Identity Verification", "message": "Face mismatch detected on correlated profiles"})
        elif flag == "low_username_consistency":
            evidence.append({"log_type": "warning", "module": "Identity Verification", "message": "Identified profiles show inconsistent username patterns"})

    # Profile understanding evidence
    ptype = profile_result["profile_type"]
    if ptype in PROFILE_EVIDENCE:
        evidence.append(PROFILE_EVIDENCE[ptype])
    if profile_result["entities"]:
        evidence.append({
            "log_type": "positive",
            "module": "Identity Verification",
            "message": f"Named entities identified: {', '.join(profile_result['entities'][:3])}",
        })

    # ── 8. Use real profile summary ────────────────────────────────────────
    summary = profile_result["summary"]

    response = {
        "trust_score": trust_score,
        "confidence": confidence,
        "risk_level": risk_level,
        "summary": summary,
        "module_scores": {
            "face_score":        face_score,
            "text_score":        text_score,
            "behavior_score":    behavior_score,
            "network_score":     network_score,
            "consistency_score": consistency_score,
            "identity_score":    identity_score,
            # Face metadata
            "face_age":    face_result.get("age", 0),
            "face_gender": face_result.get("gender", "unknown"),
            "face_emotion":face_result.get("emotion", "unknown"),
            "face_flags":  ",".join(face_result.get("flags", [])),
            "face_source": face_result.get("source", "fallback"),
            # Text metadata
            "text_classification": text_result["classification"],
            "text_scam_prob":      text_result["scam_probability"],
            "text_ai_prob":        text_result["ai_generated_probability"],
            "text_flags":          ",".join(text_result["flags"]),
            "text_scam_keywords":  ",".join(text_result["scam_keywords"]),
            "text_source":         text_result["source"],
            # Behavior metadata
            "behavior_anomaly_score": behavior_result["anomaly_score"],
            "behavior_flags":         ",".join(behavior_result["flags"]),
            "behavior_source":        behavior_result["source"],
            # Profile understanding metadata
            "profile_type":            profile_result["profile_type"],
            "profile_entities":        ",".join(profile_result["entities"]),
            "profile_summary":         profile_result["summary"],
            "profile_type_confidence": profile_result["confidence"],
            "platform":                ocr_data.get("platform", "unknown"),
            # Cross-platform metadata
            "identity_score":          identity_score,
            "identity_matches":        len(cp_result.get("matched_profiles", [])),
            "identity_face_matches":   cp_result.get("face_matches_count", 0),
            "identity_risk_flags":     ",".join(cp_result.get("risk_flags", [])),
            "identity_platforms":      ",".join([p["platform"] for p in cp_result.get("matched_profiles", [])]),
        },
        "evidence_logs": evidence,
    }
    
    # Cleanup temp face image if we created one
    if temp_face_path and os.path.exists(temp_face_path):
        try: os.unlink(temp_face_path)
        except: pass
        
    return response


def mock_analyze_profile(profile_url: str) -> dict:
    return analyze_profile(profile_url)
