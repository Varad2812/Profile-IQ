"""
Text Analysis Module — ProfileIQ
NLP-based analysis using HuggingFace transformers + rule-based heuristics.
Detects scam patterns, AI-generated text, and semantic anomalies in profile bios.

Architecture:
  - Layer 1: Rule-based scam keyword detection
  - Layer 2: Heuristic AI-text detection (no model needed)
  - Layer 3: DistilBERT zero-shot classification (normal/suspicious/promotional)
  - Layer 4: Weighted score computation
"""

import re
import logging
import unicodedata
from typing import Optional

logger = logging.getLogger(__name__)

# ── Model loading (lazy, singleton) ──────────────────────────────────────────

_classifier = None
_MODEL_LOADED = False
_MODEL_ERROR = None


def _load_model():
    global _classifier, _MODEL_LOADED, _MODEL_ERROR
    if _MODEL_LOADED:
        return
    try:
        from transformers import pipeline
        # facebook/bart-base-mnli is faster and uses less memory
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-base-mnli",
            device=-1,   # CPU
        )
        _MODEL_LOADED = True
        logger.info("[TextAnalysis] BART zero-shot classifier loaded")
    except Exception as e:
        _MODEL_ERROR = str(e)
        _MODEL_LOADED = True
        logger.warning(f"[TextAnalysis] Model load failed (heuristics only): {e}")


# ── Scam keyword rules ────────────────────────────────────────────────────────

_SCAM_KEYWORDS = [
    # Financial scams
    "earn money fast", "make money online", "investment opportunity",
    "guaranteed returns", "double your money", "passive income",
    "financial freedom", "get rich", "crypto investment", "forex signals",
    "binary options", "pump and dump", "100% profit",
    # Social engineering
    "dm me", "dm for details", "link in bio", "click the link",
    "limited offer", "act now", "don't miss out", "exclusive deal",
    "free gift", "claim your prize", "you have been selected",
    # Fake authority
    "official account", "verified seller", "trusted trader",
    "government approved", "celebrity endorsed",
    # Urgency / pressure
    "only today", "last chance", "hurry up", "time sensitive",
    "slots filling fast", "limited spots",
]

_SCAM_PATTERNS = [
    r"\b\d+[x%]\s*(profit|return|gain)\b",          # "10x profit", "500% return"
    r"\bwhatsapp\s*:?\s*\+?\d{7,}\b",               # WhatsApp numbers in bio
    r"\btelegram\s*:?\s*@\w+\b",                     # Telegram handles
    r"\b(bit\.ly|tinyurl|t\.co)/\w+\b",             # shortened URLs
    r"\$\d+[k]?\s*(daily|weekly|monthly)\b",         # "$500 daily"
    r"\b(paypal|cashapp|venmo)\s*:?\s*\$?\w+\b",    # payment handles
]

# ── AI-generated text heuristics ─────────────────────────────────────────────

_AI_BUZZWORDS = [
    "passionate about", "dedicated to", "committed to", "striving to",
    "leveraging", "synergy", "innovative solutions", "thought leader",
    "disruptive", "game changer", "visionary", "empowering",
    "transformative", "cutting-edge", "world-class", "best-in-class",
    "holistic approach", "dynamic professional", "results-driven",
    "forward-thinking", "paradigm shift",
]

_GENERIC_PHRASES = [
    "living my best life", "love what you do", "dream big",
    "work hard play hard", "blessed and grateful", "good vibes only",
    "making memories", "chasing dreams", "hustle never stops",
    "entrepreneur mindset", "lifestyle blogger",
]


def _detect_scam(text: str) -> tuple[float, list[str]]:
    """Returns (scam_probability 0-1, matched_keywords)."""
    lower = text.lower()
    matched = []

    for kw in _SCAM_KEYWORDS:
        if kw in lower:
            matched.append(kw)

    for pattern in _SCAM_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            matched.append(m.group(0)[:40])

    # Probability: each match adds weight, capped at 1.0
    prob = min(1.0, len(matched) * 0.25)
    return round(prob, 3), matched


def _detect_ai_generated(text: str) -> tuple[float, list[str]]:
    """
    Heuristic AI-text detection.
    Returns (ai_probability 0-1, signals).
    """
    lower = text.lower()
    signals = []
    score = 0.0

    # Buzzword density
    buzz_hits = [w for w in _AI_BUZZWORDS if w in lower]
    if len(buzz_hits) >= 2:
        signals.append(f"ai_buzzwords: {', '.join(buzz_hits[:3])}")
        score += 0.25 * min(len(buzz_hits), 3)

    # Generic phrase hits
    generic_hits = [p for p in _GENERIC_PHRASES if p in lower]
    if generic_hits:
        signals.append(f"generic_phrases: {', '.join(generic_hits[:2])}")
        score += 0.20 * min(len(generic_hits), 2)

    # Emoji overuse (>5 emojis in short text)
    emoji_count = sum(1 for c in text if unicodedata.category(c) in ('So', 'Sm'))
    if emoji_count > 5 and len(text) < 200:
        signals.append(f"emoji_overuse: {emoji_count} emojis")
        score += 0.15

    # Excessive capitalization (>30% caps in words)
    words = re.findall(r'\b[A-Z]{2,}\b', text)
    if len(words) > 3:
        signals.append(f"excessive_caps: {len(words)} all-caps words")
        score += 0.10

    # Repetitive punctuation (!!!, ???)
    if re.search(r'[!?]{3,}', text):
        signals.append("repetitive_punctuation")
        score += 0.10

    # Very uniform sentence length (AI tends to write uniform sentences)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 4 and avg > 5:
            signals.append("uniform_sentence_structure")
            score += 0.15

    return round(min(score, 1.0), 3), signals


