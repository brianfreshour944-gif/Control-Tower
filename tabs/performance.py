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
