
"""Tab: Backtest vs Live -- compares stored backtest_results against live trade metrics."""

import pandas as pd
import streamlit as st

import strategy as strat


def render(trades_df, backtest_df):
    """Render the Backtest vs Live tab.

    Args:
        trades_df: DataFrame from db.load_trades(), sanitized.
        backtest_df: DataFrame from db.get_backtest_results(), sanitized.
    """
    st.subheader("📊 Backtest vs Live Comparison")
    live_metrics = strat.get_live_bot_metrics(trades_df)
    if backtest_df.empty:
        st.warning("No backtest data found.")
        with st.expander("How to add backtest data"):
            st.code("""INSERT INTO backtest_results (bot_name, strategy_name, start_date, end_date, total_trades, net_profit, sharpe_ratio, max_drawdown_pct, win_rate)
VALUES ('alpaca_hybrid_bot', 'MeanReversion_v1', '2024-01-01', '2024-12-31', 150, 1250.50, 1.2, 8.5, 55.0);""", language='sql')
    elif live_metrics.empty:
        st.info("Backtest data found, but no live trades yet to compare against.")
        st.dataframe(backtest_df, width='stretch')
    else:
        try:
            latest = backtest_df.sort_values('created_at', ascending=False).drop_duplicates('bot_name')
            merged = pd.merge(latest, live_metrics, on='bot_name', how='outer')
            dcols = ['bot_name', 'net_profit', 'live_net_profit', 'sharpe_ratio', 'live_sharpe', 'max_drawdown_pct', 'live_max_drawdown', 'win_rate', 'live_win_rate']
            missing = [c for c in dcols if c not in merged.columns]
            if missing:
                st.error(f"Missing expected columns after merge: {missing}")
                st.caption("Backtest bot_name values:")
                st.write(sorted(latest['bot_name'].unique().tolist()))
                st.caption("Live trades bot_name values:")
                st.write(sorted(live_metrics['bot_name'].unique().tolist()))
            else:
                ren = merged[dcols].rename(columns={'net_profit': 'Backtest Net P&L', 'live_net_profit': 'Live Net P&L', 'sharpe_ratio': 'Backtest Sharpe', 'live_sharpe': 'Live Sharpe', 'max_drawdown_pct': 'Backtest Max DD %', 'live_max_drawdown': 'Live Max DD %', 'win_rate': 'Backtest Win Rate %', 'live_win_rate': 'Live Win Rate %'})
                st.dataframe(ren.style.format({'Backtest Net P&L': '${:.2f}', 'Live Net P&L': '${:.2f}', 'Backtest Sharpe': '{:.2f}', 'Live Sharpe': '{:.2f}', 'Backtest Max DD %': '{:.2f}%', 'Live Max DD %': '{:.2f}%', 'Backtest Win Rate %': '{:.2f}%', 'Live Win Rate %': '{:.2f}%'}).map(lambda v: 'color:green' if isinstance(v, (int, float)) and v > 0 else 'color:red' if isinstance(v, (int, float)) and v < 0 else '', subset=['Live Net P&L']), width='stretch')
        except Exception as e:
            st.error(f"Could not render backtest vs live comparison: {e}")
            st.caption("Raw backtest data:")
            st.dataframe(backtest_df, width='stretch')
            st.caption("Raw live metrics:")
            st.dataframe(live_metrics, width='stretch')
