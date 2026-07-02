
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
