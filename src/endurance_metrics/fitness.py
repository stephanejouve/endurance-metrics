"""Fitness metrics utilities.

Centralized utilities for CTL/ATL/TSB metrics extraction, calculation,
and formatting.

Examples:
    Extract wellness metrics safely::

        metrics = get_metrics_safely(wellness_list, index=0)
        print(f"CTL: {metrics['ctl']}, ATL: {metrics['atl']}, TSB: {metrics['tsb']}")

    Format metrics for display::

        display = format_metrics_display(metrics)
        print(display)  # "CTL: 45.6 | ATL: 37.7 | TSB: +7.9"
"""

from typing import Any


def extract_wellness_metrics(wellness_data: dict[str, Any] | None) -> dict[str, float]:
    """Extract CTL/ATL/TSB metrics from wellness data with proper None handling.

    Args:
        wellness_data: Wellness dictionary from fitness data (or None)

    Returns:
        Dict with 'ctl', 'atl', 'tsb' keys (float values, 0.0 if missing)

    Examples:
        >>> wellness = {'ctl': 45.6, 'atl': 37.7, 'tsb': 7.9}
        >>> extract_wellness_metrics(wellness)
        {'ctl': 45.6, 'atl': 37.7, 'tsb': 7.9}

        >>> extract_wellness_metrics(None)
        {'ctl': 0.0, 'atl': 0.0, 'tsb': 0.0}
    """
    if not wellness_data:
        return {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}

    ctl = wellness_data.get("ctl")
    atl = wellness_data.get("atl")
    tsb = wellness_data.get("tsb")

    ctl = ctl if ctl is not None else 0.0
    atl = atl if atl is not None else 0.0

    if tsb is None:
        tsb = ctl - atl
    else:
        tsb = float(tsb)

    return {
        "ctl": float(ctl),
        "atl": float(atl),
        "tsb": float(tsb),
    }


def calculate_tsb(ctl: float, atl: float) -> float:
    """Calculate Training Stress Balance from CTL and ATL.

    TSB = CTL - ATL

    Args:
        ctl: Chronic Training Load (fitness)
        atl: Acute Training Load (fatigue)

    Returns:
        Training Stress Balance (form)

    Examples:
        >>> calculate_tsb(45.6, 37.7)
        7.9
        >>> calculate_tsb(40.0, 50.0)
        -10.0
    """
    return ctl - atl


def format_metrics_display(metrics: dict[str, float]) -> str:
    """Format CTL/ATL/TSB metrics for display.

    Formats metrics as: "CTL: 45.6 | ATL: 37.7 | TSB: +7.9"
    TSB includes + sign for positive values.

    Args:
        metrics: Dictionary with 'ctl', 'atl', 'tsb' keys

    Returns:
        Formatted metrics string

    Examples:
        >>> metrics = {'ctl': 45.6, 'atl': 37.7, 'tsb': 7.9}
        >>> format_metrics_display(metrics)
        'CTL: 45.6 | ATL: 37.7 | TSB: +7.9'
    """
    ctl = metrics.get("ctl", 0)
    atl = metrics.get("atl", 0)
    tsb = metrics.get("tsb", 0)
    tsb_sign = "+" if tsb >= 0 else ""
    return f"CTL: {ctl:.1f} | ATL: {atl:.1f} | TSB: {tsb_sign}{tsb:.1f}"


def is_metrics_complete(metrics: dict[str, Any]) -> bool:
    """Check if all CTL/ATL/TSB metrics are present and valid.

    Args:
        metrics: Dictionary potentially containing 'ctl', 'atl', 'tsb'

    Returns:
        True if all metrics are valid

    Examples:
        >>> is_metrics_complete({'ctl': 45.6, 'atl': 37.7, 'tsb': 7.9})
        True
        >>> is_metrics_complete({'ctl': None, 'atl': 37.7})
        False
    """
    if not metrics:
        return False
    required_keys = ["ctl", "atl", "tsb"]
    for key in required_keys:
        value = metrics.get(key)
        if value is None:
            return False
        try:
            float(value)
        except (TypeError, ValueError):
            return False
    return True


def calculate_metrics_change(
    metrics_start: dict[str, float], metrics_end: dict[str, float]
) -> dict[str, float | None]:
    """Calculate change in metrics between two timepoints.

    Args:
        metrics_start: Metrics at start of period
        metrics_end: Metrics at end of period

    Returns:
        Dict with 'ctl_change', 'atl_change', 'tsb_change' keys

    Examples:
        >>> start = {'ctl': 40.0, 'atl': 35.0, 'tsb': 5.0}
        >>> end = {'ctl': 45.6, 'atl': 37.7, 'tsb': 7.9}
        >>> calculate_metrics_change(start, end)
        {'ctl_change': 5.6, 'atl_change': 2.7, 'tsb_change': 2.9}
    """
    ctl_start = metrics_start.get("ctl")
    ctl_end = metrics_end.get("ctl")
    ctl_change = (ctl_end - ctl_start) if (ctl_start is not None and ctl_end is not None) else None

    atl_start = metrics_start.get("atl")
    atl_end = metrics_end.get("atl")
    atl_change = (atl_end - atl_start) if (atl_start is not None and atl_end is not None) else None

    tsb_start = metrics_start.get("tsb")
    tsb_end = metrics_end.get("tsb")
    tsb_change = (tsb_end - tsb_start) if (tsb_start is not None and tsb_end is not None) else None

    return {
        "ctl_change": ctl_change,
        "atl_change": atl_change,
        "tsb_change": tsb_change,
    }


def get_metrics_safely(
    wellness_list: list[dict[str, Any]] | None, index: int = 0
) -> dict[str, float]:
    """Safely extract metrics from wellness list with fallback.

    Args:
        wellness_list: List of wellness data (or None)
        index: Index to extract (default: 0 for most recent)

    Returns:
        Dict with 'ctl', 'atl', 'tsb' keys (0.0 if unavailable)

    Examples:
        >>> wellness_list = [{'ctl': 45.6, 'atl': 37.7}]
        >>> get_metrics_safely(wellness_list, index=0)
        {'ctl': 45.6, 'atl': 37.7, 'tsb': 7.9}
    """
    if not wellness_list:
        return {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}
    if index < 0 or index >= len(wellness_list):
        return {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}
    wellness_data = wellness_list[index]
    return extract_wellness_metrics(wellness_data)
