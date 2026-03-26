"""Tests for advanced metrics utilities."""

import pytest

from endurance_metrics.advanced import (
    calculate_ramp_rate,
    detect_overtraining_risk,
    detect_training_peaks,
    format_metrics_comparison,
    get_recovery_recommendation,
    get_weekly_metrics_trend,
)


def test_calculate_ramp_rate_weekly_increase():
    assert calculate_ramp_rate(65.0, 60.0, days=7) == 5.0


def test_calculate_ramp_rate_biweekly():
    assert calculate_ramp_rate(65.0, 60.0, days=14) == 2.5


def test_calculate_ramp_rate_declining():
    assert calculate_ramp_rate(60.0, 65.0, days=7) == -5.0


def test_calculate_ramp_rate_zero_days_raises():
    with pytest.raises(ValueError, match="days must be positive"):
        calculate_ramp_rate(65.0, 60.0, days=0)


def test_calculate_ramp_rate_negative_days_raises():
    with pytest.raises(ValueError, match="days must be positive"):
        calculate_ramp_rate(65.0, 60.0, days=-7)


def test_weekly_trend_rising():
    data = [{"ctl": 60.0}, {"ctl": 62.0}, {"ctl": 65.0}, {"ctl": 67.0}]
    result = get_weekly_metrics_trend(data, "ctl")
    assert result["trend"] == "rising"
    assert result["slope"] > 1.0
    assert result["weeks_analyzed"] == 4


def test_weekly_trend_declining():
    data = [{"ctl": 67.0}, {"ctl": 65.0}, {"ctl": 62.0}, {"ctl": 59.0}]
    result = get_weekly_metrics_trend(data, "ctl")
    assert result["trend"] == "declining"
    assert result["slope"] < -1.0


def test_weekly_trend_stable():
    data = [{"ctl": 60.0}, {"ctl": 60.5}, {"ctl": 59.5}, {"ctl": 60.0}]
    result = get_weekly_metrics_trend(data, "ctl")
    assert result["trend"] == "stable"
    assert -1.0 <= result["slope"] <= 1.0


def test_weekly_trend_empty_data():
    result = get_weekly_metrics_trend([], "ctl")
    assert result["trend"] == "unknown"
    assert result["weeks_analyzed"] == 0


def test_weekly_trend_insufficient_data():
    result = get_weekly_metrics_trend([{"ctl": 60.0}], "ctl")
    assert result["trend"] == "insufficient_data"


def test_detect_peaks_single_peak():
    history = [50, 52, 51, 58, 60, 55, 53]
    peaks = detect_training_peaks(history, threshold_percent=10.0)
    assert len(peaks) >= 1
    assert any(p["value"] >= 58 for p in peaks)


def test_detect_peaks_no_peaks():
    history = [50, 51, 52, 53, 54, 55]
    peaks = detect_training_peaks(history, threshold_percent=10.0)
    assert len(peaks) == 0


def test_detect_peaks_multiple_peaks():
    history = [50, 52, 58, 55, 52, 62, 60, 55]
    peaks = detect_training_peaks(history, threshold_percent=10.0)
    assert len(peaks) >= 1
    assert peaks[0]["index"] == 5
    assert peaks[0]["value"] == 62


def test_detect_peaks_insufficient_history():
    peaks = detect_training_peaks([50, 52, 51], threshold_percent=10.0)
    assert len(peaks) == 0


def test_recovery_recommendation_critical():
    result = get_recovery_recommendation(
        tsb=-22.0, atl_ctl_ratio=1.7, profile={"age": 54, "category": "master"}
    )
    assert result["priority"] == "critical"
    assert result["intensity_limit"] <= 60
    assert result["rest_days"] >= 2


def test_recovery_recommendation_high():
    result = get_recovery_recommendation(
        tsb=-18.0, atl_ctl_ratio=1.45, profile={"age": 54, "category": "master"}
    )
    assert result["priority"] == "high"
    assert result["intensity_limit"] <= 75
    assert "Z2" in result["recommendation"]


def test_recovery_recommendation_medium():
    result = get_recovery_recommendation(
        tsb=-12.0, atl_ctl_ratio=1.25, profile={"age": 35, "category": "senior"}
    )
    assert result["priority"] == "medium"
    assert result["intensity_limit"] <= 90


def test_recovery_recommendation_low():
    result = get_recovery_recommendation(
        tsb=5.0, atl_ctl_ratio=1.0, profile={"age": 35, "category": "senior"}
    )
    assert result["priority"] == "low"
    assert result["intensity_limit"] == 100
    assert "Normal" in result["recommendation"]


def test_recovery_recommendation_master_adjustments():
    result_master = get_recovery_recommendation(
        tsb=-18.0, atl_ctl_ratio=1.45, profile={"age": 54, "category": "master"}
    )
    result_senior = get_recovery_recommendation(
        tsb=-18.0, atl_ctl_ratio=1.45, profile={"age": 35, "category": "senior"}
    )
    assert result_master["rest_days"] >= result_senior["rest_days"]
    assert result_master["duration_limit"] <= result_senior["duration_limit"]


def test_format_comparison_basic():
    p1 = {"ctl": 60.0, "atl": 55.0, "tsb": 5.0}
    p2 = {"ctl": 65.0, "atl": 58.0, "tsb": 7.0}
    result = format_metrics_comparison(p1, p2)
    assert "CTL" in result
    assert "ATL" in result
    assert "TSB" in result
    assert "UP" in result


