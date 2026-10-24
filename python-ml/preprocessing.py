import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
BALANCE_COLUMNS = ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]
LABEL_COLUMN = "isFraud"

FEATURE_COLUMNS = (
    ["amount_log"]
    + [f"{col}_log" for col in BALANCE_COLUMNS]
    + ["amount_to_balance", "hour_of_day"]
    + [f"type_{t}" for t in TRANSACTION_TYPES]
)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn transactions into the model's feature table.

    Expects columns: type, amount, the four balance columns, and hour_of_day.
    Used both for training and for scoring live transactions.
    """
    unknown = set(df["type"]) - set(TRANSACTION_TYPES)
    if unknown:
        raise ValueError(f"Unknown transaction types: {sorted(unknown)}")

    features = pd.DataFrame(index=df.index)
    features["amount_log"] = np.log1p(df["amount"])
    for col in BALANCE_COLUMNS:
        features[f"{col}_log"] = np.log1p(df[col])
    features["amount_to_balance"] = (df["amount"] / (df["oldbalanceOrg"] + 1)).clip(upper=10)
    features["hour_of_day"] = df["hour_of_day"]
    for t in TRANSACTION_TYPES:
        features[f"type_{t}"] = (df["type"] == t).astype(int)

    return features[FEATURE_COLUMNS]


def preprocess(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    df = df.assign(hour_of_day=df["step"] % 24)

    X = build_features(df)
    y = df[LABEL_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    df = pd.read_csv("data/paysim.csv")
    X_train, X_test, y_train, y_test = preprocess(df)

    print("=" * 50)
    print("PREPROCESSING RESULTS")
    print("=" * 50)

    print("\nShapes:")
    print(f"  X_train: {X_train.shape}")
    print(f"  X_test:  {X_test.shape}")

    train_fraud = int(y_train.sum())
    test_fraud = int(y_test.sum())
    total_fraud = int(df[LABEL_COLUMN].sum())
    print("\nFraud distribution:")
    print(f"  y_train: {train_fraud:,} fraud / {len(y_train):,} total ({y_train.mean() * 100:.4f}%)")
    print(f"  y_test:  {test_fraud:,} fraud / {len(y_test):,} total ({y_test.mean() * 100:.4f}%)")
    print(f"  Total fraud accounted for: {train_fraud + test_fraud:,} / {total_fraud:,}")

    print(f"\nFeature columns ({len(FEATURE_COLUMNS)}):")
    for col in FEATURE_COLUMNS:
        print(f"  {col}")

    print(f"\nMissing values in X_train: {int(X_train.isnull().sum().sum())}")
    print(f"Original DataFrame untouched: {'hour_of_day' not in df.columns}")
    print("\nDone. preprocessing.py is working correctly.")
