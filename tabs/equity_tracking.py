"""Tab: Equity Tracking -- per-bot starting balance, live balance (each bot
reports its own real account equity into bot_status), calculated balance
(starting equity + realized P&L + current value of held inventory), and
the delta between live and calculated as a sanity check.

NOTE: Bots that share an exchange account with other bots (e.g. multiple
OKX bots on one account) cannot report a *real* live equity that's
specific to just that bot -- there's no way to attribute "this much of
the shared balance belongs to bot X" from the exchange side. For those
bots, only the calculated column will be meaningful; live_equity will
show as "not reporting" until/unless that bot is given its own isolated
account.
"""

import pandas as pd
import streamlit as st

import strategy as strat
from ui_helpers import colored_pnl


def render(trades_df, status_df):
    """Render the Equity Tracking tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
        status_df: DataFrame from db.get_bot_status(), sanitized.
    """
    st.subheader("💼 Equity Tracking per Bot")
    st.caption(
        "**Starting** = equity when the bot first reported in. **Live** = the bot's own "
        "real account equity, self-reported each loop (only meaningful for bots with their "
        "own isolated exchange account -- bots sharing an account with others can't report "
        "a number specific to just themselves). **Calculated** = starting + realized P&L + "
        "current value of held inventory, derived purely from trade history. A large delta "
        "between live and calculated is worth investigating (uncaptured fees, slippage, or "
        "a logging gap)."
    )

    if trades_df.empty and (status_df is None or status_df.empty):
        st.info("No trade or bot status data yet.")
        return

    fifo = strat.fifo_stats_all_bots(trades_df)

    all_symbols = sorted({
        symbol
        for bot_data in fifo.values()
        for symbol in bot_data.get('holdings', {}).keys()
    })
    current_prices = {}
    if all_symbols:
        import database as db
        current_prices = db.get_current_prices(all_symbols)

    equity_df = strat.compute_bot_equity(fifo, status_df, current_prices)

    if equity_df.empty:
        st.info("No bots have reported equity data yet.")
        return

    for _, row in equity_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['bot_name']}**")
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                if pd.notna(row['starting_equity']):
                    st.metric("Starting Balance", f"${row['starting_equity']:,.2f}")
                else:
                    st.metric("Starting Balance", "Not reported yet")

            with c2:
                if pd.notna(row['live_equity']):
                    st.metric("Live Balance", f"${row['live_equity']:,.2f}")
                    if pd.notna(row['live_equity_updated_at']):
                        st.caption(f"Last reported: {row['live_equity_updated_at']}")
                else:
                    st.metric("Live Balance", "Not reporting")
                    st.caption("Either shares an account with other bots, or hasn't reported yet.")

            with c3:
                if pd.notna(row['calculated_equity']):
                    st.metric("Calculated Balance", f"${row['calculated_equity']:,.2f}")
                    st.caption(f"Realized P&L: {'+' if row['realized_pnl'] >= 0 else ''}${row['realized_pnl']:,.2f} "
                              f"| Inventory: ${row['inventory_value']:,.2f}")
                else:
                    st.metric("Calculated Balance", "—")
                    st.caption("Needs a starting_equity report first.")

            with c4:
                if pd.notna(row['delta']):
                    st.metric("Live vs Calculated", f"${row['delta']:,.2f}",
                             delta=f"{'+' if row['delta'] >= 0 else ''}{row['delta']:,.2f}",
                             delta_color="off")
                    if abs(row['delta']) >= 5:
                        st.caption("⚠️ Worth investigating")
                else:
                    st.metric("Live vs Calculated", "—")

    with st.expander("View raw data"):
        st.dataframe(equity_df, width='stretch')
