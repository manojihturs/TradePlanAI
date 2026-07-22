# TradePlan — ORB Ladder System

Automates a manual Nifty options opening-range strategy:

- **SP zone**: synthetic futures opening range via put-call parity on the ATM CE/PE 9:15 candle (`Fut = Strike + CE - PE`). ATM is fixed from the 9:15 candle's OPEN tick, not a live LTP snapshot.
- **Ladder**: ATM +/- N strike first-candle CE/PE levels, used as a trend-strength ruler.
- **Signal engine**: a three-state machine (NEUTRAL / CE_WINS / PE_WINS) that only trades on triple confirmation (implied spot breaks the SP zone AND both ATM CE and PE close on the correct side of their own 9:15 range), removing discretionary/sentiment entries.
- **Risk management**: fixed rupee risk per trade derived from capital + daily loss cap, a hard stop-loss, and a trailing stop-loss (breakeven lock at 1R, then trailing behind each ladder line crossed). A daily loss limit locks the machine out for the rest of the session once hit.
- **Fully automatic**: no trade-approval prompts. `orb_auto.py` runs unattended day after day.
- **Telegram notifications**: mandatory for live/auto mode — required on every ENTRY and EXIT.
- **Logging**: every alert is written to a daily file under `logs/`, in addition to Telegram + console.
- **Dashboard**: `orb_ui.py` serves a local live status page (capital, day PnL, open position, trade history, live Nifty spot/future LTP, a Telegram test-message button).
- **Trade journal**: every completed trade is written both to SQLite (`orb_trades`, with `entry_note`/`exit_note` explaining why it was taken and why it made/lost money) and to a per-day sheet in `trade_journal.xlsx`.

Scope: **Nifty only** for now.

## Files

- `orb_common.py` — config, Upstox API helpers, SQLite schema, alerting, logging, expiry/ATM resolution, risk sizing.
- `orb_capture.py` — 9:21 IST job: captures first candles, computes SP zone, stores levels.
- `orb_signal.py` — replay (backtest a stored day) or live signal/trade loop, with SL/TSL and daily loss cap.
- `orb_auto.py` — fully automatic daily runner: resolves expiry+ATM, captures, runs the live loop,
  sleeps until the next trading day, repeats. This is the only script you need to run once you've
  validated the strategy via replay.
- `orb_ui.py` — Flask dashboard (`http://localhost:8765`) reading `orb_state.json` + the trades DB,
  plus live Nifty spot/future LTP and a Telegram test-message button.
- `orb_journal.py` — writes each completed trade to a per-day sheet in `trade_journal.xlsx`.
- `test_offline.py` — network-free regression test of the parity math, state machine (CE_WINS,
  PE_WINS, breakeven-lock TSL, daily-loss lockout), and trade journal writes.

## Setup

```
pip install -r requirements.txt
```

Create a `.env` file in this folder (never committed - already in `.gitignore`):

```
UPSTOX_ACCESS_TOKEN=<your token>
ORB_TG_TOKEN=<telegram bot token>       # required for live/auto mode
ORB_TG_CHAT=<telegram chat id>          # required for live/auto mode
```
`orb_common.py` loads `.env` automatically. Alternatively set these as real environment variables.

Optional risk/sizing overrides (defaults shown):

```
set ORB_CAPITAL=50000
set ORB_MAX_DAILY_LOSS=2500      # rupees; keep in your 2000-3000 range
set ORB_LOT_SIZE=65
set ORB_LOTS=1
```

Per-trade risk budget = `ORB_MAX_DAILY_LOSS / MAX_STOPS_PER_DAY` (default 2), so two full-loss
trades in a day exhausts the daily cap. The stop-loss in premium points is that rupee budget
divided by quantity (`LOT_SIZE * LOTS`); the trailing stop locks to breakeven once a trade is up
1R and then trails behind each ladder line crossed.

## Usage

**Validate first** — do not skip this:

```
python orb_capture.py --expiry 2026-07-28 --date 2026-07-21
python orb_signal.py --replay 2026-07-21
```
(ATM auto-resolves from that date's historical 9:15 spot candle open; pass `--atm`/`--spot`
only if you want to override it or the historical spot candle isn't available.)

Repeat over 30-60 historical sessions and inspect `orb_trades` in `orb_levels.db` for actual win
rate before trusting live/auto mode with real capital.

**Fully automatic** (once validated):

```
python orb_auto.py
```
Leave it running. It sleeps until 09:21 IST each weekday, auto-resolves the nearest weekly
expiry and today's ATM from the 9:15 spot open, captures the opening range, runs the signal
loop until square-off, and repeats the next day — no daily manual steps and no approval prompts.
Telegram alerts fire on every ENTRY and EXIT. It is not holiday-aware; a capture failure on a
market holiday is caught, logged, and that day is skipped.

**Dashboard** (run alongside, separate process):

```
python orb_ui.py
```
Open http://localhost:8765 — shows live status (NEUTRAL / IN_TRADE / LOCKED), day PnL vs. the
daily loss cap, the open position's SL/TSL and remaining targets, and recent trade history.
Auto-refreshes every 5 seconds.

**Manual/single-day equivalent** (for testing):

```
python orb_capture.py --expiry <this week's expiry>   # run at/after 9:21 IST
python orb_signal.py --live
```

**Offline regression test** (no token needed):

```
python test_offline.py
```

## Status

Logic verified via `test_offline.py` (parity math, state transitions, SL/TSL, trade logging).
**No live backtest has been run yet** — the strategy's actual edge is unproven until you replay
a real batch of historical sessions and review `orb_trades`. Keep this paper-only until that's done.
