# orb_auto.py - fully automatic daily runner.
#
# Start it once (e.g. as a background process or a Windows service) and
# leave it running. Each trading day it will, with no manual intervention:
#   1. Sleep until just after market open.
#   2. Resolve the nearest weekly expiry + today's ATM automatically.
#   3. Capture the 09:15 opening-range levels (orb_capture.capture).
#   4. Run the live signal loop until square-off, sending a Telegram
#      alert on every ENTRY and EXIT (already built into orb_common.alert
#      via on_candle_close in orb_signal.py).
#   5. Sleep until the next trading day and repeat.
#
# Requirements:
#   set UPSTOX_ACCESS_TOKEN=<token>
#   set ORB_TG_TOKEN=<telegram bot token>      (for notifications)
#   set ORB_TG_CHAT=<telegram chat id>
#
# Run:
#   python orb_auto.py
#
# Note: this does not know market holidays. It will attempt to capture on
# every weekday; if the exchange is closed the capture step will fail to
# find a 09:15 candle and the day is skipped automatically (see except
# block below). Add an explicit holiday list if false starts bother you.

import time as systime
from datetime import datetime, timedelta

from orb_common import (IST, MARKET_OPEN, ORB_LOCK, SQUARE_OFF,
                        nearest_strike, get_spot_ltp, get_spot_open_915,
                        get_nearest_expiry, require_telegram_config,
                        setup_logging, alert)
from orb_capture import capture
from orb_signal import run_live_for_day


def next_market_open(now):
    d = now.date()
    target = datetime.combine(d, ORB_LOCK, tzinfo=IST) + timedelta(minutes=1)  # 09:21
    if now >= target:
        d = d + timedelta(days=1)
        target = datetime.combine(d, ORB_LOCK, tzinfo=IST) + timedelta(minutes=1)
    while target.weekday() >= 5:  # skip Sat/Sun
        target += timedelta(days=1)
    return target


def should_run_today_now(now, last_run_date):
    """True if today is a weekday, we're currently inside the capture-to-
    square-off window, and today's session hasn't been run yet this process
    (covers starting the app late, e.g. at 09:57 instead of 09:21)."""
    if now.weekday() >= 5:
        return False
    if last_run_date == now.date():
        return False
    open_from = datetime.combine(now.date(), ORB_LOCK, tzinfo=IST) + timedelta(minutes=1)
    return open_from <= now < datetime.combine(now.date(), SQUARE_OFF, tzinfo=IST)


def run_one_day():
    now = datetime.now(IST)
    session_date = now.date()
    try:
        expiry = get_nearest_expiry(session_date)
        try:
            atm = nearest_strike(get_spot_open_915(session_date))
        except Exception:
            atm = nearest_strike(get_spot_ltp())
    except Exception as e:
        alert("AUTO: could not resolve expiry/ATM (%s) - skipping today" % e)
        return

    try:
        capture(session_date, expiry, atm)
    except Exception as e:
        alert("AUTO: capture failed (%s) - likely a holiday or no data, skipping today" % e)
        return

    try:
        run_live_for_day(session_date)
    except Exception as e:
        alert("AUTO: live loop crashed (%s)" % e)


def main():
    require_telegram_config()   # Telegram alerts are mandatory - fail fast if missing
    setup_logging()
    alert("orb_auto started - fully automatic mode.")
    last_run_date = None
    while True:
        now = datetime.now(IST)

        if should_run_today_now(now, last_run_date):
            alert("AUTO: market is open now (%s) and today hasn't run yet - starting immediately "
                  "instead of waiting for tomorrow." % now.strftime("%H:%M"))
            run_one_day()
            last_run_date = now.date()
            systime.sleep(60)
            continue

        wake = next_market_open(now)
        wait_s = (wake - now).total_seconds()
        if wait_s > 0:
            alert("AUTO: sleeping until %s IST" % wake.strftime("%Y-%m-%d %H:%M"))
            systime.sleep(min(wait_s, 3600))
            continue  # re-check in <=1hr increments so long sleeps are interruptible/log-friendly
        run_one_day()
        last_run_date = now.date()
        systime.sleep(60)  # avoid tight loop if something returns instantly


if __name__ == "__main__":
    main()
