# Testing Checklist — Monday Readiness

**Purpose:** a step-by-step checklist for exercising TradePlanAI's replay platform before/during Monday's testing session. Everything here has already been run once as part of Sprint 5 ("Packaging") — this document lets you (or anyone else) repeat it.

Branch: `feature/tradingview-strategy-reconstruction`. See `KNOWN_LIMITATIONS.md` for what this build does *not* do yet.

---

## 1. Environment

- [ ] Python 3.12 available (`python --version`)
- [ ] Dependencies installed: `pip install -r requirements.txt` (installs `openpyxl`, `types-openpyxl`, plus the legacy `strategy`/`trading_engine` scripts' `requests`/`flask`/`python-dotenv`/`tzdata`)
- [ ] Working directory is the repo root (`C:\Code\Trade\TradePlan`) — every command below assumes this
- [ ] `orb_levels.db` present at the repo root (it's git-ignored; if missing, real-data commands below will fail with a clear error, not a crash)

## 2. Quality Gate (run before trusting anything else)

```bash
python -m pytest --cov=src --cov-report=term-missing -q
python -m mypy --strict src
python -m ruff check src tests tools
python -m black --check src tests tools
```

Expected: all tests pass, 100% coverage on `src/` (coverage is scoped to `src/` only — `tools/` is excluded, per `pyproject.toml`), zero mypy errors, zero ruff/black diffs.

For `tools/` specifically (needs both `src/` and `tools/` on `MYPYPATH`):

```bash
MYPYPATH=tools python -m mypy --strict tools/regression_validator.py tools/performance_benchmark.py --explicit-package-bases
```

## 3. Circular Dependency Check

No dedicated script exists yet (run ad hoc each sprint) — an AST-based check confirming no package in `src/` imports back to a package that imports it. Ask for this to be re-run if package boundaries change.

## 4. Configuration

- [ ] `ReplayApplicationConfiguration` requires: `dataset_path`, `symbol`, `timeframe`, `output_directory`, `replay_configuration`. `reference_inputs` and `tzinfo` (default `UTC`) are optional.
- [ ] `ReplayConfiguration` requires `start_date`/`end_date` (`end_date >= start_date`); `symbols`/`timeframe`/`replay_speed` are optional/structural only.
- [ ] No config file format (YAML/JSON/TOML) exists or is expected — configuration is constructed in code and passed in. This is deliberate (see `application/replay_application.py`'s own docstring), not a gap.

## 5. Paths

- [ ] `ReplayApplication.run()` auto-creates `output_directory` (`mkdir(parents=True, exist_ok=True)`) — you do not need to pre-create it.
- [ ] The CSV/Excel report writers below do **not** auto-create their output directory — the parent directory must already exist, or the write raises `FileNotFoundError`. Affected: `replay_report.write_report_csv`, `replay_dashboard.write_dashboard_csv`, `TradingAnalysisDashboard.export_csv`/`export_excel`, `regression_validator.write_regression_report_csv`, `performance_benchmark.write_performance_report_csv`.
- [ ] No hardcoded absolute paths exist in `src/` or `tools/` (verified via grep as part of this sprint). `tools/regression_validator.py` and `tools/performance_benchmark.py` bootstrap `sys.path` relative to their own `__file__`, so they run correctly from any checkout location.

## 6. Replay Datasets

- [ ] A CSV dataset for `ReplayApplication` needs columns `Date,Time,Open,High,Low,Close,Volume` (optional `UnderlyingPrice`) — see `data/historical_data_provider.py`.
- [ ] **No real underlying-index OHLC CSV exists anywhere in this repo.** Every replay run in this project's sprints has used a minimal placeholder driver CSV, since `WeeklyFutureStage` never reads the driver CSV's OHLC values — only the real `reference_inputs` (from `orb_levels.db`) matter for its output. See `KNOWN_LIMITATIONS.md` item 1.
- [ ] Real reference-ladder data (13-strike CE/PE first-5-minute-candle highs/lows, captured live) is available for 22 trading days in `orb_summary`/`orb_levels` inside `orb_levels.db` (2026-07-01 through 2026-07-30).

## 7. Output Folders

- [ ] Run a real replay and confirm `replay_result.json` + `event_log.json` land in the configured `output_directory`:
  ```bash
  python -c "
  import sys; sys.path.insert(0, 'src')
  from datetime import date
  from pathlib import Path
  from application.replay_application import ReplayApplication, ReplayApplicationConfiguration
  from application.replay_configuration import ReplayConfiguration
  Path('_check.csv').write_text('Date,Time,Open,High,Low,Close,Volume\n2026-07-29,09:20:00,100,100,100,100,0\n')
  config = ReplayApplicationConfiguration(
      dataset_path=Path('_check.csv'), symbol='NIFTY', timeframe='5m',
      output_directory=Path('_check_out'),
      replay_configuration=ReplayConfiguration(start_date=date(2026,7,29), end_date=date(2026,7,29)),
  )
  ReplayApplication(configuration=config).run()
  print(sorted(Path('_check_out').iterdir()))
  "
  ```
  Expected: `[_check_out/event_log.json, _check_out/replay_result.json]`. Clean up `_check.csv`/`_check_out/` afterward — these are scratch files, not part of the repo.

## 8. Logging

- [ ] No handler is configured by this codebase — call `logging.basicConfig(level=logging.INFO)` (or wire your own handler) before running a replay to see log output.
- [ ] Expected log lines per replay, in order: `Replay started` → `ReferenceBuilder completed` (if reference inputs supplied) → `WeeklyFuture completed` → `StrikeSelector completed` (per stage, per candle) → `Replay finished`. Failures log at `ERROR` from `ReplayApplication` (dataset load / replay execution / report write) and from `BusinessPipeline` (a genuine stage fault).
- [ ] Verified in Sprint 4 against the real `orb_levels.db` — every log line appeared correctly for all 22 days.

## 9. Reports

- [ ] `application.replay_report.build_report_rows`/`write_report_csv` — per-candle CSV (Weekly Future High/Low, Top/Bottom Strike).
- [ ] `application.replay_view.build_view_rows`/`render_view_table` — plain-text table, same fields.
- [ ] `application.replay_validation.build_validation_summary`/`render_validation_log` — whole-run summary + failures.
- [ ] `application.replay_consistency.validate_replay_consistency`/`render_consistency_report` — five structural checks (Reference Strike/ReferenceLevel/Weekly Future/Strike/pipeline completion) per candle.
- [ ] All four verified working against real data as part of this sprint (Sprint 1 and Sprint 5).

## 10. Dashboard

- [ ] `application.replay_dashboard` — per-trading-day validation view (`build_dashboard_rows`/`build_dashboard_summary`/`write_dashboard_csv`).
- [ ] `application.trading_analysis_dashboard.TradingAnalysisDashboard` — trader-facing view: per-day ATM/Weekly Future/Strike + diffs, summary cards, 5 chart series (structured data, not rendered pixels — see `KNOWN_LIMITATIONS.md` item 5), CSV + Excel export.
- [ ] Verified in this sprint: both CSV and Excel (`openpyxl`, sheets `Daily Analysis` + `Summary`) export correctly against a real 5-day combined `ReplayResult`.

## 11. Regression Validator

```bash
python tools/regression_validator.py
```

- [ ] Expected: `PASS` for every date currently in `orb_summary` (22/22 as of this sprint), `regression_report.csv` written, exit code `0`.
- [ ] A corrupted/missing database or NULL data in a row degrades to a clear `FAIL`/`RuntimeError` message, not a crash (Sprint 2 hardening).
- [ ] Optional: `python tools/performance_benchmark.py` — measurement only, writes `performance_report.csv`, always exits `0`.

## 12. Anomaly Watch

While testing Monday, treat any of the following as worth investigating immediately, not routine noise:
- A `FAIL` from the regression validator on a day that previously passed.
- `Days Failed` > 0 in the Replay Validation Dashboard summary.
- Any output from `replay_consistency.render_consistency_report` other than `"No inconsistencies found."`.
- A stage-failure `ERROR` log line during a replay you expected to succeed cleanly.

---

Everything above was exercised as part of Sprint 5 ("Packaging") using the real `orb_levels.db`. No code changes were required to make this checklist pass — see the Sprint 5 commit for the verification run.
