"""
Recommendation Subsystem (Chapter 4.3.3 / 4.4.5 "Recommendation Algorithm").

Combines item-based Collaborative Filtering (built from the
user_interventions rating matrix) with content-based filtering against
the user's current stress severity_level / stress_category. CF needs
enough overlapping rating history to produce a similarity signal, so a
new system (or a new user) falls back to pure content-based ranking by
effectiveness_rating -- this cold-start fallback is itself standard
practice for recommender systems (Ricci, Rokach, & Shapira, 2015), not
a shortcut around CF.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import db

MIN_RATINGS_FOR_CF = 5
TOP_N_DEFAULT = 5


def _content_based(severity_level: str, stress_category: str, exclude_ids=None, limit=10):
    exclude_ids = exclude_ids or set()
    rows = db.query_all(
        """
        SELECT intervention_id, intervention_name, intervention_type, description,
               target_severity, effectiveness_rating
        FROM interventions
        WHERE target_severity = %s OR intervention_type = %s
        ORDER BY effectiveness_rating DESC
        """,
        (severity_level, stress_category),
    )
    return [r for r in rows if r["intervention_id"] not in exclude_ids][:limit]


def _collaborative_filtering(user_id: int, severity_level: str, stress_category: str, limit=10):
    ratings = db.query_all(
        "SELECT user_id, intervention_id, rating FROM user_interventions WHERE rating IS NOT NULL"
    )
    if len(ratings) < MIN_RATINGS_FOR_CF:
        return []

    user_ids = sorted({r["user_id"] for r in ratings})
    item_ids = sorted({r["intervention_id"] for r in ratings})
    if user_id not in user_ids or len(item_ids) < 2:
        return []

    u_index = {u: i for i, u in enumerate(user_ids)}
    i_index = {it: i for i, it in enumerate(item_ids)}

    matrix = np.zeros((len(user_ids), len(item_ids)))
    for r in ratings:
        matrix[u_index[r["user_id"]], i_index[r["intervention_id"]]] = r["rating"]

    # Item-item similarity (columns of the rating matrix).
    item_vectors = matrix.T
    sim = cosine_similarity(item_vectors)

    this_user_row = matrix[u_index[user_id]]
    rated_idx = np.nonzero(this_user_row)[0]
    if len(rated_idx) == 0:
        return []

    scores = np.zeros(len(item_ids))
    for idx in rated_idx:
        liked_weight = this_user_row[idx] / 5.0
        scores += sim[idx] * liked_weight
    # Don't recommend what the user already rated.
    scores[rated_idx] = -np.inf

    ranked_item_indices = np.argsort(scores)[::-1]
    candidate_ids = [item_ids[i] for i in ranked_item_indices if scores[i] > 0][:limit]
    if not candidate_ids:
        return []

    placeholders = ",".join(["%s"] * len(candidate_ids))
    rows = db.query_all(
        f"""
        SELECT intervention_id, intervention_name, intervention_type, description,
               target_severity, effectiveness_rating
        FROM interventions WHERE intervention_id IN ({placeholders})
        """,
        tuple(candidate_ids),
    )
    by_id = {r["intervention_id"]: r for r in rows}
    return [by_id[i] for i in candidate_ids if i in by_id]


def get_recommendations(user_id: int, severity_level: str, stress_category: str, top_n=TOP_N_DEFAULT):
    cf_results = _collaborative_filtering(user_id, severity_level, stress_category, limit=top_n)
    source_by_id = {r["intervention_id"]: "collaborative_filtering" for r in cf_results}

    remaining = max(0, top_n - len(cf_results))
    content_results = []
    if remaining > 0:
        exclude = {r["intervention_id"] for r in cf_results}
        content_results = _content_based(severity_level, stress_category, exclude_ids=exclude, limit=remaining)
        for r in content_results:
            source_by_id[r["intervention_id"]] = "content_based"

    merged = (cf_results + content_results)[:top_n]
    for r in merged:
        r["recommended_via"] = source_by_id.get(r["intervention_id"], "content_based")
    return merged
