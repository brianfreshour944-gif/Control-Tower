"""Tab: Trade History -- filterable, exportable trade log."""

import streamlit as st


def render(trades_df):
    """Render the Trade History tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
    """
    st.subheader("Filtered Trade History")
    if not trades_df.empty:
        try:
            bot_filter = st.multiselect("Filter by Bot", trades_df['bot_name'].unique().tolist(), key="history_filter")
            filtered = trades_df if not bot_filter else trades_df[trades_df['bot_name'].isin(bot_filter)]
            cols = ['timestamp', 'bot_name', 'exchange', 'symbol', 'side', 'price', 'quantity', 'value', 'fee', 'order_id']
            missing = [c for c in cols if c not in filtered.columns]
            if missing:
                st.error(f"trades table is missing expected columns: {missing}")
                st.caption("Columns actually present:")
                st.write(filtered.columns.tolist())
                st.dataframe(filtered, width='stretch')
            else:
                st.dataframe(filtered[cols].style.format({'price': '{:.6f}', 'quantity': '{:.4f}', 'value': '${:.2f}', 'fee': '${:.4f}'}), width='stretch')
                st.download_button("Export CSV", filtered.to_csv(index=False), "trades.csv", key="export_trades")
        except Exception as e:
            import traceback
            st.error(f"Could not render trade history: {e}")
            st.code(traceback.format_exc())
            st.dataframe(trades_df, width='stretch')
    else:
        st.info("No trades logged yet.")
