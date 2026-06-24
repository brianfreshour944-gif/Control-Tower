"""
FILE: database.py
Handles all SQL connection, table creation, and data retrieval.
"""
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, inspect
import os
from datetime import datetime, date
import ccxt

@st.cache_resource
@st.cache_resource
def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
        db_url = db_url.replace("postgres://", "postgresql://")  # <-- ADD THIS LINE
    return create_engine(db_url, pool_size=5, max_overflow=10)

# ---------- Migrations ----------
def ensure_table_exists(table_name):
    engine = get_db_engine()
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        with engine.connect() as conn:
            if table_name == "bot_status":
                conn.execute(text("""CREATE TABLE bot_status (
                    bot_name TEXT PRIMARY KEY, status TEXT DEFAULT 'STOP',
                    last_update TIMESTAMP DEFAULT NOW(), daily_loss REAL DEFAULT 0,
                    daily_loss_limit REAL DEFAULT 100, config TEXT DEFAULT '{}')"""))
            elif table_name == "bot_errors":
                conn.execute(text("""CREATE TABLE bot_errors (
                    id SERIAL PRIMARY KEY, bot_name TEXT,
                    error_message TEXT, timestamp TIMESTAMP DEFAULT NOW())"""))
            elif table_name == "trades":
                conn.execute(text("""CREATE TABLE trades (
                    id SERIAL PRIMARY KEY, bot_name TEXT, exchange TEXT, symbol TEXT,
                    side TEXT, price REAL, quantity REAL, value REAL, fee REAL DEFAULT 0,
                    order_id TEXT, timestamp TIMESTAMP DEFAULT NOW())"""))
            elif table_name == "bot_orders":
                conn.execute(text("""CREATE TABLE bot_orders (
                    order_id TEXT PRIMARY KEY, bot_name TEXT, symbol TEXT, side TEXT,
                    price REAL, status TEXT, created_at TIMESTAMP DEFAULT NOW())"""))
            elif table_name == "backtest_results":
                conn.execute(text("""CREATE TABLE backtest_results (
                    id SERIAL PRIMARY KEY, bot_name TEXT, strategy_name TEXT,
                    start_date DATE, end_date DATE, total_trades INTEGER,
                    net_profit REAL, sharpe_ratio REAL, max_drawdown_pct REAL,
                    win_rate REAL, created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(bot_name, start_date, end_date))"""))
            conn.commit()

def migrate_bot_status():
    engine = get_db_engine()
    inspector = inspect(engine)
    if inspector.has_table("bot_status"):
        cols = [c['name'] for c in inspector.get_columns("bot_status")]
        with engine.connect() as conn:
            if "daily_loss" not in cols:
                conn.execute(text("ALTER TABLE bot_status ADD COLUMN daily_loss REAL DEFAULT 0"))
            if "daily_loss_limit" not in cols:
                conn.execute(text("ALTER TABLE bot_status ADD COLUMN daily_loss_limit REAL DEFAULT 100"))
            if "config" not in cols:
                conn.execute(text("ALTER TABLE bot_status ADD COLUMN config TEXT DEFAULT '{}'"))
            conn.commit()

