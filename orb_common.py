# orb_common.py - shared config + Upstox helpers for the ORB ladder system.
# Auth: set env var UPSTOX_ACCESS_TOKEN before running.
# Requires: pip install requests

import gzip, io, json, logging, os, sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import requests

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

INSTRUMENT     = "NIFTY"
SPOT_KEY       = "NSE_INDEX|Nifty 50"
STRIKE_GAP     = 50
NUM_STRIKES    = 6      # ladder = ATM +/- 6 (ITM6..ATM..OTM6, per the trader's own chart setup)
SIGNAL_STRIKES = 6      # all +/- 6 strikes gate signals and the other-strike early-exit rule
CANDLE_MINUTES = 5      # confirmation candle size (trader confirmed: all trades on 5-min)

IST         = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = time(9, 15)
ORB_LOCK    = time(9, 20)
LAST_ENTRY  = time(14, 30)
SQUARE_OFF  = time(15, 15)

MAX_SIGNALS_PER_DAY = 2
MAX_STOPS_PER_DAY   = 2

APP_NAME    = os.environ.get("ORB_APP_NAME", "tradePlan_local")
SERVER_NAME = os.environ.get("ORB_SERVER_NAME", "local")

# ---- Capital / risk / sizing -----------------------------------------
LOT_SIZE         = int(os.environ.get("ORB_LOT_SIZE", "65"))
LOTS             = int(os.environ.get("ORB_LOTS", "1"))
QTY              = LOT_SIZE * LOTS
INITIAL_CAPITAL  = float(os.environ.get("ORB_CAPITAL", "50000"))
MAX_DAILY_LOSS   = float(os.environ.get("ORB_MAX_DAILY_LOSS", "2500"))  # rupees, 2000-3000 range
# Risk budget per trade so that MAX_STOPS_PER_DAY losers exhausts MAX_DAILY_LOSS.
RISK_PER_TRADE_RUPEES = MAX_DAILY_LOSS / MAX_STOPS_PER_DAY
SL_POINTS        = RISK_PER_TRADE_RUPEES / QTY          # initial stop, in premium points
TSL_TRIGGER_R    = 1.0    # move stop to lock-in once profit >= 1R (SL_POINTS)
TSL_STEP_POINTS  = SL_POINTS * 0.5                       # trail buffer behind each crossed line
# Minimum net premium points a winning trade must lock in once the TSL
# activates, so a "win" clears exchange fees/STT/brokerage instead of exiting
# flat (or worse) at plain breakeven.
MIN_PROFIT_POINTS = float(os.environ.get("ORB_MIN_PROFIT_POINTS", "3"))

_HERE   = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_HERE, "orb_levels.db")
MASTER_CACHE = os.path.join(_HERE, "nse_master_cache.json")
LOG_DIR = os.path.join(_HERE, "logs")
STATE_PATH = os.path.join(_HERE, "orb_state.json")

API_BASE = "https://api.upstox.com"
INSTRUMENT_MASTER_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"

