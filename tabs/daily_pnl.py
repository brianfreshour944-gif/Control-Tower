
"""Tab: Backtest vs Live -- compares stored backtest_results against live trade metrics."""

import pandas as pd
import streamlit as st

import strategy as strat


def render(trades_df, backtest_df):
    """Render the Backtest vs Live tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
        backtest_df: DataFrame from db.get_backtest_results(), sanitized.
    """
    st.subheader("📊 Backtest vs Live Comparison")
    live_metrics = strat.get_live_bot_metrics(trades_df)
    if backtest_df.empty:
        st.warning("No backtest data found.")
        with st.expander("How to add backtest data"):
            st.code("""INSERT INTO backtest_results (bot_name, strategy_name, start_date, end_date, total_trades, net_profit, sharpe_ratio, max_drawdown_pct, win_rate)
VALUES ('alpaca_hybrid_bot', 'MeanReversion_v1', '2024-01-01', '2024-12-31', 150, 1250.50, 1.2, 8.5, 55.0);""", language='sql')
    elif live_metrics.empty:
        st.info("Backtest data found, but no live trades yet to compare against.")
        st.dataframe(backtest_df, width='stretch')
    else:
        try:
            latest = backtest_df.sort_values('created_at', ascending=False).drop_duplicates('bot_name')
            merged = pd.merge(latest, live_metrics, on='bot_name', how='outer')
            dcols = ['bot_name', 'net_profit', 'live_net_profit', 'sharpe_ratio', 'live_sharpe', 'max_drawdown_pct', 'live_max_drawdown', 'win_rate', 'live_win_rate']
            missing = [c for c in dcols if c not in merged.columns]
            if missing:
                st.error(f"Missing expected columns after merge: {missing}")
                st.caption("Backtest bot_name values:")
                st.write(sorted(latest['bot_name'].unique().tolist()))
                st.caption("Live trades bot_name values:")
                st.write(sorted(live_metrics['bot_name'].unique().tolist()))
            else:
                ren = merged[dcols].rename(columns={'net_profit': 'Backtest Net P&L', 'live_net_profit': 'Live Net P&L', 'sharpe_ratio': 'Backtest Sharpe', 'live_sharpe': 'Live Sharpe', 'max_drawdown_pct': 'Backtest Max DD %', 'live_max_drawdown': 'Live Max DD %', 'win_rate': 'Backtest Win Rate %', 'live_win_rate': 'Live Win Rate %'})
                st.dataframe(ren.style.format({'Backtest Net P&L': '${:.2f}', 'Live Net P&L': '${:.2f}', 'Backtest Sharpe': '{:.2f}', 'Live Sharpe': '{:.2f}', 'Backtest Max DD %': '{:.2f}%', 'Live Max DD %': '{:.2f}%', 'Backtest Win Rate %': '{:.2f}%', 'Live Win Rate %': '{:.2f}%'}).map(lambda v: 'color:green' if isinstance(v, (int, float)) and v > 0 else 'color:red' if isinstance(v, (int, float)) and v < 0 else '', subset=['Live Net P&L']), width='stretch')
        except Exception as e:
            st.error(f"Could not render backtest vs live comparison: {e}")
            st.caption("Raw backtest data:")
            st.dataframe(backtest_df, width='stretch')
            st.caption("Raw live metrics:")
            st.dataframe(live_metrics, width='stretch')

"""Tab: Bot Control -- start/stop a bot, manage daily loss limit, edit bot config JSON."""

import json
import streamlit as st
from sqlalchemy import text

import database as db


def render(status_df):
    """Render the Bot Control tab.

    Args:
        status_df: DataFrame from db.get_bot_status(), sanitized.
    """
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
        st.dataframe(status_df[['bot_name', 'status', 'daily_loss', 'daily_loss_limit']], width='stretch')
    else:
        st.warning("No bot status records found.")

"""Tab: Daily/Weekly P&L -- per-bot breakdown over time, showing both
Realized P&L (FIFO-matched profit, the more "honest" number) and Net Cash
Flow (raw money in/out, which swings when a bot is mid-way through buying
inventory it hasn't sold yet) side by side so the difference is visible
instead of being a footnote.
"""

import streamlit as st
import plotly.graph_objects as go

import strategy as strat
from ui_helpers import style_plotly_fig


