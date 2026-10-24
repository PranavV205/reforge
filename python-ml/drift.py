import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def detect_drift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    p_value_threshold: float = 0.05,
    drift_feature_ratio: float = 0.30,
    max_reference_rows: int = 10_000,
    random_state: int = 42,
) -> dict:
    """Two-sample KS test on every feature column.

    Drift is confirmed when MORE than drift_feature_ratio of the features have a
    p-value below p_value_threshold. Both frames must hold the model's feature
    columns (see preprocessing.FEATURE_COLUMNS), not raw transactions.
    """
    missing = set(reference_df.columns) - set(current_df.columns)
    if missing:
        raise ValueError(f"current_df is missing feature columns: {sorted(missing)}")

    # With millions of reference rows every tiny difference becomes "significant",
    # so compare against a sample of the reference instead.
    if len(reference_df) > max_reference_rows:
        reference_df = reference_df.sample(max_reference_rows, random_state=random_state)

    feature_scores = {}
    for col in reference_df.columns:
        stat, p = ks_2samp(reference_df[col], current_df[col])
        feature_scores[col] = {"ks_stat": float(stat), "p_value": float(p)}

    drifted = [c for c, s in feature_scores.items() if s["p_value"] < p_value_threshold]
    ratio = len(drifted) / len(feature_scores)
    return {
        "drift_detected": ratio > drift_feature_ratio,
        "drifted_features": drifted,
        "drift_ratio": ratio,
        "feature_scores": feature_scores,
    }


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    cols = [f"f{i}" for i in range(10)]
    reference = pd.DataFrame(rng.normal(size=(5000, 10)), columns=cols)

    same = detect_drift(reference, pd.DataFrame(rng.normal(size=(2000, 10)), columns=cols))
    assert not same["drift_detected"], same["drifted_features"]

    shifted = pd.DataFrame(rng.normal(size=(2000, 10)), columns=cols)
    shifted[cols[:5]] += 1.0  # half the features move
    moved = detect_drift(reference, shifted)
    # the 5 shifted features must all be caught; an untouched one may trip by chance at p < 0.05
    assert moved["drift_detected"] and set(cols[:5]) <= set(moved["drifted_features"]), moved

    print("drift.py self-check passed")
