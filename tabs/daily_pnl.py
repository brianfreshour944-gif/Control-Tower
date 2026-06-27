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