def render(trades_df):
    """Render the Daily/Weekly P&L tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
    """
    st.subheader("🗓️ Daily / Weekly P&L per Bot")
    st.caption(
        "**Realized P&L** = FIFO-matched profit, dated to when a trade actually closed (the SELL). "
        "**Net Cash Flow** = raw money in/out that day -- it dips when a bot buys inventory and "
        "spikes when it later sells, even if no profit was made yet. Comparing the two shows "
        "whether a bot's apparent daily swing is real profit or just inventory movement."
    )

    if trades_df.empty:
        st.info("No trade data yet.")
        return

    bots = sorted(trades_df['bot_name'].dropna().unique().tolist())
    if not bots:
        st.info("No trade data yet.")
        return

    c1, c2 = st.columns([2, 1])
    with c1:
        selected_bots = st.multiselect("Bots", bots, default=bots, key="daily_pnl_bot_filter")
    with c2:
        granularity = st.radio("Granularity", ["Daily", "Weekly"], horizontal=True, key="daily_pnl_granularity")

    if not selected_bots:
        st.info("Select at least one bot.")
        return

    filtered = trades_df[trades_df['bot_name'].isin(selected_bots)]

    daily_realized = strat.get_daily_realized_pnl_per_bot(filtered)
    daily_cash = strat.get_daily_pnl_per_bot(filtered)

    if granularity == "Weekly":
        realized_view = strat.aggregate_to_weekly(daily_realized, ['realized_pnl', 'closed_trades'])
        cash_view = strat.aggregate_to_weekly(daily_cash, ['daily_pnl'])
        x_col = 'week_start'
        x_title = "Week of"
    else:
        realized_view = daily_realized
        cash_view = daily_cash
        x_col = 'date'
        x_title = "Date"

    if realized_view.empty and cash_view.empty:
        st.info("No closed trades or cash flow in the selected range yet.")
        return

    for bot in selected_bots:
        bot_realized = realized_view[realized_view['bot_name'] == bot] if not realized_view.empty else realized_view
        bot_cash = cash_view[cash_view['bot_name'] == bot] if not cash_view.empty else cash_view

        if bot_realized.empty and bot_cash.empty:
            continue

        fig = go.Figure()
        if not bot_cash.empty:
            fig.add_trace(go.Bar(
                x=bot_cash[x_col].astype(str), y=bot_cash['daily_pnl'],
                name="Net Cash Flow", marker_color='#475569',
            ))
        if not bot_realized.empty:
            fig.add_trace(go.Bar(
                x=bot_realized[x_col].astype(str), y=bot_realized['realized_pnl'],
                name="Realized P&L", marker_color='#38BDF8',
            ))
        fig.update_layout(barmode='group', xaxis_title=x_title, yaxis_title="USD",
                          xaxis_type='category', title=f"{bot} -- {granularity} P&L",
                          legend=dict(orientation="h", yanchor="top", y=-0.2, x=0))
        st.plotly_chart(style_plotly_fig(fig), width='stretch', key=f"daily_pnl_chart_{bot}")

        if not bot_realized.empty:
            total_realized = bot_realized['realized_pnl'].sum()
            total_closed = bot_realized['closed_trades'].sum()
            st.caption(f"Total realized P&L over selected range: "
                      f"{'+' if total_realized >= 0 else ''}${total_realized:,.2f} "
                      f"across {int(total_closed)} closed trades")

    with st.expander("View raw data"):
        st.markdown("**Realized P&L (FIFO)**")
        st.dataframe(realized_view, width='stretch')
        st.markdown("**Net Cash Flow**")
        st.dataframe(cash_view, width='stretch')

"""Tab: Error Log -- raw bot error rows from the bot_errors table."""

import streamlit as st


def render(error_df):
    """Render the Error Log tab.

    Args:
        error_df: DataFrame from db.load_errors(), sanitized.
    """
    st.subheader("🚨 Error Observatory")
    if not error_df.empty:
        st.dataframe(error_df, width='stretch')
    else:
        st.success("✅ No errors logged.")

"""Tab: FIFO Debugger -- per-bot matched BUY/SELL trade pairs and cumulative FIFO P&L."""

import streamlit as st
import plotly.express as px

import strategy as strat
from ui_helpers import style_plotly_fig


def render(trades_df):
    """Render the FIFO Debugger tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
    """
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
            st.dataframe(debug_df, width='stretch')
            debug_df['cum_pnl'] = debug_df['pnl'].cumsum()
            fig_fifo_debug = px.line(debug_df, x='sell_time', y='cum_pnl', title="Cumulative FIFO P&L")
            st.plotly_chart(style_plotly_fig(fig_fifo_debug), width='stretch')

"""Tab: Open Orders -- bot-tracked open orders (DB) and live exchange orders."""

import streamlit as st

import database as db