def test_format_comparison_with_labels():
    p1 = {"ctl": 60.0}
    p2 = {"ctl": 65.0}
    labels = {"period1": "Last Week", "period2": "This Week"}
    result = format_metrics_comparison(p1, p2, labels=labels)
    assert "Last Week" in result
    assert "This Week" in result


def test_format_comparison_declining():
    p1 = {"ctl": 65.0, "atl": 60.0}
    p2 = {"ctl": 60.0, "atl": 55.0}
    result = format_metrics_comparison(p1, p2)
    assert "DOWN" in result


def test_format_comparison_stable():
    p1 = {"ctl": 60.0, "atl": 55.0}
    p2 = {"ctl": 60.2, "atl": 55.1}
    result = format_metrics_comparison(p1, p2)
    assert "->" in result


def test_overtraining_risk_critical_tsb():
    result = detect_overtraining_risk(
        ctl=65.0, atl=95.0, tsb=-30.0, profile={"age": 54, "category": "master"}
    )
    assert result["risk_level"] == "critical"
    assert result["veto"] is True
    assert "VETO" in result["recommendation"]


def test_overtraining_risk_critical_ratio():
    result = detect_overtraining_risk(
        ctl=60.0, atl=115.0, tsb=-10.0, profile={"age": 54, "category": "master"}
    )
    assert result["risk_level"] == "critical"
    assert result["veto"] is True


def test_overtraining_risk_sleep_veto():
    result = detect_overtraining_risk(
        ctl=65.0,
        atl=70.0,
        tsb=0.0,
        sleep_hours=5.0,
        profile={"age": 54, "category": "master", "sleep_dependent": True},
    )
    assert result["sleep_veto"] is True
    assert result["veto"] is True


def test_overtraining_risk_high():
    result = detect_overtraining_risk(
        ctl=65.0, atl=100.0, tsb=-22.0, sleep_hours=7.0, profile={"age": 54, "category": "master"}
    )
    assert result["risk_level"] == "high"
    assert "85% threshold" in result["recommendation"]


def test_overtraining_risk_low():
    result = detect_overtraining_risk(
        ctl=65.0, atl=60.0, tsb=5.0, sleep_hours=7.5, profile={"age": 54, "category": "master"}
    )
    assert result["risk_level"] == "low"
    assert result["veto"] is False


def test_overtraining_risk_master_vs_senior():
    result_master = detect_overtraining_risk(
        ctl=65.0, atl=95.0, tsb=-27.0, profile={"age": 54, "category": "master"}
    )
    result_senior = detect_overtraining_risk(
        ctl=65.0, atl=95.0, tsb=-27.0, profile={"age": 35, "category": "senior"}
    )
    assert result_master["veto"] is True
    assert result_senior["veto"] is True
    assert "45min" in result_master["recommendation"]
    assert "60min" in result_senior["recommendation"]


def test_overtraining_risk_custom_thresholds():
    custom = {
        "tsb_critical": -20.0,
        "ratio_critical": 1.6,
        "sleep_critical": 6.5,
        "sleep_veto": 6.0,
        "tsb_fatigued": -12.0,
        "tsb_optimal_min": -5.0,
        "ratio_warning": 1.4,
        "ratio_optimal": 1.2,
    }
    result = detect_overtraining_risk(ctl=65.0, atl=90.0, tsb=-21.0, thresholds=custom)
    assert result["risk_level"] == "critical"
    assert result["veto"] is True


class TestDetectOvertrainingRiskConsecutiveDays:
    def test_consecutive_days_warning_factor(self):
        result = detect_overtraining_risk(
            ctl=43,
            atl=46,
            tsb=-3,
            consecutive_days=3,
            profile={"age": 30, "category": "senior"},
        )
        assert any("Consecutive training: 3 days" in f for f in result["factors"])
        assert result["risk_level"] in ("medium", "high")

    def test_consecutive_days_critical_master(self):
        result = detect_overtraining_risk(
            ctl=43,
            atl=46,
            tsb=-3,
            consecutive_days=4,
            profile={"age": 54, "category": "master"},
        )
        assert any("neuromuscular overload" in f for f in result["factors"])
        assert result["risk_level"] == "high"

    def test_consecutive_days_combined_with_sleep(self):
        result = detect_overtraining_risk(
            ctl=43,
            atl=46,
            tsb=-3,
            sleep_hours=6.5,
            consecutive_days=3,
            profile={"age": 54, "category": "master", "sleep_dependent": True},
        )
        assert result["risk_level"] == "high"
        assert any("Combined" in f for f in result["factors"])

    def test_no_consecutive_days_no_factor(self):
        result = detect_overtraining_risk(
            ctl=43,
            atl=46,
            tsb=-3,
            profile={"age": 54, "category": "master"},
        )
        assert not any("Consecutive" in f for f in result["factors"])

    def test_two_consecutive_days_no_warning(self):
        result = detect_overtraining_risk(
            ctl=43,
            atl=46,
            tsb=-3,
            consecutive_days=2,
            profile={"age": 54, "category": "master"},
        )
        assert not any("Consecutive" in f for f in result["factors"])
