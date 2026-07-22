# orb_ui.py - lightweight read-only trading dashboard.
# Run alongside orb_auto.py (separate process) and open http://localhost:8765
#
# Usage:
#   python orb_ui.py
#
# Requirements: pip install flask

import json, os
from datetime import datetime
from flask import Flask, jsonify, render_template_string

from orb_common import (IST, DB_PATH, STATE_PATH, INITIAL_CAPITAL, MAX_DAILY_LOSS,
                        QTY, LOT_SIZE, LOTS, db)

app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>ORB Ladder Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { color-scheme: dark; }
  body { background:#0f1117; color:#e6e6e6; font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin:0; padding:24px; }
  h1 { font-size:20px; margin:0 0 16px; }
  .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap:12px; margin-bottom:24px; }
  .card { background:#171a23; border:1px solid #262b38; border-radius:10px; padding:14px; }
  .card .label { font-size:12px; color:#9aa3b2; text-transform:uppercase; letter-spacing:.04em; }
  .card .value { font-size:22px; font-weight:600; margin-top:4px; }
  .pos { color:#4ade80; } .neg { color:#f87171; } .neu { color:#9aa3b2; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:8px 10px; border-bottom:1px solid #262b38; }
  th { color:#9aa3b2; font-weight:500; }
  .badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px; font-weight:600; }
  .badge.NEUTRAL { background:#262b38; color:#9aa3b2; }
  .badge.IN_TRADE { background:#1e3a2e; color:#4ade80; }
  .badge.LOCKED { background:#3a1e1e; color:#f87171; }
  section { margin-bottom:28px; }
  #stamp { color:#666; font-size:12px; }
</style>
</head>
<body>
  <h1>ORB Ladder — Live Dashboard <span id="stamp"></span></h1>

  <section class="grid" id="cards"></section>

  <section>
    <h3>Position</h3>
    <div id="position" class="card">No open position</div>
  </section>

  <section>
    <h3>Recent trades</h3>
    <table id="trades"><thead><tr>
      <th>Date</th><th>Side</th><th>Entry</th><th>Exit</th><th>Reason</th>
      <th>Lines</th><th>PnL (pts)</th><th>PnL (Rs)</th>
    </tr></thead><tbody></tbody></table>
  </section>

<script>
async function refresh() {
  const r = await fetch('/api/status');
  const d = await r.json();

  document.getElementById('stamp').textContent = 'updated ' + (d.state?.updated_at || '');

  const st = d.state || {};
  const pnl = st.daily_pnl_rupees ?? 0;
  const pnlClass = pnl > 0 ? 'pos' : (pnl < 0 ? 'neg' : 'neu');
  document.getElementById('cards').innerHTML = `
    <div class="card"><div class="label">App / Server</div><div class="value" style="font-size:16px">${st.app_name || '-'} @ ${st.server || '-'}</div></div>
    <div class="card"><div class="label">Status</div><div class="value">
      <span class="badge ${st.state || 'NEUTRAL'}">${st.state || 'NEUTRAL'}</span></div></div>
    <div class="card"><div class="label">Capital</div><div class="value">Rs ${d.capital}</div></div>
    <div class="card"><div class="label">Day PnL</div><div class="value ${pnlClass}">Rs ${pnl}</div></div>
    <div class="card"><div class="label">Max Daily Loss</div><div class="value">Rs ${d.max_daily_loss}</div></div>
    <div class="card"><div class="label">Qty / lot</div><div class="value">${d.qty} (${d.lots}x${d.lot_size})</div></div>
    <div class="card"><div class="label">Signals / Stops today</div><div class="value">${st.signals ?? 0} / ${st.stops ?? 0}</div></div>
    <div class="card"><div class="label">SP Zone</div><div class="value">${st.sp_low ?? '-'} - ${st.sp_high ?? '-'}</div></div>
    <div class="card"><div class="label">ATM</div><div class="value">${st.atm ?? '-'}</div></div>
  `;

  const posEl = document.getElementById('position');
  if (st.position) {
    const p = st.position;
    posEl.innerHTML = `Side <b>${p.side}</b> | Entry ${p.entry} | SL/TSL ${p.trail?.toFixed ? p.trail.toFixed(2) : p.trail}
      | Lines crossed ${p.crossed} | Remaining targets ${JSON.stringify(p.lines)}`;
  } else {
    posEl.textContent = 'No open position';
  }

  const tr = await fetch('/api/trades');
  const trades = await tr.json();
  const qty = d.qty || 1;
  document.querySelector('#trades tbody').innerHTML = trades.map(t => `
    <tr>
      <td>${t.session_date}</td><td>${t.side}</td><td>${t.entry_price}</td>
      <td>${t.exit_price}</td><td>${t.exit_reason}</td><td>${t.lines_crossed}</td>
      <td class="${t.pnl_points >= 0 ? 'pos' : 'neg'}">${t.pnl_points}</td>
      <td class="${t.pnl_points >= 0 ? 'pos' : 'neg'}">${(t.pnl_points * qty).toFixed(2)}</td>
    </tr>`).join('');
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/api/status")
def status():
    state = {}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
    return jsonify({
        "state": state,
        "capital": INITIAL_CAPITAL,
        "max_daily_loss": MAX_DAILY_LOSS,
        "qty": QTY, "lots": LOTS, "lot_size": LOT_SIZE,
    })

@app.route("/api/trades")
def trades():
    conn = db()
    rows = conn.execute(
        "SELECT session_date, side, entry_price, exit_price, exit_reason, "
        "lines_crossed, pnl_points FROM orb_trades ORDER BY entry_ts DESC LIMIT 50"
    ).fetchall()
    cols = ["session_date", "side", "entry_price", "exit_price", "exit_reason",
            "lines_crossed", "pnl_points"]
    return jsonify([dict(zip(cols, r)) for r in rows])

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
