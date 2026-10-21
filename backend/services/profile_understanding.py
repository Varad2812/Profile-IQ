"""
Profile Understanding Engine — ProfileIQ
Uses sentence-transformers + NER to understand WHO the profile belongs to.

Tasks:
  1. Profile type classification (individual/influencer/business/suspicious)
  2. Named Entity Recognition (persons, organizations)
  3. Structured summary generation
"""

import re
import logging

logger = logging.getLogger(__name__)

# ── Model singletons ──────────────────────────────────────────────────────────

_embedder   = None
_ner_pipe   = None
_EMBED_READY = False
_NER_READY   = False

# Profile type anchor phrases for embedding similarity
_TYPE_ANCHORS = {
    "individual": [
        "personal account, sharing my life and experiences",
        "just a regular person posting about daily life",
        "student, traveler, coffee lover",
    ],
    "public_figure": [
        "professional athlete, cricketer, footballer, sports star",
        "celebrity, actor, musician, public figure with verified account",
        "politician, government official, world leader",
        "famous personality with millions of followers worldwide",
    ],
    "influencer": [
        "content creator, lifestyle blogger, brand collaborations",
        "influencer sharing fashion beauty fitness travel content",
        "follow for daily inspiration and sponsored content",
    ],
    "business": [
        "official company account, products and services",
        "brand page, customer support, business inquiries",
        "shop now, official store, buy our products",
    ],
    "suspicious": [
        "earn money fast, investment opportunity, guaranteed returns",
        "dm for business, make money online, passive income",
        "crypto signals, forex trading, financial freedom",
    ],
}


def _load_embedder():
    global _embedder, _EMBED_READY
    if _EMBED_READY:
        return
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _EMBED_READY = True
        logger.info("[ProfileUnderstanding] SentenceTransformer loaded")
    except Exception as e:
        _EMBED_READY = True
        logger.warning(f"[ProfileUnderstanding] Embedder load failed: {e}")


def _load_ner():
    global _ner_pipe, _NER_READY
    if _NER_READY:
        return
    try:
        from transformers import pipeline
        _ner_pipe = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple",
            device=-1,
        )
        _NER_READY = True
        logger.info("[ProfileUnderstanding] NER pipeline loaded")
    except Exception as e:
        _NER_READY = True
        logger.warning(f"[ProfileUnderstanding] NER load failed: {e}")


# ── Profile type classification ───────────────────────────────────────────────

def _classify_profile_type(
    bio: str, username: str, followers: int = 0, following: int = 0
) -> tuple[str, float]:
    """
    Classify profile type using embedding cosine similarity against anchor phrases.
    Falls back to rule-based if embedder unavailable.
    Uses follower count as a strong contextual signal for public figures.
    """
    text = f"{username} {bio}".strip()
    if not text:
        return "unknown", 0.0

    # Rule-based fallback (always runs as baseline)
    lower = text.lower()
    rule_scores = {
        "suspicious": sum(1 for kw in [
            "earn money", "investment", "guaranteed", "dm me", "crypto",
            "forex", "passive income", "make money", "financial freedom"
        ] if kw in lower) * 0.3,
        "business": sum(1 for kw in [
            "official", "store", "shop", "brand", "company", "ltd", "inc",
            "services", "contact us", "inquiries", "support"
        ] if kw in lower) * 0.25,
        "influencer": sum(1 for kw in [
            "content creator", "blogger", "youtuber", "collab", "sponsored",
            "ambassador", "influencer", "creator", "media kit"
        ] if kw in lower) * 0.25,
        "public_figure": sum(1 for kw in [
            "athlete", "cricketer", "footballer", "player", "captain",
            "actor", "actress", "singer", "musician", "celebrity",
            "politician", "minister", "president", "mp", "mla",
            "olympian", "world cup", "champion", "medal",
        ] if kw in lower) * 0.3,
        "individual": sum(1 for kw in [
            "student", "mom", "dad", "wife", "husband", "lover", "fan",
            "just", "living", "coffee", "dog", "cat", "travel"
        ] if kw in lower) * 0.2,
    }

    # High follower count is a strong signal for public figure/influencer
    # Accounts with millions of followers are almost never regular individuals
    ff_ratio = followers / (following + 1)
    if followers >= 5_000_000:
        rule_scores["public_figure"] += 0.5
        rule_scores["business"] = max(0, rule_scores["business"] - 0.15)
    elif followers >= 1_000_000:
        rule_scores["public_figure"] += 0.3
    elif followers >= 100_000:
        rule_scores["influencer"] += 0.15
        rule_scores["public_figure"] += 0.1

    # Very high follower-to-following ratio with high followers = public figure
    if ff_ratio > 1000 and followers >= 1_000_000:
        rule_scores["public_figure"] += 0.2

    if _embedder:
        try:
            import numpy as np
            from sentence_transformers import util

            text_emb = _embedder.encode(text[:256], convert_to_tensor=True)
            best_type = "individual"
            best_score = 0.0

            for ptype, anchors in _TYPE_ANCHORS.items():
                anchor_embs = _embedder.encode(anchors, convert_to_tensor=True)
                sims = util.cos_sim(text_emb, anchor_embs)[0]
                avg_sim = float(sims.mean())
                # Combine embedding similarity with rule score
                combined = avg_sim * 0.7 + rule_scores.get(ptype, 0) * 0.3
                if combined > best_score:
                    best_score = combined
                    best_type = ptype

            # ── Post-classification sanity checks ─────────────────────────
            # Embeddings can be noisy for short bios — enforce follower
            # thresholds so small accounts don't get absurd labels.
            if best_type == "public_figure" and followers < 100_000:
                best_type = "individual"
            if best_type == "influencer" and followers < 10_000:
                best_type = "individual"

            confidence = round(min(0.95, best_score + 0.3), 2)
            return best_type, confidence

        except Exception as e:
            logger.warning(f"[ProfileUnderstanding] Embedding classification failed: {e}")

    # Pure rule-based fallback
    if not any(rule_scores.values()):
        return "individual", 0.4

    best = max(rule_scores, key=rule_scores.get)
    # Same sanity checks as embedder path
    if best == "public_figure" and followers < 100_000:
        best = "individual"
    if best == "influencer" and followers < 10_000:
        best = "individual"
    conf = round(min(0.85, rule_scores[best] + 0.3), 2)
    return best, conf


