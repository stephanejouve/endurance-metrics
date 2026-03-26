"""Cardiovascular decoupling calculation with effort type abstraction.

Supports multiple effort normalization strategies:
- "power": Normalized Power (rolling 30s, 4th power) - cycling
- "pace": Rolling average 30s - running, swimming
- "raw": Simple average - pre-normalized data

References:
    - Friel (2009) - Effort:HR decoupling: <5% aerobic fitness validated
    - Coggan - Normalized Power (30s rolling average, 4th power)
"""

from __future__ import annotations


def _normalize_effort(data: list[float], effort_type: str = "power") -> float | None:
    """Normalize effort data according to the specified type.

    Args:
        data: Per-second effort data.
        effort_type: Normalization strategy:
            - "power": Normalized Power (rolling 30s, 4th power) - cycling
            - "pace": Rolling average 30s - running, swimming
            - "raw": Simple average - pre-normalized data

    Returns:
        Normalized effort value, or None if insufficient data.

    Raises:
        ValueError: If effort_type is not recognized.
    """
    if effort_type == "power":
        return _calc_np(data)
    elif effort_type == "pace":
        return _calc_rolling_avg(data)
    elif effort_type == "raw":
        if not data:
            return None
        non_zero = [v for v in data if v > 0]
        return sum(non_zero) / len(non_zero) if non_zero else None
    else:
        raise ValueError(
            f"Unknown effort_type: '{effort_type}'. " f"Valid types: 'power', 'pace', 'raw'"
        )


def _calc_np(watts: list[float]) -> float | None:
    """Compute Normalized Power from a watts stream.

    Uses 30-second rolling average raised to the 4th power.

    Args:
        watts: Per-second power data.

    Returns:
        Normalized power value, or None if insufficient data (<30 points).
    """
    if len(watts) < 30:
        return None
    rolling_avgs = []
    for i in range(len(watts) - 29):
        window = watts[i : i + 30]
        rolling_avgs.append(sum(window) / 30)
    if not rolling_avgs:
        return None
    fourth_powers = [p**4 for p in rolling_avgs]
    avg_fourth = sum(fourth_powers) / len(fourth_powers)
    return avg_fourth ** (1 / 4)


def _calc_rolling_avg(data: list[float], window: int = 30) -> float | None:
    """Compute rolling average normalization (e.g., for pace data).

    Args:
        data: Per-second effort data.
        window: Rolling window size in seconds (default: 30).

    Returns:
        Average of rolling averages, or None if insufficient data.
    """
    if len(data) < window:
        return None
    rolling_avgs = []
    for i in range(len(data) - window + 1):
        w = data[i : i + window]
        rolling_avgs.append(sum(w) / window)
    if not rolling_avgs:
        return None
    return sum(rolling_avgs) / len(rolling_avgs)


def compute_normalized_power(watts: list[float]) -> float | None:
    """Convenience alias: compute Normalized Power from a watts stream.

    Args:
        watts: Per-second power data.

    Returns:
        Normalized power value, or None if insufficient data.
    """
    return _calc_np(watts)


def calculate_decoupling(
    effort_data: list[float],
    cardio_data: list[float],
    max_seconds: int | None = None,
    *,
    effort_type: str = "power",
) -> float | None:
    """Calculate effort:cardio cardiovascular decoupling over a window.

    Splits the data into two halves and compares the effort:HR ratio
    between the first and second half.

    Args:
        effort_data: Per-second effort data (watts, pace, etc.).
        cardio_data: Per-second heart rate data.
        max_seconds: If provided, truncate streams to this length.
        effort_type: Normalization type ("power", "pace", "raw").

    Returns:
        Decoupling percentage (positive = cardiac drift), or None if
        insufficient data (< 60 points or no valid HR).
    """
    if not effort_data or not cardio_data:
        return None

    if max_seconds is not None and max_seconds > 0:
        effort_data = effort_data[:max_seconds]
        cardio_data = cardio_data[:max_seconds]

    min_len = min(len(effort_data), len(cardio_data))
    if min_len < 60:
        return None

    effort_data = effort_data[:min_len]
    cardio_data = cardio_data[:min_len]

    midpoint = min_len // 2

    effort_half1 = effort_data[:midpoint]
    cardio_half1 = cardio_data[:midpoint]
    effort_half2 = effort_data[midpoint:]
    cardio_half2 = cardio_data[midpoint:]

    norm_half1 = _normalize_effort(effort_half1, effort_type)
    norm_half2 = _normalize_effort(effort_half2, effort_type)

    if not norm_half1 or not norm_half2:
        return None

    hr_half1_valid = [hr for hr in cardio_half1 if hr > 0]
    hr_half2_valid = [hr for hr in cardio_half2 if hr > 0]

    if not hr_half1_valid or not hr_half2_valid:
        return None

    avg_hr_half1 = sum(hr_half1_valid) / len(hr_half1_valid)
    avg_hr_half2 = sum(hr_half2_valid) / len(hr_half2_valid)

    if avg_hr_half1 <= 0:
        return None

    ratio_half1 = norm_half1 / avg_hr_half1
    ratio_half2 = norm_half2 / avg_hr_half2

    return round(((ratio_half2 - ratio_half1) / ratio_half1) * 100, 1)


def analyze_overtime(
    effort_data: list[float],
    cardio_data: list[float],
    prescribed_seconds: int,
    *,
    effort_type: str = "power",
    threshold: float | None = None,
) -> dict | None:
    """Analyze the extension beyond prescribed duration.

    Args:
        effort_data: Full per-second effort data.
        cardio_data: Full per-second heart rate data.
        prescribed_seconds: Prescribed session duration in seconds.
        effort_type: Normalization type ("power", "pace", "raw").
        threshold: Athlete's threshold value for TSS estimation
            (e.g., FTP for cycling). If None, defaults to 200.

    Returns:
        Dict with overtime metrics, or None if no significant extension (<30s):
        - duration_extra_min: Extension duration in minutes
        - avg_effort: Average effort during extension (non-zero only)
        - avg_hr_bpm: Average heart rate during extension (non-zero only)
        - estimated_tss: Rough TSS estimate for the extension
    """
    if not effort_data or not cardio_data:
        return None

    min_len = min(len(effort_data), len(cardio_data))
    if min_len <= prescribed_seconds:
        return None

    extra_seconds = min_len - prescribed_seconds
    if extra_seconds < 30:
        return None

    effort_extra = effort_data[prescribed_seconds:min_len]
    cardio_extra = cardio_data[prescribed_seconds:min_len]

    non_zero_effort = [e for e in effort_extra if e > 0]
    avg_effort = round(sum(non_zero_effort) / len(non_zero_effort), 1) if non_zero_effort else 0.0

    non_zero_hr = [hr for hr in cardio_extra if hr > 0]
    avg_hr = round(sum(non_zero_hr) / len(non_zero_hr), 1) if non_zero_hr else 0.0

    np_extra = _normalize_effort(effort_extra, effort_type)
    threshold_value = threshold if threshold is not None else 200
    estimated_tss = 0.0
    if np_extra and np_extra > 0 and threshold_value > 0:
        intensity_factor = np_extra / threshold_value
        estimated_tss = round((extra_seconds * intensity_factor**2) / 36, 1)

    return {
        "duration_extra_min": round(extra_seconds / 60, 1),
        "avg_effort": avg_effort,
        "avg_hr_bpm": avg_hr,
        "estimated_tss": estimated_tss,
    }