TELEGRAM_BOT_TOKEN = os.environ.get("ORB_TG_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("ORB_TG_CHAT", "")

def require_telegram_config():
    """Telegram alerts are mandatory for live/auto running - fail fast if unset."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "ORB_TG_TOKEN and ORB_TG_CHAT must both be set - Telegram notification "
            "is required before running live or auto mode.")

_logger = None

def setup_logging():
    global _logger
    if _logger is not None:
        return _logger
    os.makedirs(LOG_DIR, exist_ok=True)
    fname = os.path.join(LOG_DIR, "orb_%s.log" % datetime.now(IST).strftime("%Y%m%d"))
    logger = logging.getLogger("orb")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(fname, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(fh)
    _logger = logger
    return logger

def write_state(**fields):
    """Snapshot current status to disk for the UI (orb_ui.py) to poll."""
    fields["updated_at"] = datetime.now(IST).isoformat()
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(fields, f, default=str)
    except Exception:
        pass

def _headers():
    token = os.environ.get("UPSTOX_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("Set UPSTOX_ACCESS_TOKEN environment variable first.")
    return {"Authorization": "Bearer " + token, "Accept": "application/json"}

def _get(url, params=None):
    r = requests.get(url, headers=_headers(), params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def load_instrument_master(force_refresh=False):
    today_tag = date.today().isoformat()
    if not force_refresh and os.path.exists(MASTER_CACHE):
        with open(MASTER_CACHE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("_date") == today_tag:
            return cached["rows"]
    resp = requests.get(INSTRUMENT_MASTER_URL, timeout=60)
    resp.raise_for_status()
    rows = json.loads(gzip.GzipFile(fileobj=io.BytesIO(resp.content)).read())
    with open(MASTER_CACHE, "w", encoding="utf-8") as f:
        json.dump({"_date": today_tag, "rows": rows}, f)
    return rows

def resolve_option_chain(expiry, atm, gap=STRIKE_GAP, n=NUM_STRIKES):
    """Returns {(strike, 'CE'|'PE'): instrument_key} for ATM +/- n strikes."""
    rows = load_instrument_master()
    wanted = set(atm + i * gap for i in range(-n, n + 1))
    out = {}
    for r in rows:
        if r.get("segment") != "NSE_FO":            continue
        if r.get("underlying_symbol") != INSTRUMENT: continue
        itype = r.get("instrument_type")
        if itype not in ("CE", "PE"):               continue
        exp_ms = r.get("expiry")
        if exp_ms is None:                          continue
        exp_d = datetime.fromtimestamp(exp_ms / 1000, tz=IST).date()
        if exp_d != expiry:                         continue
        strike = int(float(r.get("strike_price", 0)))
        if strike in wanted:
            out[(strike, itype)] = r["instrument_key"]
    missing = [(s, t) for s in sorted(wanted) for t in ("CE", "PE") if (s, t) not in out]
    if missing:
        raise RuntimeError("Missing contracts in instrument master: %s" % missing)
    return out

def get_ltp(instrument_key):
    data = _get(API_BASE + "/v2/market-quote/ltp", params={"instrument_key": instrument_key})
    return float(list(data["data"].values())[0]["last_price"])

def get_spot_ltp():
    return get_ltp(SPOT_KEY)

def resolve_future_instrument_key(expiry):
    """Nearest NIFTY future contract instrument_key for the given expiry."""
    rows = load_instrument_master()
    for r in rows:
        if r.get("segment") != "NSE_FO":            continue
        if r.get("underlying_symbol") != INSTRUMENT: continue
        if r.get("instrument_type") != "FUT":       continue
        exp_ms = r.get("expiry")
        if exp_ms is None:                          continue
        exp_d = datetime.fromtimestamp(exp_ms / 1000, tz=IST).date()
        if exp_d == expiry:
            return r["instrument_key"]
    raise RuntimeError("No NIFTY future found for expiry %s" % expiry)

def get_spot_open_915(session_date):
    """The 9:15 candle's OPEN tick for the underlying index - the reference
    price used to fix ATM for the day (rather than whatever LTP happens to
    be when the capture job runs)."""
    is_today = (session_date == datetime.now(IST).date())
    if is_today:
        candles = fetch_intraday_candles(SPOT_KEY, 1)
    else:
        candles = fetch_historical_candles(SPOT_KEY, 1, session_date, session_date)
    target = datetime.combine(session_date, MARKET_OPEN, tzinfo=IST)
    for cndl in candles:
        if cndl.ts == target:
            return cndl.open
    raise RuntimeError("No 09:15 spot candle found for %s yet." % session_date)

def get_nearest_expiry(session_date):
    """Nearest NIFTY option expiry on/after session_date, from the instrument master."""
    rows = load_instrument_master()
    expiries = set()
    for r in rows:
        if r.get("segment") != "NSE_FO":            continue
        if r.get("underlying_symbol") != INSTRUMENT: continue
        if r.get("instrument_type") not in ("CE", "PE"): continue
        exp_ms = r.get("expiry")
        if exp_ms is None:                          continue
        expiries.add(datetime.fromtimestamp(exp_ms / 1000, tz=IST).date())
    upcoming = sorted(e for e in expiries if e >= session_date)
    if not upcoming:
        raise RuntimeError("No upcoming NIFTY expiry found in instrument master.")
    return upcoming[0]

def nearest_strike(price, gap=STRIKE_GAP):
    return int(round(price / gap) * gap)

@dataclass
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

def _parse_candles(payload):
    out = []
    for row in payload.get("data", {}).get("candles", []):
        ts = datetime.fromisoformat(row[0]).astimezone(IST)
        out.append(Candle(ts, float(row[1]), float(row[2]),
                          float(row[3]), float(row[4]), float(row[5])))
    out.sort(key=lambda c: c.ts)   # Upstox returns newest-first
    return out

def fetch_intraday_candles(instrument_key, minutes):
    # Upstox v3. If your account is on v2, use:
    #   /v2/historical-candle/intraday/{key}/{m}minute
    url = "%s/v3/historical-candle/intraday/%s/minutes/%d" % (API_BASE, instrument_key, minutes)
    return _parse_candles(_get(url))

def fetch_historical_candles(instrument_key, minutes, day_from, day_to):
    url = "%s/v3/historical-candle/%s/minutes/%d/%s/%s" % (
        API_BASE, instrument_key, minutes, day_to.isoformat(), day_from.isoformat())
    return _parse_candles(_get(url))

def first_5min_candle(candles, session_date):
    target = datetime.combine(session_date, MARKET_OPEN, tzinfo=IST)
    for c in candles:
        if c.ts == target:
            return c
    return None

def resample(candles_1m, minutes):
    """Aggregate 1-min candles into N-min candles aligned to 09:15."""
    if not candles_1m:
        return []
    buckets = {}
    anchor = datetime.combine(candles_1m[0].ts.date(), MARKET_OPEN, tzinfo=IST)
    for c in candles_1m:
        offset = int((c.ts - anchor).total_seconds() // 60)
        if offset < 0:
            continue
        b = anchor + timedelta(minutes=(offset // minutes) * minutes)
        if b not in buckets:
            buckets[b] = Candle(b, c.open, c.high, c.low, c.close, c.volume)
        else:
            agg = buckets[b]
            agg.high = max(agg.high, c.high)
            agg.low = min(agg.low, c.low)
            agg.close = c.close
            agg.volume += c.volume
    return [buckets[k] for k in sorted(buckets)]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS orb_summary(
        session_date TEXT PRIMARY KEY, atm INTEGER, expiry TEXT,
        fut_high REAL, fut_low REAL, sp_high INTEGER, sp_low INTEGER,
        captured_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS orb_levels(
        session_date TEXT, strike INTEGER, side TEXT, instrument_key TEXT,
        first_open REAL, first_high REAL, first_low REAL,
        first_close REAL, first_volume REAL,
        PRIMARY KEY(session_date, strike, side))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS orb_trades(
        session_date TEXT, entry_ts TEXT, side TEXT, strike INTEGER,
        entry_price REAL, exit_ts TEXT, exit_price REAL,
        exit_reason TEXT, lines_crossed INTEGER, pnl_points REAL,
        entry_note TEXT, exit_note TEXT, source TEXT)""")
    # migrate older DBs created before entry_note/exit_note/source existed
    cols = [r[1] for r in conn.execute("PRAGMA table_info(orb_trades)").fetchall()]
    if "entry_note" not in cols:
        conn.execute("ALTER TABLE orb_trades ADD COLUMN entry_note TEXT")
    if "exit_note" not in cols:
        conn.execute("ALTER TABLE orb_trades ADD COLUMN exit_note TEXT")
    if "source" not in cols:
        conn.execute("ALTER TABLE orb_trades ADD COLUMN source TEXT")
        # Deliberately NOT auto-backfilling existing NULL rows as 'live' here:
        # this DB may already contain rows from both orb_auto.py (live) and
        # manual orb_signal.py --replay runs (replay) written before this
        # column existed, and guessing wrong would just re-create the exact
        # mixing problem this column exists to fix. Existing NULL rows are
        # left NULL/unknown; correct them explicitly per-row if you know
        # which mode produced them (see the one-off fix run for 2026-07-22).
    conn.commit()
    return conn

def alert(msg):
    stamp = datetime.now(IST).strftime("%H:%M:%S")
    tagged = "[%s@%s] %s" % (APP_NAME, SERVER_NAME, msg)
    print("[%s] %s" % (stamp, tagged), flush=True)
    if _logger is not None:
        _logger.info(tagged)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post("https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_BOT_TOKEN,
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": tagged}, timeout=10)
        except Exception as e:
            print("  (telegram failed: %s)" % e)
