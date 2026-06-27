
# main.py
import streamlit as st
from datetime import datetime
from sqlalchemy import text

# Import our modules
import database as db
import strategy as strat
from theme import apply_theme
from ui_helpers import colored_pnl, metric_box, white_val, sanitize_df
from tabs import (
    bot_control,
    portfolio,
    orders,
    performance,
    error_log,
    per_bot_stats,
    trade_history,
    backtest,
    fifo_debugger,
    daily_pnl,
)

# Page config
st.set_page_config(page_title="Trading Command Center", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# Theme (CSS)
apply_theme()


def render_sidebar():
    """Render the sidebar control panel (refresh, reset stats, emergency stop)."""
    with st.sidebar:
        st.header("⚙️ Control Panel")
        if st.button("🔄 Refresh All Data", width='stretch'):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        auto = st.toggle("Auto-refresh every 5s", value=st.session_state.auto_refresh)
        if auto != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto
            st.rerun()
        st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        st.divider()

        if st.button("🗑️ Reset All Trading Stats", type="secondary", width='stretch'):
            st.session_state.show_reset_confirm = True

        if st.session_state.get("show_reset_confirm"):
            st.warning("⚠️ Are you sure? This will DELETE all trades and reset daily loss.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Reset Everything", type="primary", width='stretch'):
                    db.reset_all_trading_stats()
                    st.session_state.show_reset_confirm = False
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", key="cancel_reset", width='stretch'):
                    st.session_state.show_reset_confirm = False
                    st.rerun()

        st.divider()

        if st.button("🛑 EMERGENCY STOP ALL", type="secondary", width='stretch'):
            st.session_state.show_stop_confirm = True

        if st.session_state.get("show_stop_confirm"):
            st.error("🚨 STOP ALL BOTS?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🛑 YES, STOP ALL", type="primary", width='stretch'):
                    with db.get_db_engine().connect() as conn:
                        conn.execute(text("UPDATE bot_status SET status = 'STOP'"))
                        conn.commit()
                    st.session_state.show_stop_confirm = False
                    st.success("All bots stopped")
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", key="cancel_stop", width='stretch'):
                    st.session_state.show_stop_confirm = False
                    st.rerun()


def load_data():
    """Load and sanitize all DataFrames needed by the dashboard.

    Returns a dict of {name: DataFrame} for easy unpacking in main().
    """
    trades_df = db.load_trades()
    status_df = db.get_bot_status()
    error_df = db.load_errors()
    df_pos = db.get_unified_portfolio()
    live_orders = db.get_live_exchange_orders()
    backtest_df = db.get_backtest_results()
    db_orders = db.get_open_orders_from_db()

    # ===== DEBUG: Check row counts =====
    st.sidebar.write("### 📊 Debug Info")
    st.sidebar.write(f"Trades loaded: {len(trades_df)}")
    st.sidebar.write(f"Open Orders (DB): {len(db_orders)}")
    st.sidebar.write(f"Backtest Results: {len(backtest_df)}")
    st.sidebar.write(f"Bot Status: {len(status_df)}")

    return {
        "trades_df": sanitize_df(trades_df),
        "status_df": sanitize_df(status_df),
        "error_df": sanitize_df(error_df),
        "df_pos": sanitize_df(df_pos),
        "live_orders": sanitize_df(live_orders),
        "backtest_df": sanitize_df(backtest_df),
        "db_orders": sanitize_df(db_orders),
    }


def render_top_metrics(data):
    """Render the top metric cards row and the daily cash flow banner."""
    trades_df = data["trades_df"]
    df_pos = data["df_pos"]
    status_df = data["status_df"]

    fifo = strat.fifo_stats_all_bots(trades_df)
    realized_pnl = sum(v['realized_pnl'] for v in fifo.values())
    inventory_cost = sum(v['orphaned_cost_basis'] for v in fifo.values())
    unrealized_pnl = df_pos['unrealized_pl'].sum() if not df_pos.empty else 0.0
    total_pnl = realized_pnl + unrealized_pnl
    daily_cash_flow = strat.get_daily_realized_pnl(trades_df)
    active_bots = len(status_df[status_df['status'] == 'RUNNING']) if not status_df.empty else 0

    # Split portfolio value into real vs. demo/sandbox money so a large
    # OKX sandbox balance never gets mistaken for real capital.
    if not df_pos.empty and 'is_demo' in df_pos.columns:
        live_val = df_pos.loc[~df_pos['is_demo'].astype(bool), 'market_value'].sum()
        demo_val = df_pos.loc[df_pos['is_demo'].astype(bool), 'market_value'].sum()
    else:
        live_val = df_pos['market_value'].sum() if not df_pos.empty else 0
        demo_val = 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.markdown(metric_box("Total Trades", white_val(len(trades_df), "{:,.0f}")), unsafe_allow_html=True)
    with c2: st.markdown(metric_box("Realized P&L", colored_pnl(realized_pnl)), unsafe_allow_html=True)
    with c3: st.markdown(metric_box("Unrealized P&L", colored_pnl(unrealized_pnl)), unsafe_allow_html=True)
    with c4: st.markdown(metric_box("Total P&L", colored_pnl(total_pnl)), unsafe_allow_html=True)
    with c5: st.markdown(metric_box("Active Bots", white_val(active_bots, "{:,.0f}")), unsafe_allow_html=True)
    with c6: st.markdown(metric_box("Portfolio Value (Live)", white_val(live_val)), unsafe_allow_html=True)

    if demo_val > 0:
        st.caption(f"🧪 Demo/sandbox portfolio value (not real money, excluded above): ${demo_val:,.2f}")

    flow_class = "profit" if daily_cash_flow >= 0 else "loss"
    sign = "+" if daily_cash_flow >= 0 else ""
    st.markdown(
        f'<div class="status-banner">'
        f'📅 <b>Today\'s Operating Cash Flow:</b> &nbsp;'
        f'<span class="{flow_class}" style="font-weight:700;font-size:1.1rem;">{sign}${daily_cash_flow:,.2f}</span>'
        f'&nbsp;&nbsp;|&nbsp;&nbsp;<span style="color:#94A3B8;font-size:0.85rem">'
        f'<i>Note: Negative value indicates buying asset inventory, not a loss. Currently held inventory cost: ${inventory_cost:,.2f}</i>'
        f'</span>'
        f'</div>', unsafe_allow_html=True)

    return fifo


def render_tabs(data, fifo):
    """Create the tab bar and delegate rendering to each tab module."""
    trades_df = data["trades_df"]
    status_df = data["status_df"]
    error_df = data["error_df"]
    df_pos = data["df_pos"]
    live_orders = data["live_orders"]
    backtest_df = data["backtest_df"]
    db_orders = data["db_orders"]

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "🤖 Bot Control", "💰 Portfolio", "📋 Open Orders", "📈 Performance",
        "🚨 Error Log", "🎯 Per-Bot Stats", "🗓️ Daily/Weekly P&L", "📜 Trade History",
        "📊 Backtest vs Live", "📈 Bot P&L Comparison", "🧪 FIFO Debugger"
    ])

    with tab1:
        bot_control.render(status_df)
    with tab2:
        portfolio.render(df_pos)
    with tab3:
        orders.render(db_orders, live_orders)
    with tab4:
        performance.render_performance(trades_df)
    with tab5:
        error_log.render(error_df)
    with tab6:
        per_bot_stats.render(fifo)
    with tab7:
        daily_pnl.render(trades_df)
    with tab8:
        trade_history.render(trades_df)
    with tab9:
        backtest.render(trades_df, backtest_df)
    with tab10:
        performance.render_bot_pnl_comparison(trades_df)
    with tab11:
        fifo_debugger.render(trades_df)


def main():
    st.title("🚀 Trading Command Center")
    st.caption("**Professional Multi-Exchange Trading Operations Dashboard**")

    if "auto_refresh" not in st.session_state: st.session_state.auto_refresh = False
    if "last_refresh" not in st.session_state: st.session_state.last_refresh = datetime.now()

    render_sidebar()
    data = load_data()
    fifo = render_top_metrics(data)
    st.divider()
    render_tabs(data, fifo)


if __name__ == "__main__":
    main()
