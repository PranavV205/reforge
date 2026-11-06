import numpy as np
import pandas as pd

# Load
df = pd.read_csv("data/paysim.csv")

# Shape
print("=" * 50)
print("SHAPE")
print("=" * 50)
print(f"Rows: {df.shape[0]:,}  Columns: {df.shape[1]}")
print(f"Columns: {df.columns.tolist()}")

# Missing values
print(f"\nMissing values: {df.isnull().sum().sum()}")

# Class distribution
counts = df["isFraud"].value_counts()
print("\n" + "=" * 50)
print("CLASS DISTRIBUTION")
print("=" * 50)
print(f"Legitimate (0): {counts[0]:,}  ({counts[0] / len(df) * 100:.3f}%)")
print(f"Fraud (1):      {counts[1]:,}  ({counts[1] / len(df) * 100:.3f}%)")

# Transaction types and where fraud happens
print("\n" + "=" * 50)
print("FRAUD BY TRANSACTION TYPE")
print("=" * 50)
by_type = df.groupby("type")["isFraud"].agg(total="count", fraud="sum")
by_type["fraud_rate_%"] = (by_type["fraud"] / by_type["total"] * 100).round(3)
print(by_type)

# Account draining (sender had money before, none after)
drained = (df["oldbalanceOrg"] > 0) & (df["newbalanceOrig"] == 0)
drained_rate = drained.groupby(df["isFraud"]).mean() * 100
print("\nSender's account drained:")
print(f"  Fraud:      {drained_rate[1]:.1f}%")
print(f"  Legitimate: {drained_rate[0]:.1f}%")

# Amounts
print("\n" + "=" * 50)
print("AMOUNT")
print("=" * 50)
print(df["amount"].describe().round(2))
print("\nMedian amount by class:")
print(df.groupby("isFraud")["amount"].median().round(2))

# Skew before and after log transform
print("\nMean vs median, raw:    "
      f"{df['amount'].mean():,.0f} vs {df['amount'].median():,.0f}")
logged = np.log1p(df["amount"])
print(f"Mean vs median, logged: {logged.mean():.2f} vs {logged.median():.2f}")

# Hour of day
df["hour_of_day"] = df["step"] % 24
print("\n" + "=" * 50)
print("FRAUD RATE BY HOUR OF DAY")
print("=" * 50)
by_hour = df.groupby("hour_of_day")["isFraud"].agg(total="count", fraud_rate="mean")
by_hour["fraud_rate"] = (by_hour["fraud_rate"] * 100).round(3)
print(by_hour)

# The flagged column
print(f"\nRows flagged by the simulator's rule: {df['isFlaggedFraud'].sum()}")