def render(db_orders, live_orders):
    """Render the Open Orders tab.

    Args:
        db_orders: DataFrame from db.get_open_orders_from_db(), sanitized.
        live_orders: DataFrame from db.get_live_exchange_orders(), sanitized.
    """
    st.subheader("📋 Open Orders")
    if not db_orders.empty:
        cols = ['order_id', 'bot_name', 'symbol', 'side', 'price']
        if 'created_at' in db_orders.columns:
            cols.append('created_at')
        st.dataframe(db_orders[cols], width='stretch')
    else:
        st.info("No bot-tracked open orders (status = 'OPEN').")
        try:
            all_orders = db.get_all_orders_debug() if hasattr(db, 'get_all_orders_debug') else None
        except Exception:
            all_orders = None
        if all_orders is not None and not all_orders.empty:
            with st.expander("Debug: all rows in bot_orders table"):
                st.dataframe(all_orders, width='stretch')
                st.caption(f"Distinct status values found: {sorted(all_orders['status'].dropna().unique().tolist())}")

    st.divider()
    st.subheader("Live Exchange Orders")
    if not live_orders.empty:
        st.dataframe(live_orders[['exchange', 'id', 'symbol', 'side', 'type', 'qty', 'limit_price', 'bot_name']], width='stretch')
        sel_id = st.selectbox("Select order to cancel", live_orders['id'].tolist(), key="cancel_select")
        if st.button("Cancel Selected Order"):
            st.warning("Cancellation code not implemented in this snippet.")
    else:
        st.success("No live open orders.")

"""Tab: Per-Bot Stats -- FIFO realized P&L + open inventory summary, per-bot expanders, charts.

NOTE: This view (and the FIFO Debugger tab) is driven entirely by `fifo`, the dict
returned by strategy.fifo_stats_all_bots(trades_df). A bot only appears here once it
has at least one row in the `trades` table -- bots that are RUNNING but have never had
an order successfully fill (e.g. rejected for insufficient balance) will not show up,
even though they exist in bot_status. This is expected with the current implementation,
not a rendering bug.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ui_helpers import style_plotly_fig


def render(fifo):
    """Render the Per-Bot Stats tab.

    Args:
        fifo: dict from strategy.fifo_stats_all_bots(trades_df), keyed by bot_name.
    """
    st.subheader("🎯 Per-Bot Performance — FIFO Realized P&L + Inventory")
    st.caption("Realized P&L = profit on closed (matched) trades only. Inventory = coins still held.")
    if not fifo:
        st.info("No trade data yet.")
    else:
        rows = list(fifo.values())
        summary = pd.DataFrame(rows)[['bot_name', 'total_closed', 'wins', 'losses', 'win_rate', 'realized_pnl', 'orphaned_qty', 'orphaned_cost_basis']].rename(columns={
            'total_closed': 'Closed Trades', 'wins': 'Wins', 'losses': 'Losses', 'win_rate': 'Win Rate %', 'realized_pnl': 'Realized P&L', 'orphaned_qty': 'Inventory Qty', 'orphaned_cost_basis': 'Inventory Cost Basis'
        })
        st.dataframe(summary.style.format({
            'Win Rate %': '{:.2f}%', 'Realized P&L': '${:,.2f}', 'Inventory Cost Basis': '${:,.2f}', 'Inventory Qty': '{:.6f}'
        }).map(lambda v: 'color:#10B981' if isinstance(v, float) and v > 0 else 'color:#F43F5E' if isinstance(v, float) and v < 0 else '', subset=['Realized P&L']), width='stretch')
        st.divider()
        for bot_name, stats in fifo.items():
            pnl = stats['realized_pnl']
            icon = '🟢' if pnl >= 0 else '🔴'
            with st.expander(f"{icon} {bot_name}  |  Realized P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f}  |  Win Rate: {stats['win_rate']}%", expanded=True):
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Realized P&L", f"{'+' if pnl >= 0 else ''}${pnl:,.2f}")
                mc2.metric("Win Rate", f"{stats['win_rate']}%")
                mc3.metric("Closed Trades", stats['total_closed'])
                mc4.metric("Wins / Losses", f"{stats['wins']} W / {stats['losses']} L")
                if stats['orphaned_qty'] > 0:
                    st.info(f"📦 Open Inventory: {stats['orphaned_qty']:.6f} units | Cost basis: ${stats['orphaned_cost_basis']:,.2f} | This is unsold inventory — NOT a realized loss.")
                else:
                    st.success("✅ All positions closed — clean state")
        # Charts
        chart_data = pd.DataFrame(list(fifo.values()))
        fig_pnl_bar = px.bar(chart_data, x='bot_name', y='realized_pnl', title="Realized P&L per Bot", color='realized_pnl', color_continuous_scale='RdYlGn')
        st.plotly_chart(style_plotly_fig(fig_pnl_bar), width='stretch')

        fig_wl = go.Figure()
        fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['win_rate'], name='Win %', marker_color='#10B981'))
        fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['losses'] / chart_data['total_closed'].replace(0, 1) * 100, name='Loss %', marker_color='#F43F5E'))
        fig_wl.update_layout(title="Win / Loss % per Bot", barmode='group')
        st.plotly_chart(style_plotly_fig(fig_wl), width='stretch')

"""Tabs: Performance (aggregate metrics + cumulative cash flow) and
Bot P&L Comparison (per-bot cumulative cash flow lines).

