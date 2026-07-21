# TradePlan — ORB Ladder System

Automates a manual Nifty options opening-range strategy:

- **SP zone**: synthetic futures opening range via put-call parity on the ATM CE/PE 9:15 candle (`Fut = Strike + CE - PE`).
- **Ladder**: ATM +/- N strike first-candle CE/PE levels, used as a trend-strength ruler.
- **Signal engine**: a three-state machine (NEUTRAL / CE_WINS / PE_WINS) that only trades on triple confirmation (implied spot breaks the SP zone AND both ATM CE and PE close on the correct side of their own 9:15 range), removing discretionary/sentiment entries.

## Files

- `orb_common.py` — config, Upstox API helpers, SQLite schema, alerting, expiry/ATM resolution.
- `orb_capture.py` — 9:21 IST job: captures first candles, computes SP zone, stores levels.
- `orb_signal.py` — replay (backtest a stored day) or live signal/trade loop.
- `orb_auto.py` — fully automatic daily runner: resolves expiry+ATM, captures, runs the live loop,
  sleeps until the next trading day, repeats. This is the only script you need to run once you've
  validated the strategy via replay.

## Setup

```
pip install -r requirements.txt
set UPSTOX_ACCESS_TOKEN=<your token>
set ORB_TG_TOKEN=<telegram bot token>      # optional, for entry/exit alerts
set ORB_TG_CHAT=<telegram chat id>
```

## Usage

Backfill and validate a known day first (do this before trusting anything below):

```
python orb_capture.py --expiry 2026-07-28 --date 2026-07-21 --atm 24200
python orb_signal.py --replay 2026-07-21
```

Fully automatic (recommended once validated):

```
python orb_auto.py
```
Leave it running. It sleeps until 09:21 IST each weekday, auto-resolves the nearest weekly
expiry and today's ATM from the live spot price, captures the opening range, runs the signal
loop until square-off, and repeats the next day — no daily manual steps. Telegram alerts fire
on every ENTRY and EXIT automatically (`orb_common.alert`, wired into `orb_signal.on_candle_close`).
It is not holiday-aware yet; a capture failure on a market holiday is caught and logged, and
that day is simply skipped.

Manual/single-day equivalent (for testing):

```
python orb_capture.py --expiry <this week's expiry>   # run at/after 9:21 IST
python orb_signal.py --live
```

## Status

Unvalidated — no backtest run yet. Trail/stop constants in `orb_signal.py`
(`entry * 0.7`, `crossed * 0.85`) are placeholders; tune them after replaying
30-60 historical sessions and inspecting the `orb_trades` table before any
paper or live trading.
