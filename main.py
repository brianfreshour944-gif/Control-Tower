import streamlit as st
import pandas as pd
import plotly.express as px
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import db  # Your updated db.py

def scheduled_daily_reset():
    """This hits the PostgreSQL database."""
    db.archive_and_reset_daily_stats(bot_name="default_bot")  # Change if you have multiple bots

# Start scheduler (runs at midnight UTC)
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=scheduled_daily_reset,
    trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
    id="daily_postgres_reset",
    replace_existing=True
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ---------- DASHBOARD UI ----------
st.set_page_config(layout="wide")
st.title("🏗️ Control Tower (PostgreSQL)")

with st.sidebar:
    st.caption(f"⏰ Next reset: {scheduler.get_job('daily_postgres_reset').next_run_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    if st.button("🚀 Force Archive & Reset"):
        db.archive_and_reset_daily_stats(bot_name="default_bot")
        st.success("Stats archived & reset!")
        st.rerun()

# --- Historical Charts (PostgreSQL Aggregations) ---
tab_live, tab_historical = st.tabs(["📈 Live", "📅 Weekly/Monthly"])

with tab_historical:
    st.subheader("📆 Historical Performance")
    rows = db.get_historical_performance(bot_name="default_bot", days=90)
    if not rows:
        st.info("Waiting for first midnight archive...")
    else:
        df = pd.DataFrame(rows)
        df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
        df = df.sort_values('snapshot_date')
        
        # Weekly aggregation via pandas
        df['week'] = df['snapshot_date'].dt.strftime('%Y-W%W')
        weekly = df.groupby('week')['daily_pnl'].sum().reset_index()
        
        # Monthly aggregation via pandas
        df['month'] = df['snapshot_date'].dt.strftime('%Y-%m')
        monthly = df.groupby('month')['daily_pnl'].sum().reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(weekly, x='week', y='daily_pnl', title="Weekly Net P&L")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(monthly, x='month', y='daily_pnl', title="Monthly Net P&L")
            st.plotly_chart(fig, use_container_width=True)
        
        # Cumulative Equity Curve
        df['cumulative'] = df['daily_pnl'].cumsum()
        fig = px.line(df, x='snapshot_date', y='cumulative', title="Cumulative P&L")
        st.plotly_chart(fig, use_container_width=True)


