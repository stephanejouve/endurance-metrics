"""Tests for cardiovascular decoupling calculation utilities."""

import pytest

from endurance_metrics.decoupling import (
    analyze_overtime,
    calculate_decoupling,
    compute_normalized_power,
)


class TestCalculateDecoupling:

    def test_flat_streams_near_zero(self):
        watts = [200.0] * 600
        hr = [140.0] * 600
        result = calculate_decoupling(watts, hr)
        assert result is not None
        assert result == pytest.approx(0.0, abs=0.1)

    def test_hr_drift_negative_decoupling(self):
        n = 600
        watts = [200.0] * n
        hr = [130.0 + (20.0 * i / n) for i in range(n)]
        result = calculate_decoupling(watts, hr)
        assert result is not None
        assert result < 0

    def test_power_drop_negative_decoupling(self):
        n = 600
        watts = [220.0 - (40.0 * i / n) for i in range(n)]
        hr = [140.0] * n
        result = calculate_decoupling(watts, hr)
        assert result is not None
        assert result < 0

    def test_with_max_seconds_truncates(self):
        watts = [200.0] * 600 + [100.0] * 600
        hr = [140.0] * 600 + [160.0] * 600
        full_result = calculate_decoupling(watts, hr)
        windowed_result = calculate_decoupling(watts, hr, max_seconds=600)
        assert full_result is not None
        assert windowed_result is not None
        assert abs(windowed_result) < abs(full_result)

    def test_none_when_insufficient_data(self):
        assert calculate_decoupling([200.0] * 50, [140.0] * 50) is None

    def test_none_when_no_hr(self):
        assert calculate_decoupling([200.0] * 200, [0.0] * 200) is None

    def test_none_when_empty_lists(self):
        assert calculate_decoupling([], []) is None

    def test_different_length_streams_aligned(self):
        result = calculate_decoupling([200.0] * 800, [140.0] * 600)
        assert result is not None
        assert result == pytest.approx(0.0, abs=0.1)

    def test_effort_type_pace(self):
        """Pace-based normalization (rolling average)."""
        n = 600
        pace = [300.0] * n  # 5:00/km constant
        hr = [140.0] * n
        result = calculate_decoupling(pace, hr, effort_type="pace")
        assert result is not None
        assert result == pytest.approx(0.0, abs=0.1)

    def test_effort_type_raw(self):
        """Raw effort (simple average)."""
        n = 600
        effort = [100.0] * n
        hr = [140.0] * n
        result = calculate_decoupling(effort, hr, effort_type="raw")
        assert result is not None
        assert result == pytest.approx(0.0, abs=0.1)

    def test_effort_type_invalid_raises(self):
        """Invalid effort_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown effort_type"):
            calculate_decoupling([200.0] * 100, [140.0] * 100, effort_type="invalid")

    def test_default_effort_type_is_power(self):
        """Default effort_type is 'power' (NP calculation)."""
        watts = [200.0] * 600
        hr = [140.0] * 600
        result_default = calculate_decoupling(watts, hr)
        result_power = calculate_decoupling(watts, hr, effort_type="power")
        assert result_default == result_power


class TestAnalyzeOvertime:

    def test_returns_metrics_for_extension(self):
        prescribed = 600
        total = 900
        watts = [200.0] * prescribed + [100.0] * (total - prescribed)
        hr = [140.0] * prescribed + [120.0] * (total - prescribed)
        result = analyze_overtime(watts, hr, prescribed, threshold=200)
        assert result is not None
        assert result["duration_extra_min"] == pytest.approx(5.0, abs=0.1)
        assert result["avg_effort"] == pytest.approx(100.0, abs=1.0)
        assert result["avg_hr_bpm"] == pytest.approx(120.0, abs=1.0)
        assert "estimated_tss" in result

    def test_none_when_no_extension(self):
        assert analyze_overtime([200.0] * 500, [140.0] * 500, prescribed_seconds=600) is None

    def test_none_when_extension_under_30s(self):
        prescribed = 600
        assert (
            analyze_overtime([200.0] * (prescribed + 20), [140.0] * (prescribed + 20), prescribed)
            is None
        )

    def test_none_when_exactly_prescribed(self):
        assert analyze_overtime([200.0] * 600, [140.0] * 600, 600) is None

    def test_none_when_empty_data(self):
        assert analyze_overtime([], [], 600) is None

    def test_extension_with_zero_effort(self):
        prescribed = 600
        watts = [200.0] * prescribed + [0.0] * 120
        hr = [140.0] * prescribed + [110.0] * 120
        result = analyze_overtime(watts, hr, prescribed, threshold=200)
        assert result is not None
        assert result["avg_effort"] == 0.0
        assert result["avg_hr_bpm"] == pytest.approx(110.0, abs=1.0)

    def test_estimated_tss_reasonable(self):
        prescribed = 3600
        extra = 900
        watts = [200.0] * prescribed + [200.0] * extra
        hr = [140.0] * prescribed + [145.0] * extra
        result = analyze_overtime(watts, hr, prescribed, threshold=200)
        assert result is not None
        assert result["estimated_tss"] > 0
        assert result["estimated_tss"] == pytest.approx(25.0, abs=5.0)

    def test_default_threshold(self):
        """Without explicit threshold, default 200 is used."""
        prescribed = 3600
        extra = 900
        watts = [200.0] * prescribed + [200.0] * extra
        hr = [140.0] * prescribed + [145.0] * extra
        result_default = analyze_overtime(watts, hr, prescribed)
        result_explicit = analyze_overtime(watts, hr, prescribed, threshold=200)
        assert result_default["estimated_tss"] == result_explicit["estimated_tss"]

    def test_custom_threshold(self):
        """Custom threshold changes TSS estimate."""
        prescribed = 3600
        extra = 900
        watts = [200.0] * prescribed + [200.0] * extra
        hr = [140.0] * prescribed + [145.0] * extra
        result_200 = analyze_overtime(watts, hr, prescribed, threshold=200)
        result_300 = analyze_overtime(watts, hr, prescribed, threshold=300)
        # Higher threshold → lower IF → lower TSS
        assert result_200["estimated_tss"] > result_300["estimated_tss"]

    def test_pace_effort_type(self):
        """Overtime analysis with pace effort type."""
        prescribed = 600
        total = 900
        pace = [300.0] * total  # 5:00/km constant
        hr = [140.0] * total
        result = analyze_overtime(pace, hr, prescribed, effort_type="pace", threshold=300)
        assert result is not None
        assert result["duration_extra_min"] == pytest.approx(5.0, abs=0.1)


class TestComputeNormalizedPower:

    def test_constant_power(self):
        watts = [200.0] * 600
        np_val = compute_normalized_power(watts)
        assert np_val is not None
        assert np_val == pytest.approx(200.0, abs=0.1)

    def test_insufficient_data(self):
        assert compute_normalized_power([200.0] * 20) is None

    def test_empty_data(self):
        assert compute_normalized_power([]) is None
