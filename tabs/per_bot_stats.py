"""Tab: Per-Bot Stats -- FIFO realized P&L + open inventory summary, per-bot expanders, charts.

NOTE: This view (and the FIFO Debugger tab) is driven entirely by `fifo`, the dict
returned by strategy.fifo_stats_all_bots(trades_df). A bot only appears here once it
has at least one row in the `trades` table -- bots that are RUNNING but have never had
an order successfully fill (e.g. rejected for insufficient balance) will not show up,
even though they exist in bot_status. This is expected with the current implementation,
not a rendering bug.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ui_helpers import style_plotly_fig


def render(fifo):
    """Render the Per-Bot Stats tab.

    Args:
        fifo: dict from strategy.fifo_stats_all_bots(trades_df), keyed by bot_name.
    """
    st.subheader("🎯 Per-Bot Performance — FIFO Realized P&L + Inventory")
    st.caption("Realized P&L = profit on closed (matched) trades only. Inventory = coins still held.")
    if not fifo:
        st.info("No trade data yet.")
    else:
        rows = list(fifo.values())
        summary = pd.DataFrame(rows)[['bot_name', 'total_closed', 'wins', 'losses', 'win_rate', 'realized_pnl', 'orphaned_qty', 'orphaned_cost_basis']].rename(columns={
            'total_closed': 'Closed Trades', 'wins': 'Wins', 'losses': 'Losses', 'win_rate': 'Win Rate %', 'realized_pnl': 'Realized P&L', 'orphaned_qty': 'Inventory Qty', 'orphaned_cost_basis': 'Inventory Cost Basis'
        })
        st.dataframe(summary.style.format({
            'Win Rate %': '{:.2f}%', 'Realized P&L': '${:,.2f}', 'Inventory Cost Basis': '${:,.2f}', 'Inventory Qty': '{:.6f}'
        }).map(lambda v: 'color:#10B981' if isinstance(v, float) and v > 0 else 'color:#F43F5E' if isinstance(v, float) and v < 0 else '', subset=['Realized P&L']), width='stretch')
        st.divider()
        for bot_name, stats in fifo.items():
            pnl = stats['realized_pnl']
            icon = '🟢' if pnl >= 0 else '🔴'
            with st.expander(f"{icon} {bot_name}  |  Realized P&L: {'+' if pnl >= 0 else ''}${pnl:,.2f}  |  Win Rate: {stats['win_rate']}%", expanded=True):
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Realized P&L", f"{'+' if pnl >= 0 else ''}${pnl:,.2f}")
                mc2.metric("Win Rate", f"{stats['win_rate']}%")
                mc3.metric("Closed Trades", stats['total_closed'])
                mc4.metric("Wins / Losses", f"{stats['wins']} W / {stats['losses']} L")
                if stats['orphaned_qty'] > 0:
                    st.info(f"📦 Open Inventory: {stats['orphaned_qty']:.6f} units | Cost basis: ${stats['orphaned_cost_basis']:,.2f} | This is unsold inventory — NOT a realized loss.")
                else:
                    st.success("✅ All positions closed — clean state")
        # Charts
        chart_data = pd.DataFrame(list(fifo.values()))
        fig_pnl_bar = px.bar(chart_data, x='bot_name', y='realized_pnl', title="Realized P&L per Bot", color='realized_pnl', color_continuous_scale='RdYlGn')
        st.plotly_chart(style_plotly_fig(fig_pnl_bar), width='stretch')

        fig_wl = go.Figure()
        fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['win_rate'], name='Win %', marker_color='#10B981'))
        fig_wl.add_trace(go.Bar(x=chart_data['bot_name'], y=chart_data['losses'] / chart_data['total_closed'].replace(0, 1) * 100, name='Loss %', marker_color='#F43F5E'))
        fig_wl.update_layout(title="Win / Loss % per Bot", barmode='group')
        st.plotly_chart(style_plotly_fig(fig_wl), width='stretch')
