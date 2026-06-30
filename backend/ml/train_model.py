"""
Trains a Random Forest classifier for stress severity classification
(Chapter 4.4.5, "Stress Classification Algorithm").

No real-world labeled stress dataset was available (a limitation the
report itself notes in section 1.6), so this generates a synthetic
labeled dataset: each sample is a latent "true stress" level that
generates 10 correlated DASS-21-style item responses (0-3), and the
label is the severity bucket of the *latent* level with noise -- not a
simple deterministic sum threshold -- so the forest has to learn from
the joint pattern of responses rather than just re-deriving the sum.
"""
import os
import sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from questions import QUESTIONS, SEVERITY_THRESHOLDS  # noqa: E402

N_SAMPLES = 6000
N_QUESTIONS = len(QUESTIONS)
RANDOM_STATE = 42

# Severity buckets expressed as fractions of the latent stress scale [0, 1]
# (roughly matching the proportions implied by the 0-30 scoring guide).
LATENT_THRESHOLDS = [
    (0.00, 0.34, "Low"),
    (0.34, 0.65, "Moderate"),
    (0.65, 0.82, "High"),
    (0.82, 1.01, "Very High"),
]


def latent_to_severity(u: float) -> str:
    for low, high, label in LATENT_THRESHOLDS:
        if low <= u < high:
            return label
    return "Very High"


def generate_dataset(n_samples: int, rng: np.random.Generator):
    X = np.zeros((n_samples, N_QUESTIONS), dtype=int)
    y = []

    # Per-question sensitivity to the latent stress level (some items react
    # more strongly than others), plus a small fixed bias per item.
    sensitivity = rng.uniform(0.8, 1.3, size=N_QUESTIONS)
    bias = rng.uniform(-0.1, 0.1, size=N_QUESTIONS)

    for i in range(n_samples):
        # Latent stress drawn from a Beta distribution skewed toward the
        # lower/moderate range, like a real population.
        u = rng.beta(2.0, 3.0)

        # Each item's response probability rises with latent stress,
        # individual item sensitivity, and item-specific noise.
        for j in range(N_QUESTIONS):
            p = np.clip(u * sensitivity[j] + bias[j] + rng.normal(0, 0.05), 0.02, 0.98)
            X[i, j] = rng.binomial(3, p)

        # Label noise: the "true" severity is the latent level jittered
        # slightly, simulating contextual factors the questionnaire alone
        # doesn't capture.
        u_label = np.clip(u + rng.normal(0, 0.04), 0, 1)
        y.append(latent_to_severity(u_label))

    return X, np.array(y)


def main():
    rng = np.random.default_rng(RANDOM_STATE)
    X, y = generate_dataset(N_SAMPLES, rng)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {acc:.4f}")
    print(classification_report(y_test, y_pred))

    out_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(out_dir, "model.joblib")
    joblib.dump(
        {
            "model": clf,
            "feature_order": [q["id"] for q in QUESTIONS],
            "classes": list(clf.classes_),
            "accuracy": acc,
        },
        model_path,
    )
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
