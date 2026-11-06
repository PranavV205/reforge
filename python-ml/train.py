import sys
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score

import storage
from preprocessing import preprocess

CONTAMINATION = 0.0013  # roughly the fraud rate in PaySim (0.129%)
N_ESTIMATORS = 300  # chosen on a validation slice of the training data; the default 100 trees scored worse
MAX_SAMPLES = 4096  # rows per tree; the default 256 is too few to learn "normal" on 5M rows
MODEL_PATH = "model.pkl"


def train_model(X_train: pd.DataFrame, contamination: float = CONTAMINATION) -> IsolationForest:
    """Fit an Isolation Forest. Unsupervised: labels are never passed in."""
    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        max_samples=MAX_SAMPLES,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train)
    return model


def predict_fraud(model: IsolationForest, X: pd.DataFrame) -> pd.Series:
    """Isolation Forest returns -1 for an anomaly and 1 for normal. Map to 1 = fraud, 0 = legit."""
    return pd.Series((model.predict(X) == -1).astype(int), index=X.index)


def evaluate(model: IsolationForest, X: pd.DataFrame, y: pd.Series) -> dict:
    """Labels are used here only, to grade the model."""
    pred = predict_fraud(model, X)
    return {
        "f1": f1_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred),
        "flagged": int(pred.sum()),
    }


if __name__ == "__main__":
    df = pd.read_csv("data/paysim.csv")
    X_train, X_test, y_train, y_test = preprocess(df)

    model = train_model(X_train)
    metrics = evaluate(model, X_test, y_test)
    joblib.dump(model, MODEL_PATH)

    print("=" * 50)
    print("TRAINING RESULTS")
    print("=" * 50)
    print(f"Training rows:   {len(X_train):,}")
    print(f"Test rows:       {len(X_test):,}  ({int(y_test.sum()):,} real fraud)")
    print(f"Flagged as fraud: {metrics['flagged']:,}")
    print(f"Precision: {metrics['precision']:.3f}")
    print(f"Recall:    {metrics['recall']:.3f}")
    print(f"F1:        {metrics['f1']:.3f}")
    print(f"\nModel saved to {MODEL_PATH}")

    if "--upload" in sys.argv:
        client = storage.get_client()
        version = storage.next_version(client)
        storage.save_model(model, version, client)
        storage.activate_model(version, client)
        versions = [{**v, "status": "archived"} for v in storage.load_versions(client)]
        versions.append({
            "version": version,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "f1_score": metrics["f1"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "training_set_size": len(X_train),
            "drift_trigger": False,
            "status": "active",
        })
        storage.save_versions(versions, client)
        print(f"Uploaded {version} to MinIO and set it active")
