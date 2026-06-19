import streamlit as st
import database as db
import strategy as strat # The new Brain

# Load data
trades_df = db.load_trades()

# Compute metrics
fifo_data = strat.fifo_stats_all_bots(trades_df)
performance = strat.compute_performance_metrics(trades_df)

# Now just render the results
st.dataframe(performance)
