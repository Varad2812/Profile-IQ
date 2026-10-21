"""
Behavior Analysis Module — ProfileIQ
ML-based anomaly detection using IsolationForest.
Platform-agnostic: works for Instagram, Twitter, LinkedIn, TikTok, etc.

Pipeline:
  1. Feature engineering from follower/following/posts counts
  2. Z-score normalization
  3. IsolationForest anomaly detection (trained on synthetic normal data)
  4. Score conversion + flag generation
"""

import math
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ── Synthetic training data (normal profile distributions) ────────────────────
# Represents realistic ranges for genuine human accounts across platforms.
# IsolationForest is unsupervised — it learns what "normal" looks like.

_RNG = np.random.default_rng(42)

def _generate_training_data(n: int = 2000) -> np.ndarray:
    """
    Generate synthetic normal profile feature vectors for IsolationForest training.
    Features: [ff_ratio, posts_per_follower, log_activity, log_popularity, engagement_proxy]
    """
    rows = []

    # Micro accounts (0–1K followers) — most common
    n1 = int(n * 0.40)
    followers = _RNG.integers(10, 1000, n1).astype(float)
    following = _RNG.integers(50, 1500, n1).astype(float)
    posts     = _RNG.integers(5, 500, n1).astype(float)
    rows.append(_featurize_batch(followers, following, posts))

    # Mid-tier (1K–100K)
    n2 = int(n * 0.30)
    followers = _RNG.integers(1000, 100_000, n2).astype(float)
    following = _RNG.integers(100, 5000, n2).astype(float)
    posts     = _RNG.integers(50, 2000, n2).astype(float)
    rows.append(_featurize_batch(followers, following, posts))

    # Macro / influencer (100K–5M)
    n3 = int(n * 0.20)
    followers = _RNG.integers(100_000, 5_000_000, n3).astype(float)
    following = _RNG.integers(100, 2000, n3).astype(float)
    posts     = _RNG.integers(100, 5000, n3).astype(float)
    rows.append(_featurize_batch(followers, following, posts))

    # Celebrity / mega accounts (5M–100M) — public figures, athletes, actors
    n4 = n - n1 - n2 - n3
    followers = _RNG.integers(5_000_000, 100_000_000, n4).astype(float)
    following = _RNG.integers(50, 500, n4).astype(float)
    posts     = _RNG.integers(200, 5000, n4).astype(float)
    rows.append(_featurize_batch(followers, following, posts))

    return np.vstack(rows)


def _featurize_batch(followers, following, posts) -> np.ndarray:
    ff_ratio          = followers / (following + 1)
    posts_per_follower = posts / (followers + 1)
    log_activity      = np.log1p(posts)
    log_popularity    = np.log1p(followers)
    engagement_proxy  = np.log1p(posts) / (np.log1p(followers) + 1)
    return np.column_stack([ff_ratio, posts_per_follower, log_activity, log_popularity, engagement_proxy])


# ── Model singleton ───────────────────────────────────────────────────────────

_model = None
_scaler_mean = None
_scaler_std  = None
_MODEL_READY = False


def _ensure_model():
    global _model, _scaler_mean, _scaler_std, _MODEL_READY
    if _MODEL_READY:
        return
    try:
        from sklearn.ensemble import IsolationForest

        X = _generate_training_data(2000)

        # Z-score normalization — fit on training data
        _scaler_mean = X.mean(axis=0)
        _scaler_std  = X.std(axis=0) + 1e-8   # avoid div-by-zero

        X_scaled = (X - _scaler_mean) / _scaler_std

        _model = IsolationForest(
            n_estimators=200,
            contamination=0.08,   # ~8% of real profiles are anomalous
            random_state=42,
            n_jobs=-1,
        )
        _model.fit(X_scaled)
        _MODEL_READY = True
        logger.info("[BehaviorAnalysis] IsolationForest trained on synthetic data")

    except Exception as e:
        logger.error(f"[BehaviorAnalysis] Model init failed: {e}")
        _MODEL_READY = True   # mark done to avoid retry loop


# ── Feature engineering ───────────────────────────────────────────────────────

def _parse_count(value) -> int:
    """Parse '12.3K', '1.2M', '450' → int."""
    if not value:
        return 0
    s = str(value).strip().upper().replace(",", "")
    try:
        if s.endswith("M"):
            return int(float(s[:-1]) * 1_000_000)
        if s.endswith("K"):
            return int(float(s[:-1]) * 1_000)
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _engineer_features(followers: int, following: int, posts: int) -> np.ndarray:
    f  = max(followers, 0)
    fo = max(following, 0)
    p  = max(posts, 0)

    ff_ratio           = f / (fo + 1)
    posts_per_follower = p / (f + 1)
    log_activity       = math.log1p(p)
    log_popularity     = math.log1p(f)
    engagement_proxy   = math.log1p(p) / (math.log1p(f) + 1)

    return np.array([[ff_ratio, posts_per_follower, log_activity, log_popularity, engagement_proxy]])


