"""Scoring and optimization utilities for meal plans."""

import logging
from collections import Counter

logger = logging.getLogger(__name__)


def score_weekly_time(slots: list) -> dict:
    """
    Compute time metrics for a set of meal slots.

    Returns:
        dict with total_active_min, total_passive_min, active_min_per_day,
        ingredient_overlap_pct, needs_replanning
    """
    total_active = 0
    total_passive = 0
    days_with_cooking = set()

    for slot in slots:
        if slot.status not in ("planned", "cooked") or slot.recipe is None:
            continue
        recipe = slot.recipe
        active = recipe.prep_time_min or 0
        passive = (recipe.total_time_min or 0) - active
        total_active += active
        total_passive += max(passive, 0)
        days_with_cooking.add(str(slot.date))

    day_count = len(days_with_cooking) or 1
    active_per_day = total_active / day_count

    overlap_pct = estimate_ingredient_overlap(slots)

    return {
        "total_active_min": total_active,
        "total_passive_min": total_passive,
        "active_min_per_day": round(active_per_day, 1),
        "ingredient_overlap_pct": round(overlap_pct * 100, 1),
        "needs_replanning": active_per_day > 45,
    }


def estimate_ingredient_overlap(slots: list) -> float:
    """
    Compute ingredient overlap score across all slots.

    overlap = (sum of appearances - unique count) / total appearances
    Target: > 0.3 (30% overlap)
    """
    ingredient_counts: Counter = Counter()

    for slot in slots:
        if slot.recipe is None:
            continue
        recipe = slot.recipe
        seen_in_recipe = set()
        for ri in recipe.recipe_ingredients or []:
            iid = ri.ingredient_id
            if iid not in seen_in_recipe:
                ingredient_counts[iid] += 1
                seen_in_recipe.add(iid)

    if not ingredient_counts:
        return 0.0

    total_appearances = sum(ingredient_counts.values())
    unique_count = len(ingredient_counts)

    if total_appearances == 0:
        return 0.0

    overlap = (total_appearances - unique_count) / total_appearances
    return max(0.0, overlap)
