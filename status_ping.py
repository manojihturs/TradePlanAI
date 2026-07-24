# status_ping.py - one-shot status summary, printed AND sent to Telegram.
# Meant to be run every N minutes by a Monitor loop during the unlimited-
# trades test day, so there's a heartbeat even on quiet periods with no
# entry/exit (those already alert on their own via orb_signal.py).
#
# Usage: python status_ping.py

import json
from datetime import datetime
from orb_common import IST, STATE_PATH, QTY, alert

def main():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        msg = "STATUS PING: could not read state file (%s) - orb_auto.py may be down." % e
        print(msg)
        alert(msg)
        return

    now = datetime.now(IST).strftime("%H:%M")
    st = state.get("state", "?")
    pnl = state.get("daily_pnl_rupees", 0)
    signals = state.get("signals", 0)
    stops = state.get("stops", 0)
    pos = state.get("position")
    updated_at = state.get("updated_at", "?")

    if pos:
        pos_txt = " | OPEN: %s entry %.2f, trail %.2f" % (
            pos.get("side"), pos.get("entry", 0), pos.get("trail", 0))
    else:
        pos_txt = " | no open position"

    msg = ("STATUS %s | %s | day PnL Rs %.2f | signals %d, stops %d%s | state updated %s"
           % (now, st, pnl, signals, stops, pos_txt, updated_at))
    print(msg)
    alert(msg)

if __name__ == "__main__":
    main()