# ── Flag generation ───────────────────────────────────────────────────────────

def _generate_flags(followers: int, following: int, posts: int, anomaly_score: float) -> list:
    flags = []
    ff = followers / (following + 1)

    # Ratio anomalies — only flag for smaller accounts
    # Celebrities naturally have extreme ratios (46.5M / 113 = ~411K)
    if ff > 100 and followers < 1_000_000:
        flags.append("extremely_high_follower_ratio")
    elif ff < 0.01 and followers > 100:
        flags.append("anomalous_ratio")

    # Activity anomalies
    if posts == 0:
        flags.append("no_posts")
    elif posts < 3 and followers > 1000:
        flags.append("low_activity")

    # Ghost following (following many, few followers)
    if following > 5000 and followers < 500:
        flags.append("mass_following_pattern")

    # Unusual growth (many followers, zero posts — bought followers)
    # Exclude celebrity accounts which legitimately have high follower counts
    if followers > 10000 and posts < 10 and followers < 1_000_000:
        flags.append("unusual_growth_pattern")

    # Bot-like ratio (exactly round numbers)
    if followers > 0 and followers % 1000 == 0 and posts < 20:
        flags.append("suspicious_round_numbers")

    # Strong anomaly from model
    if anomaly_score < 0.3:
        flags.append("ml_anomaly_detected")

    return flags


# ── Score conversion ──────────────────────────────────────────────────────────

def _anomaly_to_score(raw_score: float, flags: list) -> int:
    """
    IsolationForest decision_function returns:
      positive = more normal, negative = more anomalous
    We normalize to 0–100.
    """
    # Typical range is roughly -0.5 to +0.5
    # Map to 0–100: score = (raw + 0.5) / 1.0 * 100
    normalized = (raw_score + 0.5) / 1.0
    score = int(max(0.0, min(1.0, normalized)) * 100)

    # Penalty for each flag
    score -= len(flags) * 8
    return max(5, min(100, score))


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_behavior(
    followers,
    following,
    posts,
    bio: str = "",
    platform: str = "unknown",
) -> dict:
    """
    Main entry point for behavior analysis.

    Args:
        followers: int or str (e.g. "12.3K")
        following: int or str
        posts:     int or str
        bio:       profile bio text
        platform:  detected platform name

    Returns:
    {
        "behavior_score":  int,    # 0–100
        "anomaly_score":   float,  # raw IsolationForest score
        "confidence":      float,
        "flags":           list,
        "features":        dict,   # engineered features for transparency
        "source":          str,
    }
    """
    _ensure_model()

    followers_int = _parse_count(followers)
    following_int = _parse_count(following)
    posts_int     = _parse_count(posts)

    # No data at all
    if followers_int == 0 and following_int == 0 and posts_int == 0:
        return {
            "behavior_score": 30,
            "anomaly_score": 0.0,
            "confidence": 0.3,
            "flags": ["no_profile_data"],
            "features": {},
            "source": "fallback",
        }

    try:
        X = _engineer_features(followers_int, following_int, posts_int)

        # Normalize using training statistics
        X_scaled = (X - _scaler_mean) / _scaler_std

        # IsolationForest decision_function: higher = more normal
        raw_score = float(_model.decision_function(X_scaled)[0])
        prediction = int(_model.predict(X_scaled)[0])   # 1=normal, -1=anomaly

        flags = _generate_flags(followers_int, following_int, posts_int, raw_score)
        behavior_score = _anomaly_to_score(raw_score, flags)

        # Confidence: based on how far from decision boundary
        confidence = round(min(0.95, abs(raw_score) * 2 + 0.5), 2)

        features = {
            "followers": followers_int,
            "following": following_int,
            "posts": posts_int,
            "ff_ratio": round(followers_int / (following_int + 1), 3),
            "posts_per_follower": round(posts_int / (followers_int + 1), 4),
        }

        logger.info(
            f"[BehaviorAnalysis] score={behavior_score} raw={raw_score:.3f} "
            f"pred={'normal' if prediction == 1 else 'anomaly'} flags={flags}"
        )

        return {
            "behavior_score": behavior_score,
            "anomaly_score": round(raw_score, 4),
            "confidence": confidence,
            "flags": flags,
            "features": features,
            "source": "isolation_forest",
        }

    except Exception as e:
        logger.error(f"[BehaviorAnalysis] Error: {e}")
        return {
            "behavior_score": 40,
            "anomaly_score": 0.0,
            "confidence": 0.3,
            "flags": ["analysis_error"],
            "features": {},
            "source": "fallback",
        }
