# DASS-21-style stress assessment questionnaire (10 items, per Appendix A
# of the project report). Each question is tagged with a "theme" used by
# the ML module to derive a stress_category (which feeds the recommendation
# engine's content-based filtering) on top of the numeric severity score.

QUESTIONS = [
    {"id": 1, "text": "I feel overwhelmed by my daily responsibilities.", "theme": "Workload"},
    {"id": 2, "text": "I find it difficult to relax after work or school.", "theme": "Relaxation"},
    {"id": 3, "text": "I experience difficulty concentrating on important tasks.", "theme": "Cognitive"},
    {"id": 4, "text": "I feel nervous or anxious without obvious reasons.", "theme": "Anxiety"},
    {"id": 5, "text": "I experience sleep disturbances due to worries.", "theme": "Sleep"},
    {"id": 6, "text": "I feel emotionally exhausted most of the time.", "theme": "Emotional Exhaustion"},
    {"id": 7, "text": "I find it difficult to manage multiple tasks effectively.", "theme": "Time Management"},
    {"id": 8, "text": "I experience physical symptoms such as headaches or fatigue when stressed.", "theme": "Physical"},
    {"id": 9, "text": "I worry excessively about future events.", "theme": "Anxiety"},
    {"id": 10, "text": "I feel unable to cope with challenges effectively.", "theme": "Coping"},
]

SCALE = {
    0: "Never",
    1: "Sometimes",
    2: "Often",
    3: "Almost Always",
}

# Scoring guide from Appendix A of the report
SEVERITY_THRESHOLDS = [
    (0, 10, "Low"),
    (11, 20, "Moderate"),
    (21, 25, "High"),
    (26, 30, "Very High"),
]

THEMES = sorted({q["theme"] for q in QUESTIONS})


def severity_from_score(total_score: int) -> str:
    for low, high, label in SEVERITY_THRESHOLDS:
        if low <= total_score <= high:
            return label
    return "Very High" if total_score > 30 else "Low"


def category_from_responses(responses: list[int]) -> str:
    """Pick the theme with the highest summed response score."""
    theme_scores: dict[str, int] = {t: 0 for t in THEMES}
    for q in QUESTIONS:
        theme_scores[q["theme"]] += responses[q["id"] - 1]
    return max(theme_scores.items(), key=lambda kv: kv[1])[0]