Grouped together because both are P&L-over-time charts built from trades_df.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

import strategy as strat
from ui_helpers import style_plotly_fig


def render_performance(trades_df):
    """Render the Performance tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
    """
    st.subheader("📈 Performance Metrics")
    if not trades_df.empty:
        m = strat.compute_performance_metrics(trades_df).iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trades", f"{int(m['Total Trades']):,}")
        c2.metric("Gross P&L", f"${m['Gross P&L (USD)']:,.2f}")
        c3.metric("Net P&L (after fees)", f"${m['Net P&L (USD)']:,.2f}")
        c4.metric("Total Fees", f"${m['Total Fees (USD)']:,.2f}")
        st.metric("Sharpe Ratio", m['Sharpe Ratio (daily)'])
        st.metric("Max Drawdown", f"{m['Max Drawdown (%)']}%")
        df_eq = trades_df.copy()
        df_eq['timestamp'] = pd.to_datetime(df_eq['timestamp'])
        df_eq = df_eq.sort_values('timestamp')
        df_eq['net_cash'] = df_eq.apply(lambda r: r['value'] - r['fee'] if r['side'] == 'SELL' else -r['value'] - r['fee'], axis=1)
        df_eq['cum_pnl'] = df_eq['net_cash'].cumsum()
        fig_cum = px.line(df_eq, x='timestamp', y='cum_pnl', title="Cumulative Cash Flow")
        st.plotly_chart(style_plotly_fig(fig_cum), width='stretch')
        st.caption("Note: this chart goes negative when bots are accumulating inventory.")
    else:
        st.info("No trade data yet.")


def render_bot_pnl_comparison(trades_df):
    """Render the Bot P&L Comparison tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
    """
    st.subheader("📈 Cumulative Cash Flow per Bot")
    st.caption("Negative slope = bot accumulating inventory. Positive slope = selling inventory for profit.")
    if not trades_df.empty:
        df = trades_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['net_cash'] = df.apply(lambda r: r['value'] - r['fee'] if r['side'] == 'SELL' else -r['value'] - r['fee'], axis=1)
        df = df.sort_values(['bot_name', 'timestamp'])
        df['cum_pnl'] = df.groupby('bot_name')['net_cash'].cumsum()
        fig_pnl_comp = px.line(df, x='timestamp', y='cum_pnl', color='bot_name', title="Per-Bot Cumulative Cash Flow")
        st.plotly_chart(style_plotly_fig(fig_pnl_comp), width='stretch')
        bots = df['bot_name'].unique().tolist()
        sel = st.multiselect("Filter bots", bots, default=bots, key="bot_line_filter")
        if sel:
            fig_pnl_filtered = px.line(df[df['bot_name'].isin(sel)], x='timestamp', y='cum_pnl', color='bot_name', title="Filtered")
            st.plotly_chart(style_plotly_fig(fig_pnl_filtered), width='stretch')
    else:
        st.info("No trade data yet.")

"""Tab: Portfolio -- live positions, asset allocation pie chart, unrealized P&L."""

import streamlit as st
import plotly.express as px

from ui_helpers import style_plotly_fig


def render(df_pos):
    """Render the Portfolio tab.

    Args:
        df_pos: DataFrame from db.get_unified_portfolio(), sanitized.
    """
    st.subheader("Live Portfolio & Unrealized P&L")
    if not df_pos.empty:
        fig_pie = px.pie(df_pos, values='market_value', names='symbol', hole=0.4, title="Asset Allocation")
        st.plotly_chart(style_plotly_fig(fig_pie), width='stretch')
        st.dataframe(df_pos[['source', 'symbol', 'quantity', 'avg_entry', 'current_price', 'market_value', 'unrealized_pl']]
                     .style.format({'quantity': '{:.4f}', 'avg_entry': '${:.2f}', 'current_price': '${:.2f}', 'market_value': '${:,.2f}', 'unrealized_pl': '${:,.2f}'}), width='stretch')
        st.metric("Total Portfolio Value", f"${df_pos['market_value'].sum():,.2f}", delta=f"${df_pos['unrealized_pl'].sum():,.2f} unrealized")
    else:
        st.info("No open positions found.")
