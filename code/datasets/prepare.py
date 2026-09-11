"""Clean raw UCI observations and hold out entire hull geometries."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ["buoyancy", "prismatic", "length_displacement", "beam_draught", "length_beam", "froude"]
TARGET = "resistance"


def clean_data(frame):
    frame = frame.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    # Drop incomplete observations: only 7 columns and no missing values in the original.
    frame = frame.dropna().drop_duplicates()
    valid = frame["prismatic"].between(0, 1, inclusive="neither")
    valid &= (frame[["length_displacement", "beam_draught", "length_beam", "froude"]] > 0).all(axis=1)
    valid &= frame[TARGET] >= 0
    return frame.loc[valid].copy()


def remove_training_outliers(train):
    # Fit feature-only fences on training data. Never trim test targets to improve scores.
    # Buoyancy/prismatic are deliberately sparse experimental settings; their rare
    # levels are valid designs, so do not reject them with frequency-based fences.
    continuous = FEATURES[2:]
    q1, q3 = train[continuous].quantile(0.25), train[continuous].quantile(0.75)
    spread = q3 - q1
    lower, upper = q1 - 3 * spread, q3 + 3 * spread
    valid = ((train[continuous] >= lower) & (train[continuous] <= upper)).all(axis=1)
    return train.loc[valid].copy(), {"lower": lower.to_dict(), "upper": upper.to_dict()}


def prepare(root=ROOT):
    raw = pd.read_csv(root / "data/raw/yacht_hydrodynamics.data", sep=r"\s+", header=None)
    if raw.shape[1] != 7:
        raise ValueError("Expected six features and one target in the raw file")
    raw.columns = FEATURES + [TARGET]
    clean = clean_data(raw)
    groups = clean[FEATURES[:5]].astype(str).agg("|".join, axis=1)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(clean, groups=groups))
    train, test = clean.iloc[train_idx], clean.iloc[test_idx]
    before = len(train)
    train, fences = remove_training_outliers(train)
    if len(train) < 20 or len(test) < 10:
        raise ValueError("Too few valid observations for training and evaluation")
    (root / "data/processed").mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    train.to_csv(root / "data/processed/train.csv", index=False)
    test.to_csv(root / "data/processed/test.csv", index=False)
    report = {"raw_rows": len(raw), "clean_rows": len(clean), "invalid_or_duplicate_rows_removed": len(raw)-len(clean),
              "training_outliers_removed": before-len(train), "train_rows": len(train), "test_rows": len(test),
              "train_hulls": len(train[FEATURES[:5]].drop_duplicates()), "test_hulls": len(test[FEATURES[:5]].drop_duplicates()),
              "split": "GroupShuffleSplit by five hull geometry features; seed=42", "outlier_fences": fences}
    (root / "reports/data_quality.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    prepare()
