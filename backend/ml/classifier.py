import os
import joblib
import numpy as np
from questions import severity_from_score, category_from_responses

_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.joblib")
_bundle = None


def _load():
    global _bundle
    if _bundle is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                "Model not trained yet. Run: python ml/train_model.py"
            )
        _bundle = joblib.load(_MODEL_PATH)
    return _bundle


def classify(responses: list[int]) -> dict:
    """
    responses: list of 10 ints (0-3), in question-id order (1..10).
    Returns total_score, severity_level (Random Forest prediction with the
    appendix scoring-guide thresholds as a sanity-checked fallback),
    stress_category, and class probabilities.
    """
    if len(responses) != 10 or any(r not in (0, 1, 2, 3) for r in responses):
        raise ValueError("responses must be exactly 10 integers between 0 and 3")

    total_score = sum(responses)
    category = category_from_responses(responses)

    try:
        bundle = _load()
        model = bundle["model"]
        X = np.array(responses, dtype=int).reshape(1, -1)
        severity = model.predict(X)[0]
        proba = model.predict_proba(X)[0]
        probabilities = {cls: round(float(p), 4) for cls, p in zip(model.classes_, proba)}
    except FileNotFoundError:
        # Fallback to the static appendix scoring guide if the model
        # hasn't been trained in this environment yet.
        severity = severity_from_score(total_score)
        probabilities = {severity: 1.0}

    return {
        "total_score": total_score,
        "severity_level": severity,
        "stress_category": category,
        "probabilities": probabilities,
    }
