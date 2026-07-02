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
