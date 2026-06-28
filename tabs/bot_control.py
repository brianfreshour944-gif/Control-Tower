
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
