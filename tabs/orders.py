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
