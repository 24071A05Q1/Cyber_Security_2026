from __future__ import annotations

from functools import lru_cache

import joblib

from src.config import settings


@lru_cache(maxsize=1)
def load_model():
    if not settings.model_path.exists():
        raise FileNotFoundError("Classifier not found. Run: python scripts/bootstrap.py")
    return joblib.load(settings.model_path)


def predict_category(text: str) -> tuple[str, float]:
    model = load_model()
    probabilities = model.predict_proba([text])[0]
    best_index = int(probabilities.argmax())
    category = str(model.classes_[best_index])
    return category, float(probabilities[best_index])