def migrate_bot_orders():
    engine = get_db_engine()
    inspector = inspect(engine)
    if inspector.has_table("bot_orders"):
        cols = [c['name'] for c in inspector.get_columns("bot_orders")]
        with engine.connect() as conn:
            if "created_at" not in cols:
                conn.execute(text("ALTER TABLE bot_orders ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
            conn.commit()

def migrate_trades():
    engine = get_db_engine()
    inspector = inspect(engine)
    if inspector.has_table("trades"):
        cols = [c['name'] for c in inspector.get_columns("trades")]
        with engine.connect() as conn:
            if "fee" not in cols:
                conn.execute(text("ALTER TABLE trades ADD COLUMN fee REAL DEFAULT 0"))
                conn.commit()

# ---------- Data loaders ----------
@st.cache_data(ttl=30, show_spinner=False)
def load_trades(limit=5000):
    ensure_table_exists("trades")
    migrate_trades()
    ensure_table_exists("backtest_results")
    df = pd.read_sql(f"SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}", get_db_engine())
    df['fee'] = df['fee'].fillna(0.0) if 'fee' in df.columns else 0.0
    df['side'] = df['side'].str.upper()
    return df

@st.cache_data(ttl=10, show_spinner=False)
def get_bot_status():
    ensure_table_exists("bot_status")
    migrate_bot_status()
    return pd.read_sql("SELECT * FROM bot_status", get_db_engine())

@st.cache_data(ttl=60, show_spinner=False)
def load_errors(limit=100):
    ensure_table_exists("bot_errors")
    return pd.read_sql(f"SELECT * FROM bot_errors ORDER BY timestamp DESC LIMIT {limit}", get_db_engine())

@st.cache_data(ttl=3600, show_spinner=False)
def get_backtest_results():
    ensure_table_exists("backtest_results")
    return pd.read_sql("SELECT * FROM backtest_results ORDER BY created_at DESC", get_db_engine())

@st.cache_data(ttl=10, show_spinner=False)
def get_open_orders_from_db():
    ensure_table_exists("bot_orders")
    migrate_bot_orders()
    return pd.read_sql("SELECT * FROM bot_orders WHERE status = 'OPEN'", get_db_engine())

@st.cache_data(ttl=10, show_spinner=False)
def get_all_orders_debug():
    ensure_table_exists("bot_orders")
    migrate_bot_orders()
    return pd.read_sql("SELECT * FROM bot_orders", get_db_engine())

@st.cache_data(ttl=15, show_spinner=False)
def get_unified_portfolio():
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOrdersRequest
    from alpaca.trading.enums import QueryOrderStatus
    API_KEY = os.getenv("APCA_API_KEY_ID")
    API_SECRET = os.getenv("APCA_API_SECRET_KEY")
    PAPER = os.getenv("APCA_API_PAPER", "true").lower() == "true"
    trading_client = TradingClient(api_key=API_KEY, secret_key=API_SECRET, paper=PAPER)
    okx = ccxt.okx({
        'apiKey': os.getenv('OKX_API_KEY'),
        'secret': os.getenv('OKX_API_SECRET'),
        'password': os.getenv('OKX_PASSPHRASE'),
        'hostname': 'app.okx.com',
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    okx.set_sandbox_mode(True)

    positions = []
    try:
        for p in trading_client.get_all_positions():
            qty = float(p.qty); avg = float(p.avg_entry_price); cur = float(p.current_price)
            positions.append({"source": "Alpaca", "symbol": p.symbol, "quantity": qty,
                              "avg_entry": avg, "current_price": cur,
                              "market_value": qty * cur, "unrealized_pl": (cur - avg) * qty})
    except Exception as e:
        st.sidebar.error(f"Alpaca positions: {e}")
    try:
        balance = okx.fetch_balance()
        tickers = okx.fetch_tickers()
        for coin, amount in balance['total'].items():
            if float(amount) > 0.001 and coin not in ['USDT', 'USD', 'USDC']:
                sym = f"{coin}/USDT"
                if sym in tickers:
                    price = tickers[sym]['last']
                    positions.append({"source": "OKX", "symbol": coin, "quantity": float(amount),
                                      "avg_entry": 0.0, "current_price": price,
                                      "market_value": float(amount) * price, "unrealized_pl": 0.0})
    except Exception as e:
        st.sidebar.error(f"OKX balance: {e}")
    return pd.DataFrame(positions)

@st.cache_data(ttl=10, show_spinner=False)
def get_live_exchange_orders():
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOrdersRequest
    from alpaca.trading.enums import QueryOrderStatus
    API_KEY = os.getenv("APCA_API_KEY_ID")
    API_SECRET = os.getenv("APCA_API_SECRET_KEY")
    PAPER = os.getenv("APCA_API_PAPER", "true").lower() == "true"
    trading_client = TradingClient(api_key=API_KEY, secret_key=API_SECRET, paper=PAPER)
    okx = ccxt.okx({
        'apiKey': os.getenv('OKX_API_KEY'),
        'secret': os.getenv('OKX_API_SECRET'),
        'password': os.getenv('OKX_PASSPHRASE'),
        'hostname': 'app.okx.com',
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    okx.set_sandbox_mode(True)

    orders = []
    try:
        for o in trading_client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN)):
            orders.append({"exchange": "Alpaca", "id": o.id, "symbol": o.symbol,
                           "side": o.side.value, "type": o.order_type.value,
                           "qty": float(o.qty),
                           "limit_price": float(o.limit_price) if o.limit_price else None,
                           "bot_name": "N/A"})
    except Exception as e:
        st.sidebar.error(f"Alpaca orders: {e}")
    try:
        for o in okx.fetch_open_orders():
            orders.append({"exchange": "OKX", "id": o['id'], "symbol": o['symbol'],
                           "side": o['side'], "type": o['type'], "qty": o['amount'],
                           "limit_price": o.get('price'), "bot_name": "N/A"})
    except Exception as e:
        st.sidebar.error(f"OKX orders: {e}")
    return pd.DataFrame(orders)

def reset_all_trading_stats():
    """⚠️ DESTRUCTIVE: Deletes all trades and resets daily loss to 0."""
    engine = get_db_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM trades"))
        conn.execute(text("DELETE FROM bot_orders"))
        conn.execute(text("UPDATE bot_status SET daily_loss = 0"))
        conn.execute(text("""
            INSERT INTO bot_status (bot_name, status, daily_loss, daily_loss_limit)
            VALUES ('okx_grid_bot', 'RUNNING', 0, 150)
            ON CONFLICT (bot_name) DO UPDATE
            SET daily_loss = 0, status = 'RUNNING', daily_loss_limit = 150
        """))
        conn.commit()
    st.cache_data.clear()

# ===== NEW: Clear Errors Function =====
def clear_errors():
    """⚠️ DESTRUCTIVE: Deletes all error logs from the bot_errors table."""
    engine = get_db_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM bot_errors"))
        conn.commit()
    st.cache_data.clear()
