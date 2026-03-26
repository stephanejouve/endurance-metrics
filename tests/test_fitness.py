"""Tests for fitness metrics utilities."""

import pytest

from endurance_metrics.fitness import (
    calculate_metrics_change,
    calculate_tsb,
    extract_wellness_metrics,
    format_metrics_display,
    get_metrics_safely,
    is_metrics_complete,
)


class TestExtractWellnessMetrics:
    def test_extract_complete_wellness(self):
        wellness = {"ctl": 45.6, "atl": 37.7, "tsb": 7.9}
        result = extract_wellness_metrics(wellness)
        assert result["ctl"] == 45.6
        assert result["atl"] == 37.7
        assert result["tsb"] == 7.9

    def test_extract_none_wellness(self):
        result = extract_wellness_metrics(None)
        assert result["ctl"] == 0.0
        assert result["atl"] == 0.0
        assert result["tsb"] == 0.0

    def test_extract_with_none_values(self):
        wellness = {"ctl": None, "atl": 35.0, "tsb": None}
        result = extract_wellness_metrics(wellness)
        assert result["ctl"] == 0.0
        assert result["atl"] == 35.0
        assert result["tsb"] == -35.0

    def test_extract_without_tsb(self):
        wellness = {"ctl": 45.6, "atl": 37.7}
        result = extract_wellness_metrics(wellness)
        assert result["ctl"] == 45.6
        assert result["atl"] == 37.7
        assert result["tsb"] == pytest.approx(7.9, abs=0.1)

    def test_extract_empty_dict(self):
        result = extract_wellness_metrics({})
        assert result["ctl"] == 0.0
        assert result["atl"] == 0.0
        assert result["tsb"] == 0.0


class TestCalculateTSB:
    def test_calculate_positive_tsb(self):
        assert calculate_tsb(45.6, 37.7) == pytest.approx(7.9, abs=0.1)

    def test_calculate_negative_tsb(self):
        assert calculate_tsb(40.0, 50.0) == -10.0

    def test_calculate_zero_tsb(self):
        assert calculate_tsb(45.0, 45.0) == 0.0


class TestFormatMetricsDisplay:
    def test_format_positive_tsb(self):
        metrics = {"ctl": 45.6, "atl": 37.7, "tsb": 7.9}
        assert format_metrics_display(metrics) == "CTL: 45.6 | ATL: 37.7 | TSB: +7.9"

    def test_format_negative_tsb(self):
        metrics = {"ctl": 40.0, "atl": 50.0, "tsb": -10.0}
        assert format_metrics_display(metrics) == "CTL: 40.0 | ATL: 50.0 | TSB: -10.0"

    def test_format_zero_tsb(self):
        metrics = {"ctl": 45.0, "atl": 45.0, "tsb": 0.0}
        assert format_metrics_display(metrics) == "CTL: 45.0 | ATL: 45.0 | TSB: +0.0"

    def test_format_missing_values(self):
        assert format_metrics_display({}) == "CTL: 0.0 | ATL: 0.0 | TSB: +0.0"


class TestIsMetricsComplete:
    def test_complete_metrics(self):
        assert is_metrics_complete({"ctl": 45.6, "atl": 37.7, "tsb": 7.9}) is True

    def test_zero_values_are_complete(self):
        assert is_metrics_complete({"ctl": 0, "atl": 0, "tsb": 0}) is True

    def test_none_value(self):
        assert is_metrics_complete({"ctl": None, "atl": 37.7, "tsb": 7.9}) is False

    def test_missing_key(self):
        assert is_metrics_complete({"ctl": 45.6, "atl": 37.7}) is False

    def test_empty_dict(self):
        assert is_metrics_complete({}) is False

    def test_none_dict(self):
        assert is_metrics_complete(None) is False

    def test_invalid_type(self):
        assert is_metrics_complete({"ctl": "invalid", "atl": 37.7, "tsb": 7.9}) is False


class TestCalculateMetricsChange:
    def test_calculate_positive_change(self):
        start = {"ctl": 40.0, "atl": 35.0, "tsb": 5.0}
        end = {"ctl": 45.6, "atl": 37.7, "tsb": 7.9}
        result = calculate_metrics_change(start, end)
        assert result["ctl_change"] == pytest.approx(5.6, abs=0.1)
        assert result["atl_change"] == pytest.approx(2.7, abs=0.1)
        assert result["tsb_change"] == pytest.approx(2.9, abs=0.1)

    def test_calculate_negative_change(self):
        start = {"ctl": 50.0, "atl": 40.0, "tsb": 10.0}
        end = {"ctl": 45.0, "atl": 37.0, "tsb": 8.0}
        result = calculate_metrics_change(start, end)
        assert result["ctl_change"] == -5.0
        assert result["atl_change"] == -3.0
        assert result["tsb_change"] == -2.0

    def test_calculate_with_none_values(self):
        start = {"ctl": None, "atl": 35.0, "tsb": None}
        end = {"ctl": 45.6, "atl": 37.7, "tsb": 7.9}
        result = calculate_metrics_change(start, end)
        assert result["ctl_change"] is None
        assert result["atl_change"] == pytest.approx(2.7, abs=0.1)
        assert result["tsb_change"] is None

    def test_calculate_no_change(self):
        same = {"ctl": 45.0, "atl": 37.0, "tsb": 8.0}
        result = calculate_metrics_change(same, same)
        assert result["ctl_change"] == 0.0
        assert result["atl_change"] == 0.0
        assert result["tsb_change"] == 0.0


class TestGetMetricsSafely:
    def test_get_from_valid_list(self):
        wellness_list = [{"ctl": 45.6, "atl": 37.7}]
        result = get_metrics_safely(wellness_list, index=0)
        assert result["ctl"] == 45.6
        assert result["atl"] == 37.7
        assert result["tsb"] == pytest.approx(7.9, abs=0.1)

    def test_get_from_none_list(self):
        result = get_metrics_safely(None)
        assert result == {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}

    def test_get_from_empty_list(self):
        result = get_metrics_safely([])
        assert result == {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}

    def test_get_out_of_bounds_index(self):
        result = get_metrics_safely([{"ctl": 45.6, "atl": 37.7}], index=5)
        assert result == {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}

    def test_get_negative_index(self):
        result = get_metrics_safely([{"ctl": 45.6, "atl": 37.7}], index=-1)
        assert result == {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}
