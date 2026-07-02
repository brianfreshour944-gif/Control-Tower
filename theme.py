"""
theme.py

Custom dark-theme CSS for the Trading Command Center dashboard.
Call apply_theme() once near the top of main.py, right after st.set_page_config().

NOTE: Streamlit dataframes (st.dataframe) render their grid using glide-data-grid,
which paints cells onto an HTML canvas and uses internal hidden <div> elements for
column-width measurement and scroll virtualization. Do NOT add a broad selector like
  [data-testid="stDataFrame"] div, span, p, button, input, select, textarea { ... }
with !important color/background rules -- this was previously the cause of dataframe
columns/text disappearing or rendering blank, because it interfered with the grid
internal sizing logic. Style stDataFrame at the container/th/td level only.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ----- Comprehensive Dark Theme for Streamlit ----- */
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
    }

    /* ----- Sidebar Dark Styling ----- */
    [data-testid="stSidebar"] {
        background-color: #0F131C !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #E2E8F0 !important;
    }

    /* ----- Metrics Container Styling ----- */
    .custom-metric {
        background-color: #151A24;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: rgba(0, 0, 0, 0.2) 0px 4px 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .custom-metric:hover {
        transform: translateY(-2px);
        border-color: #38BDF8;
    }
    .custom-metric-label {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .custom-metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #E2E8F0 !important;
    }

    /* ----- Semantic Colors ----- */
    .profit { color: #10B981 !important; }
    .loss   { color: #F43F5E !important; }
    .neutral { color: #F59E0B !important; }

    /* ----- Title & Typography styling ----- */
    h1, h2, h3, h4, h5, h6, .stSubheader {
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        color: #E2E8F0 !important;
    }
    h1 {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* ----- Buttons Styling ----- */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }
    .stButton>button:hover {
        background-color: #1E293B !important;
        border-color: #38BDF8 !important;
    }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%) !important;
        border: none !important;
        color: white !important;
    }

    /* ----- Input Fields Styling ----- */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div,
    .stMultiSelect>div>div>div {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Dataframe Styling ----- */
    .dataframe, .stDataFrame {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }
    .dataframe th, .stDataFrame th {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #1E293B !important;
    }
    .dataframe td, .stDataFrame td {
        border: 1px solid #1E293B !important;
    }

    /* ----- AgGrid Dark Theme ----- */
    .ag-theme-alpine {
        --ag-background-color: #0B0E14 !important;
        --ag-header-background-color: #151A24 !important;
        --ag-foreground-color: #E2E8F0 !important;
        --ag-header-foreground-color: #38BDF8 !important;
        --ag-border-color: #1E293B !important;
        --ag-row-hover-color: #1E293B !important;
        --ag-selected-row-background-color: #38BDF820 !important;
        --ag-odd-row-background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
    }

    /* ----- Alerts & Notifications ----- */
    .stAlert {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }

    /* ----- Progress Bar ----- */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%) !important;
    }

    /* ----- Tabs Styling ----- */
    div[data-testid="stTabs"] button {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #94A3B8 !important;
        padding: 0.5rem 1rem !important;
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px 8px 0 0 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #38BDF8 !important;
        border-bottom-color: #38BDF8 !important;
        background-color: #1E293B !important;
    }

    /* ----- Status Banner ----- */
    .status-banner {
        background: #151A24;
        border-left: 4px solid #38BDF8;
        border-radius: 0 8px 8px 0;
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid #1E293B;
        border-left: 4px solid #38BDF8;
        color: #E2E8F0 !important;
    }

    /* ----- Scrollbar Styling ----- */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0B0E14; }
    ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #38BDF8; }

    /* ----- Checkbox & Radio ----- */
    .stCheckbox>label, .stRadio>label {
        color: #E2E8F0 !important;
    }

    /* ----- Expander ----- */
    .streamlit-expanderHeader {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }

    /* ----- Code Blocks ----- */
    .stCodeBlock pre {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }

    /* ----- File Uploader ----- */
    .stFileUploader>div>div>div>div {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
    }

    /* ----- Date Input ----- */
    .stDateInput>div>div>input {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Slider ----- */
    .stSlider>div>div>div>div {
        background-color: #151A24 !important;
    }
    .stSlider>div>div>div>div>div>div {
        background-color: #38BDF8 !important;
    }

    /* ----- JSON Viewer ----- */
    .stJson pre {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Code Blocks (more specific) ----- */
    code, pre, .stCodeBlock pre, .stJson pre {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- AgGrid Additional Styling ----- */
    .ag-theme-alpine .ag-header-cell,
    .ag-theme-alpine .ag-header-group-cell {
        background-color: #151A24 !important;
        color: #38BDF8 !important;
        border-color: #1E293B !important;
    }
    .ag-theme-alpine .ag-row {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        border-color: #1E293B !important;
    }
    .ag-theme-alpine .ag-row:hover {
        background-color: #1E293B !important;
    }
    .ag-theme-alpine .ag-cell {
        border-color: #1E293B !important;
    }

    /* ----- Comprehensive AgGrid Dark Theme Override ----- */
    .ag-theme-alpine {
        --ag-background-color: #0B0E14 !important;
        --ag-foreground-color: #E2E8F0 !important;
        --ag-header-background-color: #151A24 !important;
        --ag-header-foreground-color: #38BDF8 !important;
        --ag-odd-row-background-color: #0B0E14 !important;
        --ag-row-hover-color: #1E293B !important;
        --ag-selected-row-background-color: #38BDF820 !important;
        --ag-range-selection-background-color: #38BDF830 !important;
        --ag-range-selection-border-color: #38BDF8 !important;
        --ag-header-column-resize-active-color: #38BDF8 !important;
        --ag-border-color: #1E293B !important;
        --ag-row-border-color: #1E293B !important;
        --ag-header-column-separator-color: #1E293B !important;
        --ag-header-column-separator-display: block !important;
        --ag-header-column-separator-width: 1px !important;
    }

    /* ----- AgGrid Specific Element Styling ----- */
    .ag-theme-alpine .ag-header,
    .ag-theme-alpine .ag-header-viewport,
    .ag-theme-alpine .ag-header-container {
        background-color: #151A24 !important;
    }

    .ag-theme-alpine .ag-body,
    .ag-theme-alpine .ag-body-viewport,
    .ag-theme-alpine .ag-body-container {
        background-color: #0B0E14 !important;
    }

    .ag-theme-alpine .ag-row-even {
        background-color: #0B0E14 !important;
    }

    .ag-theme-alpine .ag-row-odd {
        background-color: #151A24 !important;
    }

    .ag-theme-alpine .ag-cell {
        color: #E2E8F0 !important;
        background-color: transparent !important;
    }

    .ag-theme-alpine .ag-cell-inline-editing {
        background-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-cell-focus {
        border-color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-cell-value {
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-header-cell-text {
        color: #38BDF8 !important;
        font-weight: 600 !important;
    }

    .ag-theme-alpine .ag-header-cell-resize {
        background-color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-header-icon {
        color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-paging-panel {
        background-color: #151A24 !important;
        border-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-paging-button {
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-paging-disabled {
        color: #94A3B8 !important;
    }

    .ag-theme-alpine .ag-paging-row-summary-panel {
        background-color: #151A24 !important;
        border-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-tooltip {
        background-color: #151A24 !important;
        border-color: #1E293B !important;
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-menu {
        background-color: #151A24 !important;
        border-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-menu-option {
        color: #E2E8F0 !important;
        background-color: transparent !important;
    }

    .ag-theme-alpine .ag-menu-option:hover {
        background-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-menu-option-text {
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-filter-toolbar {
        background-color: #151A24 !important;
        border-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-input-field {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border-color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-input-field-input {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-select {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border-color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-picker-field {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
        border-color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-checkbox-input-wrapper {
        background-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-checkbox-input {
        background-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-checkbox-checked {
        background-color: #38BDF8 !important;
        border-color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-checkbox-unchecked {
        background-color: #1E293B !important;
        border-color: #94A3B8 !important;
    }

    .ag-theme-alpine .ag-icon {
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-icon:hover {
        color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-tab {
        background-color: #151A24 !important;
        border-color: #1E293B !important;
        color: #E2E8F0 !important;
    }

    .ag-theme-alpine .ag-tab-active {
        background-color: #1E293B !important;
        border-bottom-color: #38BDF8 !important;
        color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-tab-selected {
        background-color: #1E293B !important;
        border-bottom-color: #38BDF8 !important;
        color: #38BDF8 !important;
    }

    /* ----- AgGrid Scrollbar Styling ----- */
    .ag-theme-alpine ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }

    .ag-theme-alpine ::-webkit-scrollbar-track {
        background: #0B0E14 !important;
    }

    .ag-theme-alpine ::-webkit-scrollbar-thumb {
        background: #1E293B !important;
        border-radius: 4px !important;
    }

    .ag-theme-alpine ::-webkit-scrollbar-thumb:hover {
        background: #38BDF8 !important;
    }

    /* ----- AgGrid Force Dark Theme ----- */
    .ag-theme-alpine {
        filter: none !important;
        -webkit-filter: none !important;
    }

    /* ----- AgGrid Container Styling ----- */
    .ag-theme-alpine {
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* ----- AgGrid Header Override ----- */
    .ag-theme-alpine .ag-header-row {
        border-bottom: 1px solid #1E293B !important;
    }

    /* ----- AgGrid Cell Content ----- */
    .ag-theme-alpine .ag-cell-content {
        color: #E2E8F0 !important;
    }

    /* ----- AgGrid Loading Overlay ----- */
    .ag-theme-alpine .ag-overlay-loading-center {
        background-color: rgba(15, 19, 28, 0.9) !important;
        color: #E2E8F0 !important;
        border: 1px solid #38BDF8 !important;
    }

    /* ----- AgGrid No Rows Overlay ----- */
    .ag-theme-alpine .ag-overlay-no-rows-center {
        background-color: rgba(15, 19, 28, 0.9) !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- AgGrid Force Important Overrides ----- */
    .ag-theme-alpine, .ag-theme-alpine * {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        border-color: #1E293B !important;
    }

    .ag-theme-alpine .ag-header-cell, .ag-theme-alpine .ag-header-group-cell {
        background-color: #151A24 !important;
        color: #38BDF8 !important;
    }

    .ag-theme-alpine .ag-input-field, .ag-theme-alpine .ag-select, .ag-theme-alpine .ag-picker-field {
        background-color: #1E293B !important;
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Container Styling ----- */
    .stContainer {
        background-color: transparent !important;
    }

    /* ----- Streamlit Widget Styling ----- */
    .st-bw, .st-bx, .st-bt, .st-bu, .st-bv, .st-bw, .st-bx, .st-by, .st-bz, .st-c0 {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Streamlit Element Styling ----- */
    .st-c1, .st-c2, .st-c3, .st-c4, .st-c5, .st-c6, .st-c7, .st-c8, .st-c9, .st-c10 {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Streamlit Block Styling ----- */
    .st-bb, .st-bc, .st-bd, .st-be, .st-bf, .st-bg, .st-bh, .st-bi, .st-bj, .st-bk {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Streamlit Section Styling ----- */
    .st-d2, .st-d3, .st-d4, .st-d5, .st-d6, .st-d7, .st-d8, .st-d9, .st-d10 {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Streamlit Widget Labels ----- */
    .st-bw label, .st-bx label, .st-bt label, .st-bu label, .st-bv label,
    .stTextInput label, .stNumberInput label, .stTextArea label,
    .stSelectbox label, .stMultiSelect label, .stDateInput label,
    .stCheckbox label, .stRadio label {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Placeholder Text ----- */
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }

    /* ----- Streamlit Tooltip ----- */
    .stTooltip {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Spinner ----- */
    .stSpinner > div {
        border-top-color: #38BDF8 !important;
    }

    /* ----- Streamlit Status ----- */
    .stStatus {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Empty Styling ----- */
    .stEmpty {
        background-color: transparent !important;
    }

    /* ----- Streamlit Metric Styling ----- */
    .stMetric {
        background-color: transparent !important;
    }

    /* ----- Streamlit Table Styling ----- */
    table, th, td {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }
    th {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
    }

    /* ----- Streamlit HR/Divider ----- */
    hr, .stDivider {
        border-color: #1E293B !important;
    }

    /* ----- Streamlit Markdown ----- */
    .stMarkdown {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Caption ----- */
    .stCaption {
        color: #94A3B8 !important;
    }

    /* ----- Streamlit Title ----- */
    .stTitle {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Header ----- */
    .stHeader {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Subheader ----- */
    .stSubheader {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Info ----- */
    .stInfo {
        background-color: #151A24 !important;
        border-left: 4px solid #38BDF8 !important;
    }

    /* ----- Streamlit Success ----- */
    .stSuccess {
        background-color: #151A24 !important;
        border-left: 4px solid #10B981 !important;
    }

    /* ----- Streamlit Warning ----- */
    .stWarning {
        background-color: #151A24 !important;
        border-left: 4px solid #F59E0B !important;
    }

    /* ----- Streamlit Error ----- */
    .stError {
        background-color: #151A24 !important;
        border-left: 4px solid #F43F5E !important;
    }

    /* ----- Streamlit Exception ----- */
    .stException {
        background-color: #151A24 !important;
        border-left: 4px solid #F43F5E !important;
    }

    /* ----- Streamlit Help ----- */
    .stHelp {
        background-color: #151A24 !important;
        border-left: 4px solid #38BDF8 !important;
    }

    /* ----- Streamlit Expander Content ----- */
    .streamlit-expanderContent {
        background-color: #0B0E14 !important;
        border: 1px solid #1E293B !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ----- Streamlit Expander Header Enhanced ----- */
    .streamlit-expanderHeader {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        color: #E2E8F0 !important;
        font-weight: 600 !important;
    }

    /* ----- Streamlit Expander Header Content ----- */
    .streamlit-expanderHeader .streamlit-expanderHeaderContent {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Expander Header Icon ----- */
    .streamlit-expanderHeader .streamlit-expanderHeaderIcon {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Expander Header Arrow ----- */
    .streamlit-expanderHeader .streamlit-expanderArrow {
        color: #E2E8F0 !important;
        border-color: #E2E8F0 !important;
    }

    /* ----- Streamlit Expander Header Hover ----- */
    .streamlit-expanderHeader:hover {
        background-color: #1E293B !important;
        border-color: #38BDF8 !important;
    }

    /* ----- Streamlit Expander Header Active ----- */
    .streamlit-expanderHeader[aria-expanded="true"] {
        background-color: #1E293B !important;
        border-color: #38BDF8 !important;
    }

    /* ----- Streamlit Expander Content Enhanced ----- */
    .streamlit-expanderContent {
        background-color: #0B0E14 !important;
        border: 1px solid #1E293B !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Expander Content Elements ----- */
    /* ----- Streamlit Expander Content Tables ----- */
    .streamlit-expanderContent table {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Expander Content Headers ----- */
    .streamlit-expanderContent th {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Expander Content Cells ----- */
    .streamlit-expanderContent td {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Expander Content Metrics ----- */
    .streamlit-expanderContent .stMetric {
        background-color: transparent !important;
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Expander Content Buttons ----- */
    .streamlit-expanderContent .stButton>button {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Expander Content Inputs ----- */
    .streamlit-expanderContent .stTextInput>div>div>input,
    .streamlit-expanderContent .stNumberInput>div>div>input {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Per-Bot Performance Specific Styling ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #38BDF8 !important;
    }

    /* ----- Per-Bot Performance Header Text ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] span,
    .streamlit-expanderHeader[aria-label*="bot"] span,
    .streamlit-expanderHeader[aria-label*="Bot"] span {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
    }

    /* ----- Per-Bot Performance Icon Styling ----- */
    .streamlit-expanderHeader[aria-label*="🟢"],
    .streamlit-expanderHeader[aria-label*="🔴"] {
        color: #E2E8F0 !important;
    }

    /* ----- Per-Bot Performance Expander Content ----- */
    .streamlit-expanderContent[aria-label*="Per-Bot"],
    .streamlit-expanderContent[aria-label*="bot"],
    .streamlit-expanderContent[aria-label*="Bot"] {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
    }

    /* ----- Per-Bot Performance Metric Boxes ----- */
    .streamlit-expanderContent .custom-metric {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Per-Bot Performance Info Boxes ----- */
    .streamlit-expanderContent .stInfo,
    .streamlit-expanderContent .stSuccess,
    .streamlit-expanderContent .stWarning,
    .streamlit-expanderContent .stError {
        background-color: #151A24 !important;
        border-left: 4px solid #38BDF8 !important;
        color: #E2E8F0 !important;
    }

    /* ----- Per-Bot Performance Column Layout ----- */
    .streamlit-expanderContent .stColumn {
        background-color: transparent !important;
    }

    /* ----- Per-Bot Performance Button Styling ----- */
    .streamlit-expanderContent .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%) !important;
        border: none !important;
        color: white !important;
    }

    /* ----- Per-Bot Performance Progress Bars ----- */
    .streamlit-expanderContent .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #38BDF8 0%, #0369A1 100%) !important;
    }

    /* ----- Per-Bot Performance Input Fields ----- */
    .streamlit-expanderContent .stTextArea>div>div>textarea {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Per-Bot Performance Select Boxes ----- */
    .streamlit-expanderContent .stSelectbox>div>div>div {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Per-Bot Performance Inline Style Overrides ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] [style*="color: white"],
    .streamlit-expanderHeader[aria-label*="bot"] [style*="color: white"],
    .streamlit-expanderHeader[aria-label*="Bot"] [style*="color: white"],
    .streamlit-expanderContent[aria-label*="Per-Bot"] [style*="color: white"],
    .streamlit-expanderContent[aria-label*="bot"] [style*="color: white"],
    .streamlit-expanderContent[aria-label*="Bot"] [style*="color: white"] {
        color: #E2E8F0 !important;
    }

    /* ----- Per-Bot Performance Background Overrides ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] [style*="background: white"],
    .streamlit-expanderHeader[aria-label*="bot"] [style*="background: white"],
    .streamlit-expanderHeader[aria-label*="Bot"] [style*="background: white"],
    .streamlit-expanderContent[aria-label*="Per-Bot"] [style*="background: white"],
    .streamlit-expanderContent[aria-label*="bot"] [style*="background: white"],
    .streamlit-expanderContent[aria-label*="Bot"] [style*="background: white"] {
        background: #151A24 !important;
    }

    /* ----- Per-Bot Performance Z-Index Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        z-index: 100 !important;
        position: relative !important;
    }

    /* ----- Per-Bot Performance Layer Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"]::before,
    .streamlit-expanderHeader[aria-label*="bot"]::before,
    .streamlit-expanderHeader[aria-label*="Bot"]::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background-color: #151A24 !important;
        z-index: -1 !important;
        border-radius: 8px !important;
    }

    /* ----- Per-Bot Performance Ultimate Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #38BDF8 !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.5rem 0 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        box-sizing: border-box !important;
        position: relative !important;
        z-index: 10 !important;
        overflow: hidden !important;
    }

    /* ----- Per-Bot Performance Header Content Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] .streamlit-expanderHeaderContent,
    .streamlit-expanderHeader[aria-label*="bot"] .streamlit-expanderHeaderContent,
    .streamlit-expanderHeader[aria-label*="Bot"] .streamlit-expanderHeaderContent {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        line-height: 1.5 !important;
        white-space: normal !important;
        text-overflow: ellipsis !important;
        overflow: hidden !important;
    }

    /* ----- Per-Bot Performance Header Icon Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] .streamlit-expanderHeaderIcon,
    .streamlit-expanderHeader[aria-label*="bot"] .streamlit-expanderHeaderIcon,
    .streamlit-expanderHeader[aria-label*="Bot"] .streamlit-expanderHeaderIcon {
        color: #E2E8F0 !important;
        margin-right: 0.5rem !important;
        font-size: 1.2rem !important;
        flex-shrink: 0 !important;
    }

    /* ----- Per-Bot Performance Header Arrow Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] .streamlit-expanderArrow,
    .streamlit-expanderHeader[aria-label*="bot"] .streamlit-expanderArrow,
    .streamlit-expanderHeader[aria-label*="Bot"] .streamlit-expanderArrow {
        color: #E2E8F0 !important;
        border-color: #E2E8F0 !important;
        margin-left: auto !important;
        flex-shrink: 0 !important;
    }

    /* ----- Per-Bot Performance Hover Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"]:hover,
    .streamlit-expanderHeader[aria-label*="bot"]:hover,
    .streamlit-expanderHeader[aria-label*="Bot"]:hover {
        background-color: #1E293B !important;
        border-color: #60A5FA !important;
        color: #E2E8F0 !important;
    }

    /* ----- Per-Bot Performance Active Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"][aria-expanded="true"],
    .streamlit-expanderHeader[aria-label*="bot"][aria-expanded="true"],
    .streamlit-expanderHeader[aria-label*="Bot"][aria-expanded="true"] {
        background-color: #1E293B !important;
        border-color: #38BDF8 !important;
        color: #E2E8F0 !important;
    }

    /* ----- Per-Bot Performance Content Fix ----- */
    .streamlit-expanderContent[aria-label*="Per-Bot"],
    .streamlit-expanderContent[aria-label*="bot"],
    .streamlit-expanderContent[aria-label*="Bot"] {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
        margin: 0 0 1rem 0 !important;
    }

    /* ----- Per-Bot Performance Inline Style Ultimate Override ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"] [style],
    .streamlit-expanderHeader[aria-label*="bot"] [style],
    .streamlit-expanderHeader[aria-label*="Bot"] [style],
    .streamlit-expanderContent[aria-label*="Per-Bot"] [style],
    .streamlit-expanderContent[aria-label*="bot"] [style],
    .streamlit-expanderContent[aria-label*="Bot"] [style] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border-color: #1E293B !important;
    }

    /* ----- Per-Bot Performance Pseudo-Element Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"]::after,
    .streamlit-expanderHeader[aria-label*="bot"]::after,
    .streamlit-expanderHeader[aria-label*="Bot"]::after {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background-color: #151A24 !important;
        z-index: -2 !important;
        border-radius: 8px !important;
    }

    /* ----- Per-Bot Performance Box Shadow Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    }

    /* ----- Per-Bot Performance Border Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        border-width: 1px !important;
        border-style: solid !important;
        border-color: #38BDF8 !important;
    }

    /* ----- Per-Bot Performance Text Selection Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"]::selection,
    .streamlit-expanderHeader[aria-label*="bot"]::selection,
    .streamlit-expanderHeader[aria-label*="Bot"]::selection {
        background-color: #38BDF8 !important;
        color: #0B0E14 !important;
    }

    /* ----- Per-Bot Performance Focus Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"]:focus,
    .streamlit-expanderHeader[aria-label*="bot"]:focus,
    .streamlit-expanderHeader[aria-label*="Bot"]:focus {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.3) !important;
    }

    /* ----- Per-Bot Performance Print Fix ----- */
    @media print {
        .streamlit-expanderHeader[aria-label*="Per-Bot"],
        .streamlit-expanderHeader[aria-label*="bot"],
        .streamlit-expanderHeader[aria-label*="Bot"] {
            background-color: #151A24 !important;
            color: #E2E8F0 !important;
            border-color: #1E293B !important;
        }
    }

    /* ----- Per-Bot Performance Animation Fix ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        animation: none !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }

    /* ----- Per-Bot Performance Final Force Override ----- */
    .streamlit-expanderHeader[aria-label*="Per-Bot"],
    .streamlit-expanderHeader[aria-label*="bot"],
    .streamlit-expanderHeader[aria-label*="Bot"] {
        background: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #38BDF8 !important;
        position: relative !important;
        z-index: 1000 !important;
    }

    /* ----- Streamlit Column Styling ----- */
    .stColumn {
        background-color: transparent !important;
    }

    /* ----- Streamlit Tabs Content ----- */
    .stTabs [data-testid="stTab"] {
        background-color: #0B0E14 !important;
    }

    /* ----- Streamlit Sidebar Content ----- */
    .sidebar .sidebar-content {
        background-color: #0F131C !important;
    }

    /* ----- Streamlit Main Content ----- */
    .main .block-container {
        background-color: transparent !important;
    }

    /* ----- Streamlit Widget Overrides ----- */
    [data-testid="stWidgetLabel"] {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Element Overrides ----- */
    [data-testid="stElementToolbar"] {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Dataframe Overrides ----- */
    [data-testid="stDataFrame"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Dataframe Table Styling ----- */
    [data-testid="stDataFrame"] table {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Dataframe Header Styling ----- */
    [data-testid="stDataFrame"] th {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border: 1px solid #1E293B !important;
        font-weight: 600 !important;
    }

    /* ----- Streamlit Dataframe Cell Styling ----- */
    [data-testid="stDataFrame"] td {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Dataframe Row Styling ----- */
    [data-testid="stDataFrame"] tr {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Dataframe Hover Styling ----- */
    [data-testid="stDataFrame"] tr:hover {
        background-color: #1E293B !important;
    }

    /* ----- Streamlit Dataframe Container Styling ----- */
    [data-testid="stDataFrame"] .dataframe-container {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }

    /* ----- Streamlit Dataframe Scrollable Area ----- */
    [data-testid="stDataFrame"] .dataframe-scrollable {
        background-color: #151A24 !important;
    }

    /* ----- Streamlit Dataframe Table Wrapper ----- */
    [data-testid="stDataFrame"] .dataframe-table {
        background-color: #151A24 !important;
    }

    /* ----- Streamlit Dataframe Header Wrapper ----- */
    [data-testid="stDataFrame"] .dataframe-header {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
    }

    /* ----- Streamlit Dataframe Body Wrapper ----- */
    [data-testid="stDataFrame"] .dataframe-body {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Dataframe Cell Content ----- */
    [data-testid="stDataFrame"] .dataframe-cell {
        color: #E2E8F0 !important;
        background-color: transparent !important;
    }

    /* ----- Streamlit Dataframe Even Rows ----- */
    [data-testid="stDataFrame"] .dataframe-even {
        background-color: #0B0E14 !important;
    }

    /* ----- Streamlit Dataframe Odd Rows ----- */
    [data-testid="stDataFrame"] .dataframe-odd {
        background-color: #151A24 !important;
    }

    /* ----- Streamlit Dataframe Selected Cell ----- */
    [data-testid="stDataFrame"] .dataframe-selected {
        background-color: #38BDF820 !important;
        border: 1px solid #38BDF8 !important;
    }

    /* ----- Streamlit Dataframe Specific Element Overrides ----- */
    /* NOTE: A rule here previously forced background-color/color/border-color
       with !important on every div/span/p/button/etc. inside [data-testid="stDataFrame"].
       This broke Streamlit's dataframe grid (glide-data-grid), which renders cells on
       an HTML canvas sized via internal measurement <div> elements. Forcing styles onto
       those divs interfered with the grid's own sizing/rendering, causing columns and
       cell text to disappear or render blank. Removed — do not re-add a broad
       div/span/etc selector scoped to stDataFrame. */

    /* ----- Streamlit Dataframe Scrollbar ----- */
    [data-testid="stDataFrame"] ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }

    [data-testid="stDataFrame"] ::-webkit-scrollbar-track {
        background: #0B0E14 !important;
    }

    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
        background: #1E293B !important;
        border-radius: 4px !important;
    }

    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover {
        background: #38BDF8 !important;
    }

    /* ----- Streamlit Dataframe Inline Styles Override ----- */
    [data-testid="stDataFrame"] [style*="background-color: white"],
    [data-testid="stDataFrame"] [style*="background-color: #fff"],
    [data-testid="stDataFrame"] [style*="background-color: #ffffff"],
    [data-testid="stDataFrame"] [style*="background: white"],
    [data-testid="stDataFrame"] [style*="background: #fff"],
    [data-testid="stDataFrame"] [style*="background: #ffffff"] {
        background-color: #151A24 !important;
        background: #151A24 !important;
    }

    /* ----- Streamlit Dataframe Inline Color Override ----- */
    [data-testid="stDataFrame"] [style*="color: white"],
    [data-testid="stDataFrame"] [style*="color: #fff"],
    [data-testid="stDataFrame"] [style*="color: #ffffff"] {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Dataframe Inline Border Override ----- */
    [data-testid="stDataFrame"] [style*="border-color: white"],
    [data-testid="stDataFrame"] [style*="border-color: #fff"],
    [data-testid="stDataFrame"] [style*="border-color: #ffffff"] {
        border-color: #1E293B !important;
    }

    /* ----- Streamlit Dataframe Class Overrides ----- */
    [data-testid="stDataFrame"] .white,
    [data-testid="stDataFrame"] .light,
    [data-testid="stDataFrame"] .bg-white,
    [data-testid="stDataFrame"] .background-white {
        background-color: #151A24 !important;
    }

    [data-testid="stDataFrame"] .text-white,
    [data-testid="stDataFrame"] .color-white {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Dataframe ID Overrides ----- */
    [data-testid="stDataFrame"] #white,
    [data-testid="stDataFrame"] #light,
    [data-testid="stDataFrame"] #bg-white {
        background-color: #151A24 !important;
    }

    /* ----- Streamlit JSON Overrides ----- */
    [data-testid="stJson"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Code Overrides ----- */
    [data-testid="stCodeBlock"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Text Overrides ----- */
    [data-testid="stText"] {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Markdown Overrides ----- */
    [data-testid="stMarkdown"] {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Caption Overrides ----- */
    [data-testid="stCaption"] {
        color: #94A3B8 !important;
    }

    /* ----- Streamlit Metric Overrides ----- */
    [data-testid="stMetric"] {
        background-color: transparent !important;
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Alert Overrides ----- */
    [data-testid="stAlert"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Progress Overrides ----- */
    [data-testid="stProgress"] {
        background-color: #151A24 !important;
    }

    /* ----- Streamlit Slider Overrides ----- */
    [data-testid="stSlider"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Selectbox Overrides ----- */
    [data-testid="stSelectbox"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Multiselect Overrides ----- */
    [data-testid="stMultiSelect"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Text Input Overrides ----- */
    [data-testid="stTextInput"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Number Input Overrides ----- */
    [data-testid="stNumberInput"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Text Area Overrides ----- */
    [data-testid="stTextArea"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Date Input Overrides ----- */
    [data-testid="stDateInput"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Checkbox Overrides ----- */
    [data-testid="stCheckbox"] {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Radio Overrides ----- */
    [data-testid="stRadio"] {
        color: #E2E8F0 !important;
    }

    /* ----- Streamlit Button Overrides ----- */
    [data-testid="stButton"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Tabs Overrides ----- */
    [data-testid="stTabs"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Expander Overrides ----- */
    [data-testid="stExpander"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Container Overrides ----- */
    [data-testid="stContainer"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Column Overrides ----- */
    [data-testid="stColumn"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Divider Overrides ----- */
    [data-testid="stDivider"] {
        border-color: #1E293B !important;
    }

    /* ----- Streamlit File Uploader Overrides ----- */
    [data-testid="stFileUploader"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Color Picker Overrides ----- */
    [data-testid="stColorPicker"] {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Time Input Overrides ----- */
    [data-testid="stTimeInput"] {
        background-color: #151A24 !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Camera Input Overrides ----- */
    [data-testid="stCameraInput"] {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Audio Overrides ----- */
    [data-testid="stAudio"] {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Video Overrides ----- */
    [data-testid="stVideo"] {
        background-color: #151A24 !important;
        border: 1px solid #1E293B !important;
    }

    /* ----- Streamlit Image Overrides ----- */
    [data-testid="stImage"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Plotly Chart Overrides ----- */
    [data-testid="stPlotlyChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Pydeck Chart Overrides ----- */
    [data-testid="stPydeckChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Graphviz Chart Overrides ----- */
    [data-testid="stGraphvizChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Vega Lite Chart Overrides ----- */
    [data-testid="stVegaLiteChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Altair Chart Overrides ----- */
    [data-testid="stAltairChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Bokeh Chart Overrides ----- */
    [data-testid="stBokehChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Deck.GL Chart Overrides ----- */
    [data-testid="stDeckGlChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Plotly Chart Overrides ----- */
    [data-testid="stPlotlyChart"] {
        background-color: transparent !important;
    }

    /* ----- Streamlit Final Overrides ----- */
    * {
        scrollbar-color: #1E293B #0B0E14 !important;
    }
</style>
"""


def apply_theme():
    """Inject the custom dark theme CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