def _classify_with_model(text: str) -> dict:
    """
    Zero-shot classification using BART-large-mnli.
    Only trusts model result when confidence > 0.55 to avoid false positives.
    """
    if not _classifier:
        return {"label": "unknown", "scores": {}}

    try:
        candidate_labels = ["normal personal bio", "suspicious promotional content", "scam or spam"]
        result = _classifier(text[:512], candidate_labels=candidate_labels)
        labels = result["labels"]
        scores = result["scores"]

        label_map = {
            "normal personal bio": "normal",
            "suspicious promotional content": "suspicious",
            "scam or spam": "scam",
        }

        top_label = label_map.get(labels[0], "normal")
        top_score = scores[0]
        score_dict = {label_map.get(l, l): round(s, 3) for l, s in zip(labels, scores)}

        # Only accept non-normal classification if confidence is high enough
        # This prevents false positives on innocent bios
        if top_label != "normal" and top_score < 0.55:
            top_label = "normal"

        return {"label": top_label, "scores": score_dict, "top_score": top_score}
    except Exception as e:
        logger.warning(f"[TextAnalysis] Classification failed: {e}")
        return {"label": "unknown", "scores": {}, "top_score": 0.0}


# ── Score computation ─────────────────────────────────────────────────────────

def _compute_text_score(
    text: str,
    scam_prob: float,
    ai_prob: float,
    classification: str,
    flags: list[str],
) -> int:
    score = 100

    # Empty / very short bio
    if not text or len(text.strip()) < 3:
        return 20   # hard floor for empty bio

    if len(text.strip()) < 15:
        score -= 10
        flags.append("very_short_bio")

    # Scam signals
    if scam_prob >= 0.75:
        score -= 35
    elif scam_prob >= 0.50:
        score -= 25
    elif scam_prob >= 0.25:
        score -= 15

    # AI-generated signals
    if ai_prob >= 0.60:
        score -= 20
    elif ai_prob >= 0.35:
        score -= 10

    # Model classification
    if classification == "scam":
        score -= 25
    elif classification == "suspicious":
        score -= 15

    return max(5, min(100, score))


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_text(bio: str, extra_text: str = "") -> dict:
    """
    Main entry point for text analysis.

    Args:
        bio:        Profile bio string (from OCR or URL)
        extra_text: Optional additional text (captions, comments)

    Returns:
    {
        "text_score":             int,    # 0–100
        "scam_probability":       float,
        "ai_generated_probability": float,
        "classification":         str,    # normal | suspicious | scam | unknown
        "scam_keywords":          list,   # matched scam keywords
        "ai_signals":             list,   # detected AI-text signals
        "flags":                  list,   # summary flags
        "source":                 str,    # "nlp" | "heuristic" | "fallback"
    }
    """
    # Lazy-load model on first call
    _load_model()

    combined = " ".join(filter(None, [bio, extra_text])).strip()

    # No text at all
    if not combined:
        return {
            "text_score": 25,
            "scam_probability": 0.0,
            "ai_generated_probability": 0.0,
            "classification": "unknown",
            "scam_keywords": [],
            "ai_signals": [],
            "flags": ["no_text_data"],
            "source": "fallback",
        }

    flags = []

    # Layer 1: Scam detection
    scam_prob, scam_keywords = _detect_scam(combined)
    if scam_prob > 0:
        flags.append("contains_scam_keywords")

    # Layer 2: AI-text heuristics
    ai_prob, ai_signals = _detect_ai_generated(combined)
    if ai_prob >= 0.35:
        flags.append("generic_ai_text")

    # Layer 3: Model classification
    model_result = _classify_with_model(combined)
    classification = model_result["label"]
    source = "nlp" if _classifier else "heuristic"

    if classification in ("suspicious", "scam"):
        flags.append(f"classified_{classification}")

    # Layer 4: Score
    text_score = _compute_text_score(combined, scam_prob, ai_prob, classification, flags)

    if len(combined.strip()) < 15:
        flags.append("low_information")

    logger.info(
        f"[TextAnalysis] score={text_score} scam={scam_prob} ai={ai_prob} "
        f"class={classification} flags={flags} source={source}"
    )

    return {
        "text_score": text_score,
        "scam_probability": scam_prob,
        "ai_generated_probability": ai_prob,
        "classification": classification,
        "scam_keywords": scam_keywords[:5],   # cap stored keywords
        "ai_signals": ai_signals[:5],
        "flags": flags,
        "source": source,
    }
