from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.config import settings


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=12000)),
        ("classifier", LogisticRegression(max_iter=1500, class_weight="balanced")),
    ])


def train_model(data_path: Path = settings.incident_path, model_path: Path = settings.model_path) -> dict:
    df = pd.read_csv(data_path)
    x = (df["title"].fillna("") + " " + df["description"].fillna("")).str.strip()
    y = df["category"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    model = build_pipeline()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    report = classification_report(y_test, predictions, output_dict=True)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return report


if __name__ == "__main__":
    report = train_model()
    print(f"Accuracy: {report['accuracy']:.3f}")
