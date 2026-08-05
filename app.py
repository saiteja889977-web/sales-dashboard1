import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Page Config
st.set_page_config(
    page_title="Secondary Sales Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Secondary Sales Dashboard")

def process_data(file_source):
    # Load sheet and automatically detect the header row containing 'USER'
    raw_file = pd.ExcelFile(file_source)
    sheet_name = raw_file.sheet_names[0]
    
    # Preview top rows to find header offset
    preview_df = pd.read_excel(file_source, sheet_name=sheet_name, nrows=10, header=None)
    header_idx = 0
    for idx, row in preview_df.iterrows():
        row_str = row.astype(str).str.upper().tolist()
        if any('USER' in val for val in row_str):
            header_idx = idx
            break

    # Read data with correct header row offset
    df = pd.read_excel(file_source, sheet_name=sheet_name, header=header_idx)
    df.columns = df.columns.astype(str).str.strip().str.upper()

    # Column Mapping Strategy
    mapping = {}
    ordinal_cols = []
    
    for col in df.columns:
        if 'USER' in col:
            mapping[col] = 'USER'
        elif 'DISTRIBUTOR' in col:
            mapping[col] = 'Distributor'
        elif 'BEAT' in col:
            mapping[col] = 'Beat'
        elif 'PRIMARY' in col:
            mapping[col] = 'Primary Category'
        elif col == 'QTY' or 'TOTAL' in col:
            mapping[col] = 'QTY'
        elif any(ord_word in col for ord_word in ['FIRST', 'SECON', 'THIRD', 'FOURT', 'FIFTH', 'SIXTH', 'SEVENT', 'EIGHT', 'NINTH', 'TENTH']):
            ordinal_cols.append(col)

    df = df.rename(columns=mapping)

    # Convert numeric ordinal columns and compute Total QTY if not present
    for c in ordinal_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    if 'QTY' not in df.columns or df['QTY'].sum() == 0:
        if ordinal_cols:
            df['QTY'] = df[ordinal_cols].sum(axis=1)
        else:
            num_cols = df.select_dtypes(include=['number']).columns
            df['QTY'] = df[num_cols].sum(axis=1) if len(num_cols) > 0 else 0

    # Ensure required textual columns exist
    for required_col, default_val in [('USER', 'Unassigned'), ('Distributor', 'Unassigned'), ('Beat', 'Unassigned'), ('Primary Category', 'General')]:
        if required_col not in df.columns:
            df[required_col] = default_val
        else:
            df[required_col] = df[required_col].fillna(default_val)

    # Drop completely empty rows
    df = df.dropna(subset=['USER', 'Distributor'], how='all')
    df['QTY'] = pd.to_numeric(df['QTY'], errors='coerce').fillna(0)
    
    return df, ordinal_cols

# Sidebar File Ingestion
st.sidebar.header("📂 Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx", "xls"])

raw_df = None
ordinal_cols = []

if uploaded_file is not None:
    try:
        raw_df, ordinal_cols = process_data(uploaded_file)
        st.sidebar.success("🎉 Excel file loaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error parsing uploaded file: {e}")

elif os.path.exists("Secondary Order Dump (New)_01-07-26 to 28-07-26.xlsx"):
    try:
        raw_df, ordinal_cols = process_data("Secondary Order Dump (New)_01-07-26 to 28-07-26.xlsx")
        st.sidebar.info("ℹ️ Loaded repository default Excel file.")
    except Exception as e:
        st.sidebar.warning("Repo default file could not be parsed.")

if raw_df is None or raw_df.empty:
    st.info("👋 **Please upload your sales Excel spreadsheet in the sidebar to load the dashboard.**")
    st.stop()

# Representative Selection Filter
u_opts = ["All Users"] + sorted([str(u) for u in raw_df["USER"].unique() if pd.notna(u)])
sel_user = st.sidebar.selectbox("Filter by Representative:", u_opts)

working_df = raw_df.copy()
if sel_user != "All Users":
    working_df = working_df[working_df["USER"] == sel_user]

# Top KPI Bar
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Sales Volume (QTY)", f"{int(working_df['QTY'].sum()):,}")
kpi2.metric("Active Reps", working_df["USER"].nunique())
kpi3.metric("Distributors", working_df["Distributor"].nunique())
kpi4.metric("Beats/Routes", working_df["Beat"].nunique())

st.markdown("---")

# Visualizations
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Volume by Representative")
    rep_summary = working_df.groupby('USER')['QTY'].sum().reset_index().sort_values(by='QTY', ascending=False)
    fig_rep = px.bar(rep_summary, x='USER', y='QTY', color='USER', text_auto='.2s')
    st.plotly_chart(fig_rep, use_container_width=True)

with col_right:
    st.subheader("🏪 Top Distributors by Volume")
    dist_summary = working_df.groupby('Distributor')['QTY'].sum().reset_index().sort_values(by='QTY', ascending=False).head(10)
    fig_dist = px.bar(dist_summary, x='QTY', y='Distributor', orientation='h', text_auto='.2s')
    st.plotly_chart(fig_dist, use_container_width=True)

# Data Table Display
st.subheader("📋 Ledger Data")
st.dataframe(working_df, use_container_width=True)
