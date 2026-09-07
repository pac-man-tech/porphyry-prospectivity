"""Data loading and cleaning utilities.

Functions here should handle reading raw files, applying basic cleansing,
and handling limits-of-detection (LOD) or missing-value patterns.
"""
from pathlib import Path
import pandas as pd


def read_sample_csv(path: str) -> pd.DataFrame:
    path = Path(path)
    return pd.read_csv(path)


def save_dataframe(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
