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
