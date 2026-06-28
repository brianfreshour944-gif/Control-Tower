
"""
ui_helpers.py

Small shared formatting/styling helpers used across the dashboard:
- HTML snippet builders for the custom metric boxes (colored_pnl, metric_box, white_val)
- Plotly figure theming (style_plotly_fig)
- DataFrame type/NaN cleanup before display (sanitize_df)

These have no Streamlit page logic of their own -- they're pure helpers called
from main.py and the tab modules in tabs/.
"""

import pandas as pd


# ---------- HTML metric box builders ----------

def colored_pnl(value):
    """Render a P&L value as green/red HTML based on sign."""
    cls = "profit" if value >= 0 else "loss"
    sign = "+" if value >= 0 else ""
    return f'<span class="custom-metric-value {cls}">{sign}${value:,.2f}</span>'


def metric_box(label, content_html):
    """Wrap a label + pre-rendered value HTML in the custom-metric card markup."""
    return f'<div class="custom-metric"><div class="custom-metric-label">{label}</div>{content_html}</div>'


def white_val(value, fmt="${:,.2f}"):
    """Render a neutral (non-colored) metric value, formatted with `fmt`."""
    return f'<div class="custom-metric-value" style="color:#F8FAFC">{fmt.format(value)}</div>'


# ---------- Plotly theming ----------

def style_plotly_fig(fig):
    """Apply the dashboard's dark theme styling to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#94A3B8",
        xaxis=dict(gridcolor="#1E293B", linecolor="#1E293B", zerolinecolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B", linecolor="#1E293B", zerolinecolor="#1E293B"),
        title_font=dict(size=16, color="#38BDF8", family="Inter, sans-serif"),
        legend=dict(bgcolor="rgba(15, 19, 28, 0.9)", bordercolor="#1E293B", borderwidth=1),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


# ---------- Data Sanitizer (fixed for ID columns) ----------

def sanitize_df(df, preserve_null_columns=None):
    """
    Normalize a DataFrame loaded from the DB before display:
    - Force ID-like columns to plain strings
    - Coerce other object columns to numeric where possible
    - Fill NaN in numeric columns with 0 (except columns listed in
      preserve_null_columns, where NaN/missing has real meaning and
      should NOT be turned into a misleading 0 -- e.g. starting_equity:
      "hasn't reported a balance yet" must stay distinguishable from
      "reported a balance of exactly $0")
    - Parse timestamp/date columns
    """
    if df.empty:
        return df
    df = df.copy()
    preserve_null_columns = set(preserve_null_columns or [])

    # Force ID columns to be plain strings (no fixed length)
    id_columns = ['id', 'order_id', 'bot_name', 'exchange', 'symbol']
    for col in id_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna('').str.strip().astype('string')

    # Convert other object columns to numeric if possible
    for col in df.columns:
        if df[col].dtype == 'object' and col not in id_columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass

    # Fill NaN in numeric columns with 0 and convert to float64,
    # except columns where NaN is meaningful and must be preserved.
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) and col not in preserve_null_columns:
            df[col] = df[col].fillna(0).astype('float64')

    # Convert timestamp columns
    for col in df.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')

    return df
