# endurance-metrics

Training metrics for endurance sports: CTL/ATL/TSB, ACWR, decoupling, and more.

Zero external dependencies — uses Python standard library only.

## Installation

```bash
pip install endurance-metrics
```

## Quick start

```python
from endurance_metrics import compute_ctl_atl_tsb, calculate_acwr

# Compute fitness/fatigue/form from daily training loads
activities = [
    {"date": "2026-01-01", "load": 80},
    {"date": "2026-01-02", "load": 65},
    {"date": "2026-01-03", "load": 0},
    {"date": "2026-01-04", "load": 90},
]
ctl, atl, tsb = compute_ctl_atl_tsb(activities)
print(f"CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")

# Compute Acute:Chronic Workload Ratio
acwr = calculate_acwr(activities)
print(f"ACWR={acwr:.2f}")
```

## Features

### Fitness metrics (`endurance_metrics.fitness`)

- `compute_ctl_atl_tsb()` — Chronic/Acute Training Load and Training Stress Balance
- `compute_ctl_history()` — CTL progression over time
- `compute_atl_history()` — ATL progression over time
- `compute_tsb_history()` — TSB progression over time
- `compute_fitness_summary()` — Complete fitness summary
- `compute_form_trend()` — Form trend analysis

### Advanced metrics (`endurance_metrics.advanced`)

- `compute_ramp_rate()` — CTL ramp rate (fitness loading speed)
- `compute_fitness_trend()` — Multi-period fitness trend
- `compute_peak_fitness()` — Peak CTL identification
- `detect_overtraining_risk()` — Overtraining risk detection
- `compute_training_zones_distribution()` — Training zones distribution
- `compute_periodization_score()` — Periodization quality score

### Workload metrics (`endurance_metrics.workload`)

- `calculate_acwr()` — Acute:Chronic Workload Ratio
- `calculate_monotony_strain()` — Training monotony and strain

### Decoupling analysis (`endurance_metrics.decoupling`)

- `calculate_decoupling()` — Effort:Cardio decoupling percentage
- `analyze_overtime()` — Detailed overtime analysis with pacing assessment
- `compute_normalized_power()` — Normalized Power (cycling)

Decoupling supports multiple effort types:

```python
from endurance_metrics import calculate_decoupling

# Cycling (power-based, uses Normalized Power)
dec = calculate_decoupling(watts, hr, effort_type="power")

# Running (pace-based, uses rolling average)
dec = calculate_decoupling(pace, hr, effort_type="pace")

# Pre-normalized data
dec = calculate_decoupling(effort, hr, effort_type="raw")
```

## API reference

### Field names

Workload functions accept customizable field names:

```python
from endurance_metrics import calculate_acwr

# Default: looks for "load" and "date" fields
acwr = calculate_acwr(activities)

# Custom field names
acwr = calculate_acwr(
    activities,
    load_field="tss",
    date_field="start_date",
)
```

### Decoupling with threshold

```python
from endurance_metrics import analyze_overtime

result = analyze_overtime(
    effort_data=watts,
    cardio_data=hr,
    prescribed_seconds=3600,
    effort_type="power",
    threshold=280,  # FTP or threshold value
)
```

## Development

```bash
git clone https://github.com/stephanejouve/endurance-metrics.git
cd endurance-metrics
poetry install --with dev
poetry run pytest tests/ -v
poetry run black src/ tests/ --check --line-length=100
poetry run ruff check src/
poetry run isort src/ tests/ --check-only --profile black --line-length=100
```

## License

MIT
