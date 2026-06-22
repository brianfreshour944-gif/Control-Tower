# main.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from datetime import datetime, date
from sqlalchemy import text  # needed for EMERGENCY STOP

# Import our modules
import database as db
import strategy as strat

# Page config
st.set_page_config(page_title="Trading Command Center", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .stMetric {background-color: #1a1f2e; border-radius: 10px; padding: 12px;}
    .stMetric label, .stMetric .stMetric-value, .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important; font-size: 2rem !important; font-weight: 600 !important;
    }
    .stMetric .stMetric-label, .stMetric [data-testid="stMetricLabel"] {
        color: #bbbbbb !important; font-size: 1rem !important;
    }
    .custom-metric {
        background-color: #1a1f2e; border-radius: 10px; padding: 1rem; text-align: center;
    }
    .custom-metric-label { color: #bbbbbb; font-size: 1rem; margin-bottom: 0.5rem; }
    .custom-metric-value { font-size: 2rem; font-weight: 600; }
    .profit { color: #00ff9d !important; }
    .loss   { color: #ff4d4d !important; }
    h1 { color: #00b4d8; font-size: 2.8rem; }
    .stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------- UI Helpers ----------
def colored_pnl(value):
    cls = "profit" if value >= 0 else "loss"
    sign = "+" if value >= 0 else ""
    return f'<span class="custom-metric-value {cls}">{sign}${value:,.2f}</span>'

def metric_box(label, content_html):
    return f'<div class="custom-metric"><div class="custom-metric-label">{label}</div>{content_html}</div>'

def white_val(value, fmt="${:,.2f}"):
    return f'<div class="custom-metric-value" style="color:#fff">{fmt.format(value)}</div>'

# ---------- Data Sanitizer (fixes Arrow conversion errors) ----------
def sanitize_df(df):
    """Convert all columns to safe types to prevent Arrow conversion errors."""
    if df.empty:
        return df

    # Make a copy to avoid modifying original
    df = df.copy()

    # 1. Handle ID columns – ensure they are strings (and handle varying lengths)
    id_columns = ['id', 'order_id', 'bot_name', 'exchange', 'symbol']  # add any other identifier columns
    for col in id_columns:
        if col in df.columns:
            # Convert to string, replace NaN with empty string
            df[col] = df[col].astype(str).fillna('')

    # 2. Convert object columns that look like numbers to float
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Try to convert to numeric, but skip if it's a string column already handled
                if col not in id_columns:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass

    # 3. For any numeric column, fill NaN with 0 and convert to float64
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0).astype('float64')

    # 4. Convert any timestamp columns to datetime
    for col in df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df

# ---------- Main ----------
def main():
    st.title("🚀 Trading Command Center")
    st.caption("**Professional Multi-Exchange Trading Operations Dashboard**")

    if "auto_refresh" not in st.session_state: st.session_state.auto_refresh = False
    if "last_refresh" not in st.session_state: st.session_state.last_refresh = datetime.now()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Control Panel")
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        auto = st.toggle("Auto-refresh every 5s", value=st.session_state.auto_refresh)
        if auto != st.session_state.auto_refresh:
            st.session_state.auto_refresh = auto
            st.rerun()
        st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        st.divider()
        if st.button("🗑️ Reset All Trading Stats", type="secondary", use_container_width=True):
            if st.checkbox("⚠️ Confirm: DELETE all trades & reset daily loss"):
                db.reset_all_trading_stats()
            else:
                st.warning("Check the box to confirm.")
        st.divider()
        if st.button("🛑 EMERGENCY STOP ALL", type="secondary", use_container_width=True):
            if st.checkbox("Confirm stop all bots"):
                with db.get_db_engine().connect() as conn:
                    conn.execute(text("UPDATE bot_status SET status = 'STOP'"))
                    conn.commit()
                st.success("All bots stopped")
                st.rerun()

    # ---- Load data ----
    trades_df = db.load_trades()
    # ===== 🛠️ DEBUG: Check which bots are loaded =====
    print("🔍 Bots in trades_df:", trades_df['bot_name'].unique().tolist())

    status_df = db.get_bot_status()
    error_df = db.load_errors()
    df_pos = db.get_unified_portfolio()
    live_orders = db.get_live_exchange_orders()
    backtest_df = db.get_backtest_results()
    db_orders = db.get_open_orders_from_db()

    # ---- Apply sanitizer to ALL DataFrames ----
    trades_df = sanitize_df(trades_df)
    status_df = sanitize_df(status_df)
    error_df = sanitize_df(error_df)
    df_pos = sanitize_df(df_pos)
    live_orders = sanitize_df(live_orders)
    backtest_df = sanitize_df(backtest_df)
    db_orders = sanitize_df(db_orders)

    # ---- Compute metrics ----
    fifo = strat.fifo_stats_all_bots(trades_df)
    realized_pnl = sum(v['realized_pnl'] for v in fifo.values())
    inventory_cost = sum(v['orphaned_cost_basis'] for v in fifo.values())
    unrealized_pnl = df_pos['unrealized_pl'].sum() if not df_pos.empty else 0.0
    total_pnl = realized_pnl + unrealized_pnl
    daily_cash_flow = strat.get_daily_realized_pnl(trades_df)
    active_bots = len(status_df[status_df['status'] == 'RUNNING']) if not status_df.empty else 0
    portfolio_val = df_pos['market_value'].sum() if not df_pos.empty else 0

    # ---- Top metrics ----
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.markdown(metric_box("Total Trades", white_val(len(trades_df), "{:,.0f}")), unsafe_allow_html=True)
    with c2: st.markdown(metric_box("Realized P&L", colored_pnl(realized_pnl)), unsafe_allow_html=True)
    with c3: st.markdown(metric_box("Unrealized P&L", colored_pnl(unrealized_pnl)), unsafe_allow_html=True)
    with c4: st.markdown(metric_box("Total P&L", colored_pnl(total_pnl)), unsafe_allow_html=True)
    with c5: st.markdown(metric_box("Active Bots", white_val(active_bots, "{:,.0f}")), unsafe_allow_html=True)
    with c6: st.markdown(metric_box("Portfolio Value", white_val(portfolio_val)), unsafe_allow_html=True)

    # Today's cash flow
    flow_color = "#00ff9d" if daily_cash_flow >= 0 else "#ff4d4d"
    sign = "+" if daily_cash_flow >= 0 else ""
    st.markdown(
        f'<div style="background:#1a1f2e;border-radius:8px;padding:0.5rem 1rem;margin-bottom:0.5rem;">'
        f'📅 Today\'s cash flow: <span style="color:{flow_color};font-weight:600">'
        f'{sign}${daily_cash_flow:,.2f}</span> &nbsp;'
        f'<span style="color:#888;font-size:0.85rem">'
        f'(negative = buying inventory, not a loss — inventory held: ${inventory_cost:,.2f})</span>'
        f'</div>', unsafe_allow_html=True)

    st.divider()

    # ---- Tabs ----
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "🤖 Bot Control", "💰 Portfolio", "📋 Open Orders", "📈 Performance",
        "🚨 Error Log", "🎯 Per-Bot Stats", "📜 Trade History",
        "📊 Backtest vs Live", "📈 Bot P&L Comparison", "🧪 FIFO Debugger"
    ])

    # === TAB 1: BOT CONTROL ===
    with tab1:
        st.subheader("Bot Management")
        if not status_df.empty:
            sel = st.selectbox("Select Bot", status_df['bot_name'].tolist(), key="bot_select")
            bot_row = status_df[status_df['bot_name'] == sel].iloc[0]
            cA, cB = st.columns(2)
            with cA:
                if st.button("▶️ START BOT"):
                    with db.get_db_engine().connect() as conn:
                        conn.execute(text("UPDATE bot_status SET status='RUNNING' WHERE bot_name=:n"), {"n": sel})
                        conn.commit()
                    st.rerun()
            with cB:
                if st.button("⏹️ STOP BOT"):
                    with db.get_db_engine().connect() as conn:
                        conn.execute(text("UPDATE bot_status SET status='STOP' WHERE bot_name=:n"), {"n": sel})
                        conn.commit()
                    st.rerun()
            dl = float(bot_row.get('daily_loss', 0) or 0)
            lim = float(bot_row.get('daily_loss_limit', 100) or 100)
            st.progress(max(0.0, min(1.0, dl / max(lim, 1))), text=f"Daily Loss: ${dl:.2f} / ${lim:.2f}")
            new_lim = st.number_input("Update daily loss limit ($)", value=lim, step=10.0, key="limit_input")
            if st.button("Update Limit"):
                with db.get_db_engine().connect() as conn:
                    conn.execute(text("UPDATE bot_status SET daily_loss_limit=:l WHERE bot_name=:n"), {"l": new_lim, "n": sel})
                    conn.commit()
                st.rerun()
            st.subheader("⚙️ Bot Configuration")
            try:
                cfg = json.loads(bot_row['config'])
                st.json(cfg)
                new_cfg = st.text_area("Edit config (JSON)", value=json.dumps(cfg, indent=2), height=200, key="config_edit")
                if st.button("Save Config"):
                    with db.get_db_engine().connect() as conn:
                        conn.execute(text("UPDATE bot_status SET config=:c WHERE bot_name=:n"), {"c": new_cfg, "n": sel})
                        conn.commit()
                    st.success("Config updated")
                    st.rerun()
            except:
                st.warning("No valid config JSON")
            st.dataframe(status_df[['bot_name', 'status', 'daily_loss', 'daily_loss_limit']], use_container_width=True)
        else:
            st.warning("No bot status records found.")

    # === TAB 2: PORTFOLIO ===
    with tab2:
        st.subheader("Live Portfolio & Unrealized P&L")
        if not df_pos.empty:
            st.plotly_chart(px.pie(df_pos, values='market_value', names='symbol', hole=0.4, title="Asset Allocation"), use_container_width=True)
            st.dataframe(df_pos[['source','symbol','quantity','avg_entry','current_price','market_value','unrealized_pl']]
                         .style.format({'quantity':'{:.4f}','avg_entry':'${:.2f}','current_price':'${:.2f}','market_value':'${:,.2f}','unrealized_pl':'${:,.2f}'}), use_container_width=True)
            st.metric("Total Portfolio Value", f"${df_pos['market_value'].sum():,.2f}", delta=f"${df_pos['unrealized_pl'].sum():,.2f} unrealized")
        else:
            st.info("No open positions found.")

    # === TAB 3: OPEN ORDERS ===
    with tab3:
        st.subheader("📋 Open Orders")
        if not db_orders.empty:
            cols = ['order_id','bot_name','symbol','side','price']
            if 'created_at' in db_orders.columns: cols.append('created_at')
            st.dataframe(db_orders[cols], use_container_width=True)
        else:
            st.info("No bot-tracked open orders.")
        st.divider()
        st.subheader("Live Exchange Orders")
        if not live_orders.empty:
            st.dataframe(live_orders[['exchange','id','symbol','side','type','qty','limit_price','bot_name']], use_container_width=True)
            sel_id = st.selectbox("Select order to cancel", live_orders['id'].tolist(), key="cancel_select")
            if st.button("Cancel Selected Order"):
                # Cancellation requires trading clients – you may need to import them again
                # For brevity, we skip the actual cancel code here but it's the same as original
                st.warning("Cancellation code not implemented in this snippet – copy from original.")
        else:
            st.success("No live open orders.")

    # === TAB 4: PERFORMANCE ===
    with tab4:
        st.subheader("📈 Performance Metrics")
        if not trades_df.empty:
            m = strat.compute_performance_metrics(trades_df).iloc[0]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Trades", f"{int(m['Total Trades']):,}")
            c2.metric("Gross P&L", f"${m['Gross P&L (USD)']:,.2f}")
            c3.metric("Net P&L (after fees)", f"${m['Net P&L (USD)']:,.2f}")
            c4.metric("Total Fees", f"${m['Total Fees (USD)']:,.2f}")
            st.metric("Sharpe Ratio", m['Sharpe Ratio (daily)'])
            st.metric("Max Drawdown", f"{m['Max Drawdown (%)']}%")
            # Cumulative plot
            df_eq = trades_df.copy()
            df_eq['timestamp'] = pd.to_datetime(df_eq['timestamp'])
            df_eq = df_eq.sort_values('timestamp')
            df_eq['net_cash'] = df_eq.apply(lambda r: r['value']-r['fee'] if r['side']=='SELL' else -r['value']-r['fee'], axis=1)
            df_eq['cum_pnl'] = df_eq['net_cash'].cumsum()
            st.plotly_chart(px.line(df_eq, x='timestamp', y='cum_pnl', title="Cumulative Cash Flow (sells - buys)"), use_container_width=True)
            st.caption("Note: this chart goes negative when bots are accumulating inventory. That is expected for grid bots.")
        else:
            st.info("No trade data yet.")

    # === TAB 5: ERROR LOG ===
    with tab5:
        st.subheader("🚨 Error Observatory")
        if not error_df.empty:
            st.dataframe(error_df, use_container_width=True)
        else:
            st.success("✅ No errors logged.")

    # === TAB 6: PER-BOT STATS ===
    with tab6:
        st.subheader("🎯 Per-Bot Performance — FIFO Realized P&L + Inventory")
        st.caption("Realized P&L = profit on closed (matched) trades only. Inventory = coins still held.")
        
        if trades_df.empty:
            st.info("No trade data yet.")
        else:
            # Show all bot names from trades (for debugging)
            st.write("✅ Bots in trade history:", trades_df['bot_name'].unique().tolist())
            
            # Try to get FIFO stats
            fifo = strat.fifo_stats_all_bots(trades_df)
            
            if not fifo:
                st.warning("⚠️ FIFO stats returned empty. Showing raw trade summary instead.")
                raw = trades_df.groupby('bot_name').agg({
                    'side': 'count',
                    'value': 'sum'
                }).reset_index()
                raw.columns = ['bot_name', 'Total Trades', 'Total Value']
                st.dataframe(raw.style.format({'Total Value': '${:,.2f}'}), use_container_width=True)
            else:
                rows = list(fifo.values())
                summary = pd.DataFrame(rows)[['bot_name','total_closed','wins','losses','win_rate','realized_pnl','orphaned_qty','orphaned_cost_basis']].rename(columns={
                    'total_closed':'Closed Trades','wins':'Wins','losses':'Losses','win_rate':'Win Rate %','realized_pnl':'Realized P&L','orphaned_qty':'Inventory Qty','orphaned_cost_basis':'Inventory Cost Basis'
                })
                st.dataframe(summary.style.format({
                    'Win Rate %':'{:.2f}%','Realized P&L':'${:,.2f}','Inventory Cost Basis':'${:,.2f}','Inventory Qty':'{:.6f}'
                }).map(lambda v: 'color:#00ff9d' if isinstance(v, float) and v > 0 else 'color:#ff4d4d' if isinstance(v, float) and v < 0 else '', subset=['Realized P&L']), use_container_width=True)
                st.divider()
                for bot_name, stats in fifo.items():
                    pnl = stats['realized_pnl']
                    icon = '🟢' if pnl >= 0 else '🔴'
                    with st.expander(f"{icon} {bot_name}  |  Realized P&L: {'+'if pnl>=0 else ''}${pnl:,.2f}  |  Win Rate: {stats['win_rate']}%", expanded=True):
                        mc1,mc2,mc3,mc4 = st.columns(4)
                        mc1.metric("Realized P&L", f"{'+'if pnl>=0 else ''}${pnl:,.2f}")
                        mc2.metric("Win Rate", f"{stats['win_rate']}%")
                        mc3.metric("Closed Trades", stats['total_closed'])
                        mc4.metric("Wins / Losses", f"{stats['wins']} W / {stats['losses']} L")
                        if stats['orphaned_qty'] > 0:
                            st.info(f"📦 Open Inventory: {stats['orphaned_qty']:.6f} units | Cost basis: ${stats['orphaned_cost_basis']:,.2f} | This is unsold inventory — NOT a realized loss.")
                        else:
                            st.success("✅ All positions closed — clean state")
                # Charts
                chart_data = pd.DataFrame(list(fifo.values()))
                st.plotly_chart(px.bar(chart_data, x='bot_name', y='realized_pnl', title="Realized P&L per Bot (FIFO closed trades only)", color='realized_pnl', color_continuous_scale='RdYlGn'), use_container_width=True)
                fig_wl = go.Figure()
                fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['win_rate'], name='Win %', marker_color='#4ade80'))
                fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['losses']/chart_data['total_closed'].replace(0,1)*100, name='Loss %', marker_color='#f87171'))
                fig_wl.update_layout(title="Win / Loss % per Bot", barmode='group')
                st.plotly_chart(fig_wl, use_container_width=True)

    # === TAB 7: TRADE HISTORY ===
    with tab7:
        st.subheader("Filtered Trade History")
        if not trades_df.empty:
            bot_filter = st.multiselect("Filter by Bot", trades_df['bot_name'].unique().tolist(), key="history_filter")
            filtered = trades_df if not bot_filter else trades_df[trades_df['bot_name'].isin(bot_filter)]
            cols = ['timestamp','bot_name','exchange','symbol','side','price','quantity','value','fee','order_id']
            st.dataframe(filtered[cols].style.format({'price':'{:.6f}','quantity':'{:.4f}','value':'${:.2f}','fee':'${:.4f}'}), use_container_width=True)
            st.download_button("Export CSV", filtered.to_csv(index=False), "trades.csv", key="export_trades")
        else:
            st.info("No trades logged yet.")

    # === TAB 8: BACKTEST VS LIVE ===
    with tab8:
        st.subheader("📊 Backtest vs Live Comparison")
        live_metrics = strat.get_live_bot_metrics(trades_df)
        if backtest_df.empty:
            st.warning("No backtest data found.")
            with st.expander("How to add backtest data"):
                st.code("""INSERT INTO backtest_results (bot_name, strategy_name, start_date, end_date, total_trades, net_profit, sharpe_ratio, max_drawdown_pct, win_rate)
VALUES ('alpaca_hybrid_bot', 'MeanReversion_v1', '2024-01-01', '2024-12-31', 150, 1250.50, 1.2, 8.5, 55.0);""", language='sql')
        elif not live_metrics.empty:
            latest = backtest_df.sort_values('created_at', ascending=False).drop_duplicates('bot_name')
            merged = pd.merge(latest, live_metrics, on='bot_name', how='outer')
            dcols = ['bot_name','net_profit','live_net_profit','sharpe_ratio','live_sharpe','max_drawdown_pct','live_max_drawdown','win_rate','live_win_rate']
            ren = merged[dcols].rename(columns={'net_profit':'Backtest Net P&L','live_net_profit':'Live Net P&L','sharpe_ratio':'Backtest Sharpe','live_sharpe':'Live Sharpe','max_drawdown_pct':'Backtest Max DD %','live_max_drawdown':'Live Max DD %','win_rate':'Backtest Win Rate %','live_win_rate':'Live Win Rate %'})
            st.dataframe(ren.style.format({'Backtest Net P&L':'${:.2f}','Live Net P&L':'${:.2f}','Backtest Sharpe':'{:.2f}','Live Sharpe':'{:.2f}','Backtest Max DD %':'{:.2f}%','Live Max DD %':'{:.2f}%','Backtest Win Rate %':'{:.2f}%','Live Win Rate %':'{:.2f}%'}).map(lambda v: 'color:green' if isinstance(v,(int,float)) and v>0 else 'color:red' if isinstance(v,(int,float)) and v<0 else '', subset=['Live Net P&L']), use_container_width=True)

    # === TAB 9: BOT P&L COMPARISON ===
    with tab9:
        st.subheader("📈 Cumulative Cash Flow per Bot")
        st.caption("Negative slope = bot accumulating inventory. Positive slope = selling inventory for profit.")
        if not trades_df.empty:
            df = trades_df.copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['net_cash'] = df.apply(lambda r: r['value']-r['fee'] if r['side']=='SELL' else -r['value']-r['fee'], axis=1)
            df = df.sort_values(['bot_name','timestamp'])
            df['cum_pnl'] = df.groupby('bot_name')['net_cash'].cumsum()
            st.plotly_chart(px.line(df, x='timestamp', y='cum_pnl', color='bot_name', title="Per-Bot Cumulative Cash Flow", labels={'cum_pnl':'Cash Flow (USD)'}), use_container_width=True)
            bots = df['bot_name'].unique().tolist()
            sel = st.multiselect("Filter bots", bots, default=bots, key="bot_line_filter")
            if sel:
                st.plotly_chart(px.line(df[df['bot_name'].isin(sel)], x='timestamp', y='cum_pnl', color='bot_name', title="Filtered"), use_container_width=True)
        else:
            st.info("No trade data yet.")

    # === TAB 10: FIFO DEBUGGER ===
    with tab10:
        st.subheader("🧪 FIFO Debugger")
        if trades_df.empty:
            st.info("No trades found.")
        else:
            sel_bot = st.selectbox("Select Bot", trades_df['bot_name'].unique(), key="debug_bot")
            debug_df, orphaned = strat.get_fifo_debug(sel_bot, trades_df)
            if orphaned > 0:
                st.error(f"⚠️ Orphaned qty: {orphaned:.6f}")
            else:
                st.success("✅ No orphaned positions")
            if debug_df.empty:
                st.info("No matched BUY→SELL trades yet.")
            else:
                st.dataframe(debug_df, use_container_width=True)
                debug_df['cum_pnl'] = debug_df['pnl'].cumsum()
                st.plotly_chart(px.line(debug_df, x='sell_time', y='cum_pnl', title="Cumulative FIFO P&L"), use_container_width=True)

if __name__ == "__main__":
    main()
