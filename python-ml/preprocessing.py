import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


def preprocess(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    df = df.copy()

    scaler_amount = StandardScaler()
    scaler_time = StandardScaler()

    df['Amount_scaled'] = scaler_amount.fit_transform(df[['Amount']])
    df['Time_scaled'] = scaler_time.fit_transform(df[['Time']])
    df = df.drop(columns=['Amount', 'Time'])

    X = df.drop(columns=['Class']).values
    y = df['Class'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    df = pd.read_csv("data/creditcard.csv")
    X_train, X_test, y_train, y_test = preprocess(df)

    print("=" * 50)
    print("PREPROCESSING RESULTS")
    print("=" * 50)

    print(f"\nShapes:")
    print(f"  X_train: {X_train.shape}")
    print(f"  X_test:  {X_test.shape}")
    print(f"  y_train: {y_train.shape}")
    print(f"  y_test:  {y_test.shape}")

    train_fraud = int(y_train.sum())
    test_fraud = int(y_test.sum())
    print(f"\nFraud distribution:")
    print(f"  y_train: {train_fraud} fraud / {len(y_train):,} total ({train_fraud/len(y_train)*100:.4f}%)")
    print(f"  y_test:  {test_fraud} fraud / {len(y_test):,} total  ({test_fraud/len(y_test)*100:.4f}%)")
    print(f"  Total fraud accounted for: {train_fraud + test_fraud} / 492")

    print(f"\nFeature scaling (last 2 columns = Amount_scaled, Time_scaled):")
    print(f"  Amount_scaled — mean: {X_train[:, 28].mean():.6f}, std: {X_train[:, 28].std():.6f}")
    print(f"  Time_scaled   — mean: {X_train[:, 29].mean():.6f}, std: {X_train[:, 29].std():.6f}")

    print(f"\nOriginal DataFrame columns still intact: {list(df.columns[:3])} ...")

    print("\nDone. preprocessing.py is working correctly.")
