"""Advanced metrics utilities for training analysis.

Provides trend analysis, peak detection, recovery recommendations,
and overtraining risk assessment.

Functions:
    calculate_ramp_rate: Calculate CTL progression rate (points/week)
    get_weekly_metrics_trend: Analyze weekly metric trends
    detect_training_peaks: Detect significant training load peaks
    get_recovery_recommendation: Generate recovery recommendations
    format_metrics_comparison: Format comparison between two time periods
    detect_overtraining_risk: Detect overtraining risk (CRITICAL)
"""

from statistics import mean, stdev
from typing import Any, cast


def calculate_ramp_rate(ctl_current: float, ctl_previous: float, days: int = 7) -> float:
    """Calculate CTL (Chronic Training Load) progression rate.

    Args:
        ctl_current: Current CTL value
        ctl_previous: Previous CTL value (from 'days' ago)
        days: Number of days between measurements (default: 7 for weekly)

    Returns:
        CTL change rate in points per week.

    Examples:
        >>> calculate_ramp_rate(65.0, 60.0, days=7)
        5.0
        >>> calculate_ramp_rate(65.0, 60.0, days=14)
        2.5

    Notes:
        - Recommended max ramp rate for master athletes: 5-7 points/week
        - Rates >10 points/week indicate high injury/overtraining risk
    """
    if days <= 0:
        raise ValueError("days must be positive")
    delta = ctl_current - ctl_previous
    weeks = days / 7.0
    return delta / weeks if weeks > 0 else delta


def get_weekly_metrics_trend(
    weekly_data: list[dict[str, float]], metric: str = "ctl"
) -> dict[str, Any]:
    """Analyze trend in weekly metrics.

    Args:
        weekly_data: List of dicts with weekly metrics
        metric: Metric name to analyze (default: 'ctl')

    Returns:
        Dict with trend, slope, volatility, weeks_analyzed

    Notes:
        - 'rising': slope > 1.0 points/week
        - 'stable': slope between -1.0 and +1.0
        - 'declining': slope < -1.0
    """
    if not weekly_data:
        return {"trend": "unknown", "slope": 0.0, "volatility": 0.0, "weeks_analyzed": 0}
    if len(weekly_data) < 2:
        return {
            "trend": "insufficient_data",
            "slope": 0.0,
            "volatility": 0.0,
            "weeks_analyzed": len(weekly_data),
        }
    values = [week.get(metric, 0.0) for week in weekly_data]
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    avg_change = mean(changes)
    volatility = stdev(changes) if len(changes) > 1 else 0.0
    if avg_change > 1.0:
        trend = "rising"
    elif avg_change < -1.0:
        trend = "declining"
    else:
        trend = "stable"
    return {
        "trend": trend,
        "slope": round(avg_change, 2),
        "volatility": round(volatility, 2),
        "weeks_analyzed": len(weekly_data),
    }


def detect_training_peaks(
    ctl_history: list[float], threshold_percent: float = 10.0
) -> list[dict[str, Any]]:
    """Detect significant training load peaks in CTL history.

    Args:
        ctl_history: List of CTL values in chronological order
        threshold_percent: Minimum % increase to qualify as peak

    Returns:
        List of dicts with index, value, increase_percent, baseline

    Notes:
        - Uses 3-week rolling average as baseline
    """
    if len(ctl_history) < 4:
        return []
    peaks = []
    for i in range(3, len(ctl_history)):
        baseline = mean(ctl_history[i - 3 : i])
        current = ctl_history[i]
        increase_pct = ((current - baseline) / baseline * 100) if baseline > 0 else 0
        if increase_pct >= threshold_percent:
            peaks.append(
                {
                    "index": i,
                    "value": round(current, 1),
                    "increase_percent": round(increase_pct, 1),
                    "baseline": round(baseline, 1),
                }
            )
    return peaks