# ── Named Entity Recognition ──────────────────────────────────────────────────

def _clean_ner_token(word: str) -> str:
    """Clean up WordPiece subword tokens (e.g. '##oh' -> 'oh') and reconstruct."""
    # Remove all ## prefixes and join fragments
    cleaned = word.replace(" ##", "").replace("##", "")
    return cleaned.strip()


def _extract_entities(text: str) -> list[str]:
    """Extract person and organization names from text."""
    if not text or not _ner_pipe:
        return _rule_based_entities(text)

    try:
        results = _ner_pipe(text[:512])
        entities = []
        for r in results:
            if r.get("entity_group") in ("PER", "ORG") and r.get("score", 0) > 0.75:
                word = _clean_ner_token(r.get("word", ""))
                # Skip single characters, pure punctuation, or hash fragments
                if len(word) > 1 and word not in entities and not word.startswith("#"):
                    entities.append(word)
        return entities[:8]
    except Exception as e:
        logger.warning(f"[ProfileUnderstanding] NER failed: {e}")
        return _rule_based_entities(text)


def _rule_based_entities(text: str) -> list[str]:
    """Simple regex-based entity extraction as fallback."""
    if not text:
        return []
    # Capitalized words that look like names (2+ consecutive)
    matches = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
    return list(dict.fromkeys(matches))[:5]   # deduplicate, cap at 5


# ── Summary generation ────────────────────────────────────────────────────────

_SUMMARY_TEMPLATES = {
    "individual": [
        "This appears to be a personal account belonging to an individual sharing everyday life content.",
        "The profile shows characteristics of a genuine personal account with organic activity patterns.",
    ],
    "public_figure": [
        "This profile belongs to a public figure, celebrity, or professional athlete with a large verified following.",
        "This is a high-profile account belonging to a well-known personality with significant public recognition.",
    ],
    "influencer": [
        "This profile appears to belong to a content creator or influencer focused on audience engagement.",
        "The account shows influencer-style characteristics including promotional language and content creation focus.",
    ],
    "business": [
        "This appears to be a business or brand account representing a company, product, or service.",
        "The profile exhibits commercial characteristics consistent with an official brand or business presence.",
    ],
    "suspicious": [
        "This profile contains multiple indicators associated with scam or spam accounts, including promotional language and financial solicitation.",
        "The account shows strong suspicious signals including potential financial scam patterns in the bio text.",
    ],
    "unknown": [
        "Insufficient profile data to determine account type with confidence.",
    ],
}


def _generate_summary(
    profile_type: str,
    bio: str,
    platform: str,
    entities: list,
    behavior_flags: list,
) -> str:
    import random
    rng = random.Random(hash(bio + profile_type))

    base = rng.choice(_SUMMARY_TEMPLATES.get(profile_type, _SUMMARY_TEMPLATES["unknown"]))

    # Enrich with platform
    if platform and platform != "unknown":
        base += f" The account was detected on {platform.title()}."

    # Enrich with entities
    if entities:
        names = ", ".join(entities[:3])
        base += f" Notable entities identified: {names}."

    # Enrich with behavior flags
    if "low_activity" in behavior_flags:
        base += " Activity levels are lower than expected for the follower count."
    if "unusual_growth_pattern" in behavior_flags:
        base += " Follower-to-post ratio suggests possible inorganic growth."
    if "mass_following_pattern" in behavior_flags:
        base += " Following pattern is consistent with mass-follow automation."

    return base


# ── Public API ────────────────────────────────────────────────────────────────

def understand_profile(
    bio: str = "",
    username: str = "",
    raw_text: str = "",
    platform: str = "unknown",
    behavior_flags: list = None,
    **kwargs,
) -> dict:
    """
    Main entry point for profile understanding.

    Returns:
    {
        "profile_type":  str,    # individual|influencer|business|suspicious|unknown
        "entities":      list,   # extracted person/org names
        "summary":       str,    # AI-generated profile summary
        "confidence":    float,
        "source":        str,
    }
    """
    _load_embedder()
    _load_ner()

    behavior_flags = behavior_flags or []
    combined_text = " ".join(filter(None, [bio, username, raw_text[:300]])).strip()

    if not combined_text:
        return {
            "profile_type": "unknown",
            "entities": [],
            "summary": "No profile text available for analysis.",
            "confidence": 0.0,
            "source": "fallback",
        }

    # Parse follower/following counts for contextual classification
    from services.behavior_analysis import _parse_count
    followers_int = _parse_count(kwargs.get("followers", 0))
    following_int = _parse_count(kwargs.get("following", 0))

    profile_type, confidence = _classify_profile_type(
        bio or combined_text, username,
        followers=followers_int, following=following_int,
    )
    entities = _extract_entities(combined_text)
    summary = _generate_summary(profile_type, bio, platform, entities, behavior_flags)

    source = "sentence_transformer" if _embedder else "rule_based"

    logger.info(
        f"[ProfileUnderstanding] type={profile_type} conf={confidence} "
        f"entities={entities} source={source}"
    )

    return {
        "profile_type": profile_type,
        "entities": entities,
        "summary": summary,
        "confidence": confidence,
        "source": source,
    }
