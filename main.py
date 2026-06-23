
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from datetime import datetime, date
from sqlalchemy import text
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from streamlit_option_menu import option_menu

# Import our modules
import database as db
import strategy as strat

# Page config
st.set_page_config(
    page_title="Trading Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CLEAN LIGHT CSS ==========
st.markdown("""
<style>
    /* ----- General Light Background ----- */
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }

    /* ----- Metric Cards (Clean white with shadow) ----- */
    .custom-metric {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
        transition: box-shadow 0.2s;
    }
    .custom-metric:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
    }
    .custom-metric-label {
        color: #6b7280 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .custom-metric-value {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
    }

    /* ----- P&L Colors ----- */
    .profit { color: #16a34a !important; }
    .loss { color: #dc2626 !important; }

    /* ----- Sidebar (Light) ----- */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e5e7eb !important;
    }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span {
        color: #1f2937 !important;
    }

    /* ----- Headings ----- */
    h1, h2, h3, .stSubheader {
        color: #111827 !important;
        font-weight: 600 !important;
    }
    h1 {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        background: none !important;
    }

    /* ----- Buttons ----- */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        background: #ffffff !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
        transition: all 0.15s;
    }
    .stButton>button:hover {
        border-color: #3b82f6 !important;
        background: #f8fafc !important;
    }
    .stButton>button[kind="primary"] {
        background: #3b82f6 !important;
        border: none !important;
        color: white !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: #2563eb !important;
    }

    /* ----- Progress Bar ----- */
    .stProgress > div > div > div > div {
        background: #3b82f6 !important;
    }

    /* ----- Inputs / Selects ----- */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input, 
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
    }

    /* ----- AgGrid (Light Theme) ----- */
    .ag-theme-alpine {
        --ag-background-color: #ffffff !important;
        --ag-header-background-color: #f9fafb !important;
        --ag-foreground-color: #111827 !important;
        --ag-border-color: #e5e7eb !important;
        --ag-row-hover-color: #f3f4f6 !important;
        --ag-selected-row-background-color: #eff6ff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
    }

    /* ----- Cash Flow Banner ----- */
    .cash-flow-banner {
        background: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        margin-bottom: 0.5rem;
        color: #111827 !important;
    }

    /* ----- Alerts ----- */
    .stAlert {
        background: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
    }

    /* ----- Scrollbar ----- */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

    /* ----- Option Menu (Light override) ----- */
    .nav-link-selected {
        background-color: #eff6ff !important;
        color: #1f2937 !important;
        border-left: 3px solid #3b82f6 !important;
    }
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
    return f'<div class="custom-metric-value" style="color:#111827">{fmt.format(value)}</div>'

# ---------- Data Sanitizer ----------
def sanitize_df(df):
    if df.empty:
        return df
    df = df.copy()
    id_columns = ['id', 'order_id', 'bot_name', 'exchange', 'symbol']
    for col in id_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna('')
    for col in df.columns:
        if df[col].dtype == 'object' and col not in id_columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0).astype('float64')
    for col in df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

# ---------- Main ----------
def main():
    st.title("🚀 Trading Command Center")
    st.caption("**Professional Multi-Exchange Trading Operations Dashboard**")

    # Session State
    if "auto_refresh" not in st.session_state: st.session_state.auto_refresh = False
    if "last_refresh" not in st.session_state: st.session_state.last_refresh = datetime.now()
    if "confirm_clear_errors" not in st.session_state: st.session_state.confirm_clear_errors = False
    if "confirm_reset" not in st.session_state: st.session_state.confirm_reset = False

    # ====== SIDEBAR ======
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/48/000000/trading-bot.png", width=40)
        st.markdown("### APEX DASHBOARD")

        menu_choice = option_menu(
            menu_title=None,
            options=[
                "🤖 Bot Control",
                "💰 Portfolio",
                "📋 Open Orders",
                "📈 Performance",
                "🚨 Error Log",
                "🎯 Per-Bot Stats",
                "📜 Trade History",
                "📊 Backtest vs Live",
                "📈 Bot P&L Comparison",
                "🧪 FIFO Debugger",
                "📊 Daily P&L per Bot"
            ],
            icons=[
                "robot", "pie-chart", "list-task", "graph-up-arrow",
                "exclamation-triangle", "target", "clock-history",
                "table", "graph-up", "flask", "calendar-event"
            ],
            menu_icon="app-indicator",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#3b82f6", "font-size": "18px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "2px 0px",
                    "border-radius": "6px",
                    "padding": "8px 12px",
                    "color": "#4b5563",
                },
                "nav-link-selected": {
                    "background-color": "#eff6ff",
                    "color": "#1f2937",
                    "font-weight": "600",
                    "border-left": "3px solid #3b82f6",
                },
            },
            key="menu_widget",
        )

        st.divider()
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

        # Reset Button
        if st.button("🗑️ Reset All Trading Stats", type="secondary", width='stretch'):
            st.session_state.confirm_reset = True
        if st.session_state.confirm_reset:
            st.warning("⚠️ **ARE YOU SURE?** This will DELETE ALL TRADES!")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ YES", type="primary", width='stretch'):
                    db.reset_all_trading_stats()
                    st.success("✅ Reset complete!")
                    st.session_state.confirm_reset = False
                    st.rerun()
            with c2:
                if st.button("❌ Cancel", width='stretch'):
                    st.session_state.confirm_reset = False
                    st.rerun()
        st.divider()

        if st.button("🛑 EMERGENCY STOP ALL", type="secondary", width='stretch'):
            if st.checkbox("Confirm stop all bots"):
                with db.get_db_engine().connect() as conn:
                    conn.execute(text("UPDATE bot_status SET status = 'STOP'"))
                    conn.commit()
                st.success("All bots stopped")
                st.rerun()

    # ====== LOAD DATA ======
    trades_df = db.load_trades()
    status_df = db.get_bot_status()
    error_df = db.load_errors()
    df_pos = db.get_unified_portfolio()
    live_orders = db.get_live_exchange_orders()
    backtest_df = db.get_backtest_results()
    db_orders = db.get_open_orders_from_db()

    trades_df = sanitize_df(trades_df)
    status_df = sanitize_df(status_df)
    error_df = sanitize_df(error_df)
    df_pos = sanitize_df(df_pos)
    live_orders = sanitize_df(live_orders)
    backtest_df = sanitize_df(backtest_df)
    db_orders = sanitize_df(db_orders)

    # ====== METRICS ======
    fifo = strat.fifo_stats_all_bots(trades_df)
    realized_pnl = sum(v['realized_pnl'] for v in fifo.values())
    inventory_cost = sum(v['orphaned_cost_basis'] for v in fifo.values())
    unrealized_pnl = df_pos['unrealized_pl'].sum() if not df_pos.empty else 0.0
    total_pnl = realized_pnl + unrealized_pnl
    daily_cash_flow = strat.get_daily_realized_pnl(trades_df)
    active_bots = len(status_df[status_df['status'] == 'RUNNING']) if not status_df.empty else 0
    portfolio_val = df_pos['market_value'].sum() if not df_pos.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.markdown(metric_box("Total Trades", white_val(len(trades_df), "{:,.0f}")), unsafe_allow_html=True)
    with c2: st.markdown(metric_box("Realized P&L", colored_pnl(realized_pnl)), unsafe_allow_html=True)
    with c3: st.markdown(metric_box("Unrealized P&L", colored_pnl(unrealized_pnl)), unsafe_allow_html=True)
    with c4: st.markdown(metric_box("Total P&L", colored_pnl(total_pnl)), unsafe_allow_html=True)
    with c5: st.markdown(metric_box("Active Bots", white_val(active_bots, "{:,.0f}")), unsafe_allow_html=True)
    with c6: st.markdown(metric_box("Portfolio Value", white_val(portfolio_val)), unsafe_allow_html=True)

    flow_color = "#16a34a" if daily_cash_flow >= 0 else "#dc2626"
    sign = "+" if daily_cash_flow >= 0 else ""
    st.markdown(
        f'<div class="cash-flow-banner">'
        f'📅 Today\'s cash flow: <span style="color:{flow_color};font-weight:600">'
        f'{sign}${daily_cash_flow:,.2f}</span> &nbsp;'
        f'<span style="color:#6b7280;font-size:0.85rem">'
        f'(negative = buying inventory – held: ${inventory_cost:,.2f})</span>'
        f'</div>', unsafe_allow_html=True)
    st.divider()

    # ====== RENDER CONTENT ======
    choice = menu_choice

    # ------------------------------------------------
    if choice == "🤖 Bot Control":
        with st.container():
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
                gb = GridOptionsBuilder.from_dataframe(status_df[['bot_name', 'status', 'daily_loss', 'daily_loss_limit']])
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_default_column(editable=False, filter=True, sortable=True)
                grid_options = gb.build()
                AgGrid(status_df[['bot_name', 'status', 'daily_loss', 'daily_loss_limit']],
                       gridOptions=grid_options, theme='alpine', height=300, fit_columns_on_grid_load=True)
            else:
                st.warning("No bot status records found.")

    # ------------------------------------------------
    elif choice == "💰 Portfolio":
        with st.container():
            st.subheader("Live Portfolio & Unrealized P&L")
            if not df_pos.empty:
                fig = px.pie(df_pos, values='market_value', names='symbol', hole=0.4, title="Asset Allocation")
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                st.plotly_chart(fig, width='stretch')
                gb = GridOptionsBuilder.from_dataframe(df_pos[['source','symbol','quantity','avg_entry','current_price','market_value','unrealized_pl']])
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_column("unrealized_pl", cellRenderer=JsCode("""
                    function(params) {
                        if (params.value > 0) return '<span style="color:#16a34a;">+$' + params.value.toFixed(2) + '</span>';
                        else if (params.value < 0) return '<span style="color:#dc2626;">-$' + Math.abs(params.value).toFixed(2) + '</span>';
                        else return '$0.00';
                    }
                """))
                grid_options = gb.build()
                AgGrid(df_pos[['source','symbol','quantity','avg_entry','current_price','market_value','unrealized_pl']],
                       gridOptions=grid_options, theme='alpine', height=350, fit_columns_on_grid_load=True,
                       allow_unsafe_jscode=True)
                st.metric("Total Portfolio Value", f"${df_pos['market_value'].sum():,.2f}", delta=f"${df_pos['unrealized_pl'].sum():,.2f} unrealized")
            else:
                st.info("No open positions found.")

    # ------------------------------------------------
    elif choice == "📋 Open Orders":
        with st.container():
            st.subheader("📋 Open Orders")
            if not db_orders.empty:
                cols = ['order_id','bot_name','symbol','side','price']
                if 'created_at' in db_orders.columns: cols.append('created_at')
                gb = GridOptionsBuilder.from_dataframe(db_orders[cols])
                gb.configure_pagination(paginationAutoPageSize=True)
                grid_options = gb.build()
                AgGrid(db_orders[cols], gridOptions=grid_options, theme='alpine', height=300, fit_columns_on_grid_load=True)
            else:
                st.info("No bot-tracked open orders.")
            st.divider()
            st.subheader("Live Exchange Orders")
            if not live_orders.empty:
                gb = GridOptionsBuilder.from_dataframe(live_orders[['exchange','id','symbol','side','type','qty','limit_price','bot_name']])
                gb.configure_pagination(paginationAutoPageSize=True)
                grid_options = gb.build()
                AgGrid(live_orders[['exchange','id','symbol','side','type','qty','limit_price','bot_name']],
                       gridOptions=grid_options, theme='alpine', height=300, fit_columns_on_grid_load=True)
                sel_id = st.selectbox("Select order to cancel", live_orders['id'].tolist(), key="cancel_select")
                if st.button("Cancel Selected Order"):
                    st.warning("Cancellation code not implemented in this snippet.")
            else:
                st.success("No live open orders.")

    # ------------------------------------------------
    elif choice == "📈 Performance":
        with st.container():
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
                df_eq = trades_df.copy()
                df_eq['timestamp'] = pd.to_datetime(df_eq['timestamp'])
                df_eq = df_eq.sort_values('timestamp')
                df_eq['net_cash'] = df_eq.apply(lambda r: r['value']-r['fee'] if r['side']=='SELL' else -r['value']-r['fee'], axis=1)
                df_eq['cum_pnl'] = df_eq['net_cash'].cumsum()
                fig = px.line(df_eq, x='timestamp', y='cum_pnl', title="Cumulative Cash Flow")
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                st.plotly_chart(fig, width='stretch')
                st.caption("Note: this chart goes negative when bots are accumulating inventory. That is expected for grid bots.")
            else:
                st.info("No trade data yet.")

    # ------------------------------------------------
    elif choice == "🚨 Error Log":
        with st.container():
            st.subheader("🚨 Error Observatory")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️ Clear All Errors", type="secondary", width='stretch'):
                    st.session_state.confirm_clear_errors = True
            if st.session_state.get("confirm_clear_errors", False):
                st.warning("⚠️ Are you sure you want to DELETE ALL error logs?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ YES, Delete All", type="primary", width='stretch'):
                        db.clear_errors()
                        st.success("✅ All errors cleared!")
                        st.session_state.confirm_clear_errors = False
                        st.rerun()
                with c2:
                    if st.button("❌ Cancel", width='stretch'):
                        st.session_state.confirm_clear_errors = False
                        st.rerun()
                st.divider()
            if not error_df.empty:
                gb = GridOptionsBuilder.from_dataframe(error_df)
                gb.configure_pagination(paginationAutoPageSize=True)
                grid_options = gb.build()
                AgGrid(error_df, gridOptions=grid_options, theme='alpine', height=400, fit_columns_on_grid_load=True)
            else:
                st.success("✅ No errors logged.")

    # ------------------------------------------------
    elif choice == "🎯 Per-Bot Stats":
        with st.container():
            st.subheader("🎯 Per-Bot Performance — FIFO Realized P&L + Inventory")
            st.caption("Realized P&L = profit on closed (matched) trades only. Inventory = coins still held.")
            if trades_df.empty:
                st.info("No trade data yet.")
            else:
                fifo = strat.fifo_stats_all_bots(trades_df)
                if not fifo:
                    st.warning("⚠️ FIFO stats returned empty. Showing raw trade summary instead.")
                    raw = trades_df.groupby('bot_name').agg({'side': 'count', 'value': 'sum'}).reset_index()
                    raw.columns = ['bot_name', 'Total Trades', 'Total Value']
                    st.dataframe(raw.style.format({'Total Value': '${:,.2f}'}), width='stretch')
                else:
                    rows = list(fifo.values())
                    summary = pd.DataFrame(rows)[['bot_name','total_closed','wins','losses','win_rate','realized_pnl','orphaned_qty','orphaned_cost_basis']].rename(columns={
                        'total_closed':'Closed Trades','wins':'Wins','losses':'Losses','win_rate':'Win Rate %','realized_pnl':'Realized P&L','orphaned_qty':'Inventory Qty','orphaned_cost_basis':'Inventory Cost Basis'
                    })
                    gb = GridOptionsBuilder.from_dataframe(summary)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    gb.configure_column("Realized P&L", cellRenderer=JsCode("""
                        function(params) {
                            if (params.value > 0) return '<span style="color:#16a34a;">+$' + params.value.toFixed(2) + '</span>';
                            else if (params.value < 0) return '<span style="color:#dc2626;">-$' + Math.abs(params.value).toFixed(2) + '</span>';
                            else return '$0.00';
                        }
                    """))
                    grid_options = gb.build()
                    AgGrid(summary, gridOptions=grid_options, theme='alpine', height=400, fit_columns_on_grid_load=True,
                           allow_unsafe_jscode=True)
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
                    chart_data = pd.DataFrame(list(fifo.values()))
                    fig = px.bar(chart_data, x='bot_name', y='realized_pnl', title="Realized P&L per Bot", color='realized_pnl', color_continuous_scale='RdYlGn')
                    fig.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                    st.plotly_chart(fig, width='stretch')
                    fig_wl = go.Figure()
                    fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['win_rate'], name='Win %', marker_color='#4ade80'))
                    fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['losses']/chart_data['total_closed'].replace(0,1)*100, name='Loss %', marker_color='#f87171'))
                    fig_wl.update_layout(title="Win / Loss % per Bot", barmode='group', plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                    st.plotly_chart(fig_wl, width='stretch')

    # ------------------------------------------------
    elif choice == "📜 Trade History":
        with st.container():
            st.subheader("Filtered Trade History")
            if not trades_df.empty:
                bot_filter = st.multiselect("Filter by Bot", trades_df['bot_name'].unique().tolist(), key="history_filter")
                filtered = trades_df if not bot_filter else trades_df[trades_df['bot_name'].isin(bot_filter)]
                cols = ['timestamp','bot_name','exchange','symbol','side','price','quantity','value','fee','order_id']
                gb = GridOptionsBuilder.from_dataframe(filtered[cols])
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_default_column(filter=True, sortable=True)
                gb.configure_column("price", type=["numericColumn"])
                gb.configure_column("quantity", type=["numericColumn"])
                grid_options = gb.build()
                AgGrid(filtered[cols], gridOptions=grid_options, theme='alpine', height=450, fit_columns_on_grid_load=True)
                st.download_button("Export CSV", filtered.to_csv(index=False), "trades.csv", key="export_trades")
            else:
                st.info("No trades logged yet.")

    # ------------------------------------------------
    elif choice == "📊 Backtest vs Live":
        with st.container():
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
                gb = GridOptionsBuilder.from_dataframe(ren)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_column("Live Net P&L", cellRenderer=JsCode("""
                    function(params) {
                        if (params.value > 0) return '<span style="color:#16a34a;">+$' + params.value.toFixed(2) + '</span>';
                        else if (params.value < 0) return '<span style="color:#dc2626;">-$' + Math.abs(params.value).toFixed(2) + '</span>';
                        else return '$0.00';
                    }
                """))
                grid_options = gb.build()
                AgGrid(ren, gridOptions=grid_options, theme='alpine', height=400, fit_columns_on_grid_load=True,
                       allow_unsafe_jscode=True)

    # ------------------------------------------------
    elif choice == "📈 Bot P&L Comparison":
        with st.container():
            st.subheader("📈 Cumulative Cash Flow per Bot")
            st.caption("Negative slope = bot accumulating inventory. Positive slope = selling inventory for profit.")
            if not trades_df.empty:
                df = trades_df.copy()
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['net_cash'] = df.apply(lambda r: r['value']-r['fee'] if r['side']=='SELL' else -r['value']-r['fee'], axis=1)
                df = df.sort_values(['bot_name','timestamp'])
                df['cum_pnl'] = df.groupby('bot_name')['net_cash'].cumsum()
                fig = px.line(df, x='timestamp', y='cum_pnl', color='bot_name', title="Per-Bot Cumulative Cash Flow")
                fig.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                st.plotly_chart(fig, width='stretch')
                bots = df['bot_name'].unique().tolist()
                sel = st.multiselect("Filter bots", bots, default=bots, key="bot_line_filter")
                if sel:
                    fig2 = px.line(df[df['bot_name'].isin(sel)], x='timestamp', y='cum_pnl', color='bot_name', title="Filtered")
                    fig2.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                    st.plotly_chart(fig2, width='stretch')
            else:
                st.info("No trade data yet.")

    # ------------------------------------------------
    elif choice == "🧪 FIFO Debugger":
        with st.container():
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
                    gb = GridOptionsBuilder.from_dataframe(debug_df)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    grid_options = gb.build()
                    AgGrid(debug_df, gridOptions=grid_options, theme='alpine', height=350, fit_columns_on_grid_load=True)
                    debug_df['cum_pnl'] = debug_df['pnl'].cumsum()
                    fig = px.line(debug_df, x='sell_time', y='cum_pnl', title="Cumulative FIFO P&L")
                    fig.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                    st.plotly_chart(fig, width='stretch')

    # ------------------------------------------------
    elif choice == "📊 Daily P&L per Bot":
        with st.container():
            st.subheader("📊 Daily Realized P&L per Bot")
            st.caption("Positive = net profit from sells; negative = net buying (inventory accumulation).")
            if trades_df.empty:
                st.info("No trade data available.")
            else:
                daily_df = strat.get_daily_pnl_per_bot(trades_df)
                if daily_df.empty:
                    st.info("No daily data.")
                else:
                    fig = px.bar(daily_df, x='date', y='daily_pnl', color='bot_name', title="Daily P&L by Bot")
                    fig.update_layout(plot_bgcolor='rgba(255,255,255,0)', paper_bgcolor='rgba(255,255,255,0)')
                    st.plotly_chart(fig, width='stretch')
                    pivot = daily_df.pivot(index='date', columns='bot_name', values='daily_pnl').fillna(0)
                    st.dataframe(pivot.style.format("{:,.2f}").map(lambda v: 'color: #16a34a' if v > 0 else 'color: #dc2626' if v < 0 else '', subset=pd.IndexSlice[:, :]), width='stretch')
                    st.subheader("Total Realized P&L per Bot")
                    total_per_bot = daily_df.groupby('bot_name')['daily_pnl'].sum().reset_index()
                    total_per_bot.columns = ['bot_name', 'Total P&L']
                    st.dataframe(total_per_bot.style.format({'Total P&L': '${:,.2f}'}).map(lambda v: 'color: #16a34a' if v > 0 else 'color: #dc2626' if v < 0 else '', subset=['Total P&L']), width='stretch')

if __name__ == "__main__":
    main()
