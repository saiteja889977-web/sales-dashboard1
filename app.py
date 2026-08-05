import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sales Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales Intelligence Dashboard")

# ---------------------------------------------------------
# Dynamic Data Processing Engine
# ---------------------------------------------------------
def process_data(file_source):
    df = pd.read_excel(file_source, sheet_name=0)
    df.columns = df.columns.astype(str).str.strip()
    
    # Smart column mapping dictionary
    mapping = {}
    for col in df.columns:
        c_upper = col.upper()
        if any(k in c_upper for k in ['USER', 'REP', 'AGENT', 'NAME', 'SALES PERSON']):
            mapping[col] = 'USER'
        elif any(k in c_upper for k in ['DISTRIBUTOR', 'DEALER', 'CLIENT', 'STORE', 'PARTY']):
            mapping[col] = 'Distributor'
        elif any(k in c_upper for k in ['BEAT', 'ROUTE', 'AREA', 'CITY', 'TOWN']):
            mapping[col] = 'Beat'
        elif any(k in c_upper for k in ['QTY', 'QUANTITY', 'VOLUME', 'UNITS', 'SALES QTY']):
            mapping[col] = 'QTY'
        elif any(k in c_upper for k in ['CATEGORY', 'PRODUCT', 'BRAND', 'ITEM']):
            mapping[col] = 'PrimaryCategory'
        elif 'PERIOD 1' in c_upper or 'P1' in c_upper:
            mapping[col] = 'Period 1'
        elif 'PERIOD 2' in c_upper or 'P2' in c_upper:
            mapping[col] = 'Period 2'
            
    df = df.rename(columns=mapping)
    
    # Fallback default columns if missing in upload
    if 'PrimaryCategory' not in df.columns:
        df['PrimaryCategory'] = 'General Category'
    else:
        df['PrimaryCategory'] = df['PrimaryCategory'].fillna('General Category')

    if 'QTY' not in df.columns:
        num_cols = df.select_dtypes(include=['number']).columns
        df['QTY'] = df[num_cols[0]] if len(num_cols) > 0 else 1

    if 'USER' not in df.columns:
        df['USER'] = 'Unassigned Rep'
    if 'Distributor' not in df.columns:
        df['Distributor'] = 'Unassigned Distributor'
    if 'Beat' not in df.columns:
        df['Beat'] = 'Unassigned Beat'

    if 'Period 1' not in df.columns: 
        df['Period 1'] = df['QTY'] * 0.45
    if 'Period 2' not in df.columns: 
        df['Period 2'] = df['QTY'] * 0.55
        
    # Clean numeric types
    df['QTY'] = pd.to_numeric(df['QTY'], errors='coerce').fillna(0)
    df['Period 1'] = pd.to_numeric(df['Period 1'], errors='coerce').fillna(0)
    df['Period 2'] = pd.to_numeric(df['Period 2'], errors='coerce').fillna(0)
    
    return df

# ---------------------------------------------------------
# Data Ingestion (Sidebar Upload & Repo Default)
# ---------------------------------------------------------
st.sidebar.header("📂 Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Excel File (.xlsx)", type=["xlsx", "xls"])

raw_df = None

if uploaded_file is not None:
    try:
        raw_df = process_data(uploaded_file)
        st.sidebar.success("🎉 Custom dataset loaded!")
    except Exception as e:
        st.sidebar.error(f"Error parsing uploaded file: {e}")

# Fallback to file stored in repository if no upload provided
elif os.path.exists("Secondary Order Dump (New)_01-07-26 to 28-07-26.xlsx"):
    try:
        raw_df = process_data("Secondary Order Dump (New)_01-07-26 to 28-07-26.xlsx")
        st.sidebar.info("ℹ️ Using repo default Excel sheet.")
    except Exception as e:
        st.sidebar.warning("Could not automatically load repo default dataset.")

# Empty state fallback
if raw_df is None or raw_df.empty:
    st.info("👋 **Welcome! Please upload your sales Excel file in the sidebar to populate the dashboard.**")
    st.stop()

# ---------------------------------------------------------
# Dashboard Views & Analytics
# ---------------------------------------------------------
st.sidebar.markdown("---")
u_opts = ["All Users"] + sorted(raw_df["USER"].astype(str).unique().tolist())
sel_user = st.sidebar.selectbox("Filter by Representative:", u_opts)

working_df = raw_df.copy()
if sel_user != "All Users":
    working_df = working_df[working_df["USER"] == sel_user]

# Top Metrics Row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Volume (QTY)", f"{int(working_df['QTY'].sum()):,}")
kpi2.metric("Active Reps", working_df["USER"].nunique())
kpi3.metric("Distributors", working_df["Distributor"].nunique())
kpi4.metric("Beats/Routes", working_df["Beat"].nunique())

st.markdown("---")

# Visualizations Row
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Category Distribution")
    cat_summary = working_df.groupby('PrimaryCategory')['QTY'].sum().reset_index()
    fig_pie = px.pie(cat_summary, values='QTY', names='PrimaryCategory', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("📈 Period Comparison")
    period_data = pd.DataFrame({
        'Period': ['Period 1', 'Period 2'],
        'QTY': [working_df['Period 1'].sum(), working_df['Period 2'].sum()]
    })
    fig_bar = px.bar(period_data, x='Period', y='QTY', color='Period', text_auto='.2s')
    st.plotly_chart(fig_bar, use_container_width=True)

# Detailed Data Table
st.subheader("📋 Ledger Details")
st.dataframe(
    working_df[['USER', 'Distributor', 'Beat', 'PrimaryCategory', 'Period 1', 'Period 2', 'QTY']],
    use_container_width=True
)
