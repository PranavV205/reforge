import numpy as np
import pandas as pd


def inject_drift(df: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    """Simulate "the world changed" on raw PaySim rows (demo only).

    Amounts grow 10x, 60% of transactions move to night hours (0 to 5), and half
    of them become TRANSFERs. Returns a new frame; the input is untouched.
    """
    rng = np.random.default_rng(random_state)
    out = df.copy()
    out["amount"] = out["amount"] * 10

    night = rng.random(len(out)) < 0.6
    day_start = (out["step"] // 24) * 24  # keep the day, move the hour
    out["step"] = np.where(night, day_start + rng.integers(0, 6, len(out)), out["step"])

    to_transfer = rng.random(len(out)) < 0.5
    out["type"] = np.where(to_transfer, "TRANSFER", out["type"])
    return out


if __name__ == "__main__":
    from drift import detect_drift
    from preprocessing import build_features, preprocess

    raw = pd.read_csv("data/paysim.csv")
    X_train, X_test, _, _ = preprocess(raw)

    batch = raw.sample(2000, random_state=1)
    quiet = build_features(batch.assign(hour_of_day=batch["step"] % 24))
    drifted_raw = inject_drift(batch)
    loud = build_features(drifted_raw.assign(hour_of_day=drifted_raw["step"] % 24))

    for name, current in [("normal batch", quiet), ("drifted batch", loud)]:
        r = detect_drift(X_train, current)
        print(f"{name:14s} drift={r['drift_detected']!s:5s} ratio={r['drift_ratio']:.2f} "
              f"drifted={r['drifted_features']}")
