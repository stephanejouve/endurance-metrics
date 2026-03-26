"""Training metrics for endurance sports.

Provides CTL/ATL/TSB fitness metrics, ACWR/Monotony/Strain workload metrics,
cardiovascular decoupling analysis, and advanced training analysis.
"""

from .advanced import (
    calculate_ramp_rate,
    detect_overtraining_risk,
    detect_training_peaks,
    format_metrics_comparison,
    get_recovery_recommendation,
    get_weekly_metrics_trend,
)
from .decoupling import (
    analyze_overtime,
    calculate_decoupling,
    compute_normalized_power,
)
from .fitness import (
    calculate_metrics_change,
    calculate_tsb,
    extract_wellness_metrics,
    format_metrics_display,
    get_metrics_safely,
    is_metrics_complete,
)
from .workload import compute_training_load, count_consecutive_training_days

__all__ = [
    # fitness
    "extract_wellness_metrics",
    "calculate_tsb",
    "format_metrics_display",
    "is_metrics_complete",
    "calculate_metrics_change",
    "get_metrics_safely",
    # advanced
    "calculate_ramp_rate",
    "get_weekly_metrics_trend",
    "detect_training_peaks",
    "get_recovery_recommendation",
    "format_metrics_comparison",
    "detect_overtraining_risk",
    # workload
    "compute_training_load",
    "count_consecutive_training_days",
    # decoupling
    "calculate_decoupling",
    "analyze_overtime",
    "compute_normalized_power",
]

__version__ = "0.1.0"
