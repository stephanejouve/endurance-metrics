"""Training load metrics: ACWR, Monotony, Strain.

Computes acute/chronic workload ratio and training monotony/strain
from 28 days of activity data.

References:
    - ACWR: Gabbett (2016) - 0.8-1.3 optimal, >1.5 danger
    - Monotony: Foster (1998) - >2.0 = elevated illness risk
    - Strain: Foster (1998) - >3500 associated with overtraining
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from statistics import mean, stdev


def compute_training_load(
    activities_28d: list[dict],
    *,
    load_field: str = "load",
    date_field: str = "date",
) -> dict:
    """Compute ACWR, Monotony, Strain from 28 days of activities.

    Args:
        activities_28d: List of activity dicts.
        load_field: Key for the training load value in each dict (default: "load").
        date_field: Key for the date string in each dict (default: "date").

    Returns:
        Dict with acwr, monotony, strain, acute_load, chronic_load.
        Empty dict on failure.
    """
    if not activities_28d:
        return {}

    today = datetime.now().date()
    daily_load: dict[str, float] = {}
    for i in range(28):
        d = (today - timedelta(days=27 - i)).isoformat()
        daily_load[d] = 0.0

    for act in activities_28d:
        load_val = act.get(load_field)
        if load_val is None:
            continue
        date_str = act.get(date_field, "")[:10]
        if date_str in daily_load:
            daily_load[date_str] += float(load_val)

    sorted_days = sorted(daily_load.keys())
    all_values = [daily_load[d] for d in sorted_days]

    if len(all_values) < 7:
        return {}

    acute_values = all_values[-7:]
    chronic_values = all_values

    acute_load = sum(acute_values) / 7
    chronic_load = sum(chronic_values) / 28

    acwr = round(acute_load / chronic_load, 2) if chronic_load > 0 else 0.0

    acute_mean = mean(acute_values)
    acute_stdev = stdev(acute_values) if len(acute_values) > 1 else 0.0
    monotony = round(acute_mean / acute_stdev, 2) if acute_stdev > 0 else 0.0

    weekly_load = sum(acute_values)
    strain = round(weekly_load * monotony, 0)

    return {
        "acwr": acwr,
        "monotony": monotony,
        "strain": strain,
        "acute_load": round(acute_load, 1),
        "chronic_load": round(chronic_load, 1),
    }


def count_consecutive_training_days(
    activities_28d: list[dict],
    min_load: float = 20.0,
    *,
    load_field: str = "load",
    date_field: str = "date",
) -> dict:
    """Count current streak of consecutive training days ending today.

    Args:
        activities_28d: Activity list.
        min_load: Minimum daily load to count as a training day (default 20).
        load_field: Key for the training load value (default: "load").
        date_field: Key for the date string (default: "date").

    Returns:
        Dict with consecutive_days, streak_dates, streak_load.
        Empty dict on failure.
    """
    if not activities_28d:
        return {}

    today = date.today()
    daily_load: dict[date, float] = {}
    for act in activities_28d:
        load_val = act.get(load_field)
        if load_val is None:
            continue
        date_str = act.get(date_field, "")[:10]
        if not date_str:
            continue
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            continue
        daily_load[d] = daily_load.get(d, 0.0) + float(load_val)

    if not daily_load:
        return {}

    streak_dates: list[str] = []
    streak_load = 0.0
    current = today
    while True:
        day_load = daily_load.get(current, 0.0)
        if day_load < min_load:
            break
        streak_dates.append(current.isoformat())
        streak_load += day_load
        current -= timedelta(days=1)

    if not streak_dates:
        return {}

    return {
        "consecutive_days": len(streak_dates),
        "streak_dates": list(reversed(streak_dates)),
        "streak_load": round(streak_load, 1),
    }
