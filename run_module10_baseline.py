"""Glue script: runs strategy/multi_day_backtest.py (Module 10) against
every captured session in orb_levels.db, using real Upstox data. NOT part
of the strategy/ package - only the network/DB adapter, per Module 1's
and Module 10's own no-network-dependency design.
"""

import sys
from datetime import date

sys.path.insert(0, r"C:\Code\Trade\TradePlan")

import orb_common as oc
from strategy.entry_signal import Candle as StrategyCandle
from strategy.multi_day_backtest import DayInput, export_to_excel, run_multi_day_backtest

STRIKE_GAP = 50
NUM_STRIKES = 6


def discover_sessions():
    rows = oc.db().execute("SELECT session_date, expiry FROM orb_summary ORDER BY session_date").fetchall()
    return [(date.fromisoformat(r[0]), date.fromisoformat(r[1])) for r in rows]


def make_fetch_day(session_date: date, expiry: date):
    def fetch_first_candle(strike: int, side: str):
        chain = oc.resolve_option_chain(expiry, strike, gap=STRIKE_GAP, n=0)
        instrument_key = chain[(strike, side)]
        candles_1m = oc.fetch_historical_candles(instrument_key, 1, session_date, session_date)
        first = oc.first_5min_candle(oc.resample(candles_1m, oc.CANDLE_MINUTES), session_date)
        if first is None:
            raise RuntimeError(f"no first-5min candle for strike {strike} {side}")
        return (first.open, first.high, first.low, first.close)

    def fetch_day(d: date) -> DayInput:
        spot_open = oc.get_spot_open_915(d)
        atm = int(round(spot_open / STRIKE_GAP) * STRIKE_GAP)
        strikes = [atm + i * STRIKE_GAP for i in range(-NUM_STRIKES, NUM_STRIKES + 1)]
        ce_series, pe_series = {}, {}
        for strike in strikes:
            chain = oc.resolve_option_chain(expiry, strike, gap=STRIKE_GAP, n=0)
            ce_key, pe_key = chain[(strike, "CE")], chain[(strike, "PE")]
            ce_c = oc.resample(oc.fetch_historical_candles(ce_key, 1, d, d), oc.CANDLE_MINUTES)
            pe_c = oc.resample(oc.fetch_historical_candles(pe_key, 1, d, d), oc.CANDLE_MINUTES)
            ce_series[strike] = {c.ts: StrategyCandle(c.open, c.high, c.low, c.close) for c in ce_c}
            pe_series[strike] = {c.ts: StrategyCandle(c.open, c.high, c.low, c.close) for c in pe_c}
        return DayInput(session_date=d, spot_open=spot_open, fetch_first_candle=fetch_first_candle,
                         ce_series=ce_series, pe_series=pe_series)

    return fetch_day


def main() -> None:
    sessions = discover_sessions()
    print(f"Discovered {len(sessions)} captured sessions: {[s[0].isoformat() for s in sessions]}")

    session_dates = [s[0] for s in sessions]
    expiry_by_date = {s[0]: s[1] for s in sessions}

    def fetch_day(d: date) -> DayInput:
        return make_fetch_day(d, expiry_by_date[d])(d)

    result = run_multi_day_backtest(session_dates, fetch_day, STRIKE_GAP, NUM_STRIKES)

    print("\n" + "=" * 100)
    print("DAILY SUMMARY")
    print("=" * 100)
    print(f"{'Date':<12}{'Trades':>8}{'Wins':>6}{'Losses':>8}{'WinRate%':>10}"
          f"{'GrossP':>10}{'GrossL':>10}{'NetPnL':>10}{'MaxDD':>8}{'OpenEnd':>8}"
          f"{'Rejected':>10}{'Completed':>11}{'Unused':>8}")
    for r in result.daily_reports:
        print(f"{r.session_date.isoformat():<12}{r.trades:>8}{r.wins:>6}{r.losses:>8}"
              f"{r.win_rate_pct:>10.1f}{r.gross_profit:>10.2f}{r.gross_loss:>10.2f}"
              f"{r.net_pnl:>10.2f}{r.max_drawdown:>8.2f}{r.open_positions_at_close:>8}"
              f"{r.rejected_signals:>10}{r.completed_mapped_levels:>11}{r.unused_mapped_levels:>8}")

    o = result.overall
    print("\n" + "=" * 100)
    print("OVERALL SUMMARY")
    print("=" * 100)
    print(f"Trading days:          {o.trading_days}")
    print(f"Total trades:          {o.total_trades}")
    print(f"Overall win rate:      {o.overall_win_rate_pct:.2f}%")
    print(f"Total gross profit:    {o.total_gross_profit:.2f}")
    print(f"Total gross loss:      {o.total_gross_loss:.2f}")
    print(f"Net PnL:               {o.net_pnl:.2f}")
    print(f"Avg trades/day:        {o.average_trades_per_day:.2f}")
    print(f"Avg daily PnL:         {o.average_daily_pnl:.2f}")
    print(f"Max daily drawdown:    {o.max_daily_drawdown:.2f}")
    print(f"Best day:              {o.best_day} ({o.best_day_pnl:+.2f})" if o.best_day else "Best day: n/a")
    print(f"Worst day:             {o.worst_day} ({o.worst_day_pnl:+.2f})" if o.worst_day else "Worst day: n/a")

    print("\n" + "=" * 100)
    print("FAILED DAYS")
    print("=" * 100)
    if result.failures:
        for f in result.failures:
            print(f"{f.session_date.isoformat()}: {f.reason}")
    else:
        print("None")

    print("\n" + "=" * 100)
    print("DAYS WITH OPEN POSITIONS AT CLOSE")
    print("=" * 100)
    open_days = [r for r in result.daily_reports if r.open_positions_at_close > 0]
    if open_days:
        for r in open_days:
            print(r.session_date.isoformat())
    else:
        print("None")

    print(f"\nTotal rejected signals across all days: {len(result.rejected_signals)}")
    print(f"Total level records across all days: {len(result.level_records)}")

    out_path = export_to_excel(result, "backtest_summary.xlsx")
    print(f"\nExported to {out_path}")


if __name__ == "__main__":
    main()
