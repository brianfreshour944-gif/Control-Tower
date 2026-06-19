import streamlit as st
import database as db  # This is the new module

# Now your data loading becomes clean:
trades_df   = db.load_trades()
status_df   = db.get_bot_status()