def get_recovery_recommendation(
    tsb: float, atl_ctl_ratio: float, profile: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Generate recovery recommendation based on training metrics.

    Args:
        tsb: Training Stress Balance (Form)
        atl_ctl_ratio: Ratio of ATL/CTL (Fatigue/Fitness)
        profile: Optional athlete profile dict with keys:
                 - age: int
                 - recovery_capacity: 'normal' | 'good' | 'exceptional'
                 - category: 'junior' | 'senior' | 'master'

    Returns:
        Dict with recommendation, intensity_limit (% threshold),
        duration_limit (minutes), rest_days, priority

    Notes:
        - TSB <-20 -> Critical recovery needed
        - ATL/CTL >1.5 -> High fatigue
        - Master athletes: More conservative limits
    """
    if profile is None:
        profile = {"age": 35, "recovery_capacity": "normal", "category": "senior"}
    is_master = profile.get("category") == "master" or profile.get("age", 35) >= 50
    recovery_capacity = profile.get("recovery_capacity", "normal")

    if tsb < -20 or atl_ctl_ratio > 1.6:
        priority = "critical"
    elif tsb < -15 or atl_ctl_ratio > 1.4:
        priority = "high"
    elif tsb < -10 or atl_ctl_ratio > 1.2:
        priority = "medium"
    else:
        priority = "low"

    recommendations = {
        "critical": {
            "recommendation": "Immediate rest or Z1 only. Cancel all intensity.",
            "intensity_limit": 55,
            "duration_limit": 45,
            "rest_days": 2 if is_master else 1,
        },
        "high": {
            "recommendation": "Cancel >85% threshold. Z2 endurance only, max 60min.",
            "intensity_limit": 75,
            "duration_limit": 60,
            "rest_days": 1,
        },
        "medium": {
            "recommendation": "Reduce intensity -10% OR duration -15%. Monitor closely.",
            "intensity_limit": 90,
            "duration_limit": 90,
            "rest_days": 0,
        },
        "low": {
            "recommendation": "Normal training. Follow planned sessions.",
            "intensity_limit": 100,
            "duration_limit": 120,
            "rest_days": 0,
        },
    }

    result = recommendations[priority].copy()
    result["priority"] = priority

    if is_master and priority in ["high", "critical"]:
        result["duration_limit"] = min(cast(int, result["duration_limit"]), 45)
        result["rest_days"] = cast(int, result["rest_days"]) + 1

    if recovery_capacity == "exceptional" and priority == "medium":
        result["intensity_limit"] = min(95, cast(int, result["intensity_limit"]))

    return result


def format_metrics_comparison(
    period1: dict[str, float], period2: dict[str, float], labels: dict[str, str] | None = None
) -> str:
    """Format comparison between two time periods.

    Args:
        period1: First period metrics
        period2: Second period metrics
        labels: Optional labels for periods

    Returns:
        Formatted string showing metric comparisons
    """
    if labels is None:
        labels = {"period1": "Period 1", "period2": "Period 2"}
    lines = []
    lines.append(f"\n{'=' * 60}")
    lines.append(
        f"Metrics Comparison: {labels.get('period1', 'Period 1')} "
        f"-> {labels.get('period2', 'Period 2')}"
    )
    lines.append(f"{'=' * 60}\n")
    metrics = ["ctl", "atl", "tsb"]
    for metric in metrics:
        if metric in period1 and metric in period2:
            val1 = period1[metric]
            val2 = period2[metric]
            delta = val2 - val1
            if abs(delta) < 0.5:
                direction = "->"
                change_desc = "stable"
            elif delta > 0:
                direction = "UP"
                change_desc = f"+{delta:.1f}"
            else:
                direction = "DOWN"
                change_desc = f"{delta:.1f}"
            metric_name = metric.upper()
            lines.append(f"{metric_name:6} {direction} {val1:6.1f} -> {val2:6.1f}  ({change_desc})")
    lines.append(f"{'=' * 60}\n")
    return "\n".join(lines)


def detect_overtraining_risk(
    ctl: float,
    atl: float,
    tsb: float,
    sleep_hours: float | None = None,
    consecutive_days: int | None = None,
    profile: dict[str, Any] | None = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Detect overtraining risk for athletes (CRITICAL FUNCTION).

    Combines TSB, ATL/CTL ratio, sleep quality, and athlete profile
    to assess overtraining risk and provide VETO recommendations.

    Args:
        ctl: Current Chronic Training Load (Fitness)
        atl: Current Acute Training Load (Fatigue)
        tsb: Current Training Stress Balance (Form)
        sleep_hours: Sleep duration from previous night (optional)
        consecutive_days: Number of consecutive training days (optional)
        profile: Athlete profile dict
        thresholds: Optional custom thresholds dict

    Returns:
        Dict with risk_level, veto, recommendation, factors, sleep_veto

    Notes:
        CRITICAL THRESHOLDS (Master Athlete):
        - TSB <-25 + sleep <6h -> VETO
        - ATL >CTL x 1.8 -> VETO
        - VETO means: Cancel ALL intensity, rest or Z1 only
    """
    if thresholds is None:
        thresholds = {
            "tsb_critical": -25.0,
            "tsb_fatigued": -15.0,
            "tsb_optimal_min": -5.0,
            "ratio_critical": 1.8,
            "ratio_warning": 1.5,
            "ratio_optimal": 1.3,
            "sleep_critical": 6.0,
            "sleep_veto": 5.5,
            "consecutive_days_warning": 3,
            "consecutive_days_critical": 4,
        }
    if profile is None:
        profile = {"age": 35, "category": "senior", "sleep_dependent": False}

    is_master = profile.get("category") == "master" or profile.get("age", 35) >= 50
    sleep_dependent = profile.get("sleep_dependent", False)
    atl_ctl_ratio = atl / ctl if ctl > 0 else 0

    factors = []
    veto = False
    sleep_veto = False
    risk_level = "low"

    # CRITICAL CHECKS
    if tsb < thresholds["tsb_critical"]:
        factors.append(f"TSB critically low ({tsb:.1f} < {thresholds['tsb_critical']})")
        risk_level = "critical"
        veto = True

    if atl_ctl_ratio > thresholds["ratio_critical"]:
        factors.append(
            f"ATL/CTL ratio critical ({atl_ctl_ratio:.2f} > {thresholds['ratio_critical']})"
        )
        risk_level = "critical"
        veto = True

    if sleep_hours is not None:
        if sleep_hours < thresholds["sleep_veto"]:
            factors.append(
                f"Sleep critically low ({sleep_hours:.1f}h < {thresholds['sleep_veto']}h)"
            )
            risk_level = "high" if risk_level == "low" else "critical"
            sleep_veto = True
            veto = True
        if sleep_hours < thresholds["sleep_critical"] and tsb < thresholds["tsb_fatigued"]:
            factors.append(f"Combined: Low sleep ({sleep_hours:.1f}h) + Fatigued (TSB {tsb:.1f})")
            risk_level = "critical"
            veto = True

    # HIGH RISK CHECKS
    if not veto:
        if tsb < -20:
            factors.append(f"TSB very low ({tsb:.1f})")
            risk_level = "high"
        if atl_ctl_ratio > thresholds["ratio_warning"]:
            factors.append(f"ATL/CTL ratio elevated ({atl_ctl_ratio:.2f})")
            risk_level = "high" if risk_level == "low" else risk_level
        if sleep_hours is not None and sleep_dependent:
            if sleep_hours < 7.0:
                factors.append(f"Sleep below optimal ({sleep_hours:.1f}h < 7h)")
                risk_level = "medium" if risk_level == "low" else risk_level
        if consecutive_days is not None:
            if is_master and consecutive_days >= thresholds["consecutive_days_critical"]:
                factors.append(
                    f"Consecutive training: {consecutive_days} days "
                    f"(>={thresholds['consecutive_days_critical']:.0f}"
                    f" = neuromuscular overload)"
                )
                risk_level = "high"
            elif consecutive_days >= thresholds["consecutive_days_warning"]:
                factors.append(
                    f"Consecutive training: {consecutive_days} days "
                    f"(>={thresholds['consecutive_days_warning']:.0f}"
                    f" = fatigue accumulation)"
                )
                risk_level = "medium" if risk_level == "low" else risk_level
        if (
            consecutive_days is not None
            and sleep_hours is not None
            and is_master
            and consecutive_days >= thresholds["consecutive_days_warning"]
            and sleep_hours < 7.0
        ):
            factors.append(
                f"Combined: {consecutive_days} consecutive days "
                f"+ low sleep ({sleep_hours:.1f}h)"
            )
            risk_level = "high"

    # MEDIUM RISK CHECKS
    if risk_level == "low":
        if thresholds["tsb_fatigued"] <= tsb < thresholds["tsb_optimal_min"]:
            factors.append(f"TSB fatigued range ({tsb:.1f})")
            risk_level = "medium"
        if thresholds["ratio_optimal"] < atl_ctl_ratio <= thresholds["ratio_warning"]:
            factors.append(f"ATL/CTL ratio moderate ({atl_ctl_ratio:.2f})")
            risk_level = "medium" if risk_level == "low" else risk_level

    # Recommendations
    if veto:
        if is_master:
            recommendation = (
                "VETO: Immediate rest required. Cancel ALL training "
                "OR Z1 only (max 45min, <55% threshold)."
            )
        else:
            recommendation = "VETO: Rest day recommended or very light Z1 only (max 60min)."
    elif risk_level == "high":
        recommendation = (
            "Cancel all sessions >85% threshold. Z2 endurance only, "
            "max 60min. Monitor sleep closely."
        )
    elif risk_level == "medium":
        recommendation = "Reduce intensity -10% OR duration -15%. Prioritize recovery quality."
    else:
        recommendation = "Normal training. Follow planned sessions. Monitor recovery markers."

    return {
        "risk_level": risk_level,
        "veto": veto,
        "sleep_veto": sleep_veto,
        "recommendation": recommendation,
        "factors": factors,
        "atl_ctl_ratio": round(atl_ctl_ratio, 2),
        "is_master_athlete": is_master,
    }
