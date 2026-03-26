"""Tests for training load metrics (ACWR, Monotony, Strain)."""

from datetime import datetime, timedelta

import pytest

from endurance_metrics.workload import (
    compute_training_load,
    count_consecutive_training_days,
)


def _make_activities(daily_loads: list[float], days_back: int = 28) -> list[dict]:
    """Create synthetic activities from daily load values."""
    today = datetime.now().date()
    activities = []
    for i, load_val in enumerate(daily_loads):
        if load_val > 0:
            d = today - timedelta(days=days_back - 1 - i)
            activities.append(
                {
                    "date": d.isoformat() + "T08:00:00",
                    "load": load_val,
                }
            )
    return activities


class TestComputeTrainingLoad:

    def test_empty_activities_returns_empty(self):
        assert compute_training_load([]) == {}

    def test_uniform_load_acwr_one(self):
        daily = [50.0] * 28
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        assert result["acwr"] == 1.0

    def test_acute_spike_high_acwr(self):
        daily = [20.0] * 21 + [80.0] * 7
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        assert result["acwr"] > 1.5

    def test_detraining_low_acwr(self):
        daily = [80.0] * 21 + [10.0] * 7
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        assert result["acwr"] < 0.8

    def test_monotony_uniform_high(self):
        daily = [50.0] * 28
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        assert result["monotony"] == 0.0

    def test_monotony_varied_load(self):
        daily = [20.0] * 21 + [0, 40, 60, 0, 80, 30, 50]
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        assert result["monotony"] > 0

    def test_strain_calculation(self):
        daily = [20.0] * 21 + [0, 40, 60, 0, 80, 30, 50]
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        weekly_load = sum(daily[-7:])
        expected_strain = round(weekly_load * result["monotony"], 0)
        assert result["strain"] == expected_strain

    def test_result_keys(self):
        daily = [50.0] * 28
        activities = _make_activities(daily)
        result = compute_training_load(activities)
        expected_keys = {"acwr", "monotony", "strain", "acute_load", "chronic_load"}
        assert set(result.keys()) == expected_keys

    def test_rest_days_counted_as_zero(self):
        today = datetime.now().date()
        activities = [
            {"date": (today - timedelta(days=2)).isoformat() + "T08:00:00", "load": 100},
            {"date": (today - timedelta(days=5)).isoformat() + "T08:00:00", "load": 80},
            {"date": (today - timedelta(days=20)).isoformat() + "T08:00:00", "load": 60},
        ]
        result = compute_training_load(activities)
        assert result["chronic_load"] == pytest.approx((100 + 80 + 60) / 28, rel=0.01)

    def test_multiple_activities_same_day(self):
        today = datetime.now().date()
        date_str = (today - timedelta(days=1)).isoformat() + "T08:00:00"
        activities = [
            {"date": date_str, "load": 40},
            {"date": date_str, "load": 30},
        ]
        result = compute_training_load(activities)
        assert result
        assert result["acute_load"] == pytest.approx(70 / 7, rel=0.01)

    def test_missing_load_skipped(self):
        today = datetime.now().date()
        activities = [
            {"date": (today - timedelta(days=1)).isoformat() + "T08:00:00", "load": None},
            {"date": (today - timedelta(days=2)).isoformat() + "T08:00:00"},
        ]
        result = compute_training_load(activities)
        assert result["acute_load"] == 0.0

    def test_custom_field_names(self):
        """Test using custom field names for load and date."""
        daily = [50.0] * 28
        today = datetime.now().date()
        activities = []
        for i, load_val in enumerate(daily):
            if load_val > 0:
                d = today - timedelta(days=27 - i)
                activities.append({"tss": load_val, "start_date": d.isoformat() + "T08:00:00"})
        result = compute_training_load(activities, load_field="tss", date_field="start_date")
        assert result["acwr"] == 1.0


class TestCountConsecutiveTrainingDays:

    def test_empty_returns_empty(self):
        assert count_consecutive_training_days([]) == {}

    def test_no_recent_training(self):
        today = datetime.now().date()
        activities = [
            {"date": (today - timedelta(days=10)).isoformat() + "T08:00:00", "load": 80},
        ]
        assert count_consecutive_training_days(activities) == {}

    def test_single_day(self):
        today = datetime.now().date()
        activities = [
            {"date": today.isoformat() + "T08:00:00", "load": 50},
        ]
        result = count_consecutive_training_days(activities)
        assert result["consecutive_days"] == 1
        assert result["streak_load"] == 50.0

    def test_three_consecutive(self):
        today = datetime.now().date()
        activities = [
            {"date": (today - timedelta(days=2)).isoformat() + "T08:00:00", "load": 85},
            {"date": (today - timedelta(days=1)).isoformat() + "T08:00:00", "load": 45},
            {"date": today.isoformat() + "T08:00:00", "load": 72},
        ]
        result = count_consecutive_training_days(activities)
        assert result["consecutive_days"] == 3
        assert result["streak_load"] == pytest.approx(85 + 45 + 72, rel=0.01)

    def test_gap_breaks_streak(self):
        today = datetime.now().date()
        activities = [
            {"date": (today - timedelta(days=3)).isoformat() + "T08:00:00", "load": 80},
            {"date": (today - timedelta(days=1)).isoformat() + "T08:00:00", "load": 60},
            {"date": today.isoformat() + "T08:00:00", "load": 50},
        ]
        result = count_consecutive_training_days(activities)
        assert result["consecutive_days"] == 2

    def test_below_min_load_not_counted(self):
        today = datetime.now().date()
        activities = [
            {"date": (today - timedelta(days=1)).isoformat() + "T08:00:00", "load": 15},
            {"date": today.isoformat() + "T08:00:00", "load": 50},
        ]
        result = count_consecutive_training_days(activities)
        assert result["consecutive_days"] == 1

    def test_multiple_activities_same_day(self):
        today = datetime.now().date()
        date_str = today.isoformat() + "T08:00:00"
        activities = [
            {"date": date_str, "load": 15},
            {"date": date_str, "load": 10},
        ]
        result = count_consecutive_training_days(activities)
        assert result["consecutive_days"] == 1
        assert result["streak_load"] == 25.0

    def test_custom_field_names(self):
        """Test using custom field names."""
        today = datetime.now().date()
        activities = [
            {"start_date": today.isoformat() + "T08:00:00", "tss": 50},
        ]
        result = count_consecutive_training_days(
            activities, load_field="tss", date_field="start_date"
        )
        assert result["consecutive_days"] == 1
