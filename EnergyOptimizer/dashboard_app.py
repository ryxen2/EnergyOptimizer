import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Use pyarrow for better performance if available
try:
    import pyarrow
    st.info("Using pyarrow for faster data processing if available on your system.")
    engine = 'pyarrow'
except ImportError:
    engine = 'python'

# --- Data Loading and Cleaning Function ---
@st.cache_data
def load_and_clean_data(file_name, file_label):
    df = pd.read_csv(file_name, encoding='latin1')

    if 'Unnamed: 55' in df.columns:
        df = df.drop(columns=['Unnamed: 55'])

    # Handle column name variations, specifically for 'CPU (Tctl/Tdie) [°C]'
    if 'CPU (Tctl/Tdie) [Â°C]' in df.columns:
        df.rename(columns={'CPU (Tctl/Tdie) [Â°C]': 'CPU (Tctl/Tdie) [°C]'}, inplace=True)
    elif 'CPU (Tctl/Tdie) [°C]' not in df.columns:
        st.warning(f"Warning: 'CPU (Tctl/Tdie) [°C]' not found in {file_name}. Please check column names. Available columns: {df.columns.tolist()}")

    # Try different date formats for robustness
    try:
        df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
    except:
        try:
            df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d.%m.%Y %H:%M:%S.%f', errors='coerce')
        except:
            df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')

    df = df.dropna(subset=['Timestamp'])
    df = df.drop(columns=['Date', 'Time'])

    numeric_cols = df.columns.drop('Timestamp')

    for col in numeric_cols:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.replace(' ', '', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['CPU (Tctl/Tdie) [°C]', 'CPU Package Power [W]', 'Core VIDs (avg) [V]', 'CPU1 [RPM]', 'SoC Voltage (SVI2 TFN) [V]'])

    df['Source'] = file_label
    df = df.set_index('Timestamp')

    return df

# --- Load Data ---

df_eco = load_and_clean_data("7_11_2025_eco.CSV", "7_11_2025_eco")
df_03 = load_and_clean_data("03_11_2025_(1).csv", "03_11_2025_alt")
df_01 = load_and_clean_data("01_11_2025.csv", "01_11_2025")
df_02 = load_and_clean_data("02_11_2025.csv", "02_11_2025")
df_04 = load_and_clean_data("04_11_2025.csv", "04_11_2025")
df_05 = load_and_clean_data("05_11_2025.csv", "05_11_2025")
combined_df = pd.concat([df_eco, df_03, df_01, df_02, df_04, df_05])


# --- Helper Function for Plotting Time Series (using Plotly) ---
def plot_time_series(df, y_column, title):
    fig = px.line(df, x=df.index, y=y_column, color='Source',
                  title=title,
                  labels={'Timestamp': 'Time', y_column: y_column},
                  height=400)
    fig.update_layout(xaxis_title="Time", yaxis_title=y_column, legend_title="Source File")
    fig.update_xaxes(tickformat="%H:%M")
    st.plotly_chart(fig, width='stretch')

# --- Helper Function for Plotting Distribution (Violin Plot for comparison) ---
def plot_distribution(df, column, title):
    fig = go.Figure()
    for source in df['Source'].unique():
        data = df[df['Source'] == source][column].dropna()
        fig.add_trace(go.Violin(y=data,
                                name=source,
                                box_visible=True,
                                meanline_visible=True,
                                line_color=px.colors.qualitative.Plotly[df['Source'].unique().tolist().index(source)]
                                ))

    fig.update_layout(
        title=title,
        yaxis_title=column,
        height=400
    )
    st.plotly_chart(fig, width='stretch')

# --- Streamlit Dashboard Layout ---
st.set_page_config(layout="wide", page_title="Energy Monitoring Comparison Dashboard")

st.title("⚡ Energy Monitoring Comparison Dashboard")
st.markdown("### Comparing **7_11_2025_eco**, **03_11_2025_alt**, **01_11_2025**, **02_11_2025**, **04_11_2025**, and **05_11_2025** Log Files")

st.sidebar.header("Dashboard Controls")
selected_file = st.sidebar.selectbox(
    "Select File for Detailed Statistics:",
    options=["Combined", "7_11_2025_eco", "03_11_2025_alt"]
)

if selected_file == "Combined":
    display_df = combined_df
else:
    display_df = combined_df[combined_df['Source'] == selected_file]

# ----------------------------------------------------------------------
# --- 1. TEMPERATURES Comparison ---
# ----------------------------------------------------------------------
st.header("1. Core and CPU Temperature Comparison")
st.markdown("This section compares the **CPU (Tctl/Tdie) [°C]** which is the primary die temperature and a key indicator of load.")

col1, col2 = st.columns(2)
with col1:
    plot_time_series(combined_df, 'CPU (Tctl/Tdie) [°C]', 'CPU Die Temperature Over Time')
with col2:
    plot_distribution(combined_df, 'CPU (Tctl/Tdie) [°C]', 'CPU Temperature Distribution (Tctl/Tdie)')

st.markdown("---")

# ----------------------------------------------------------------------
# --- 2. POWER USAGE Comparison ---
# ----------------------------------------------------------------------
st.header("2. Power Usage Comparison")
st.markdown("This compares the total **CPU Package Power [W]** (including cores and SOC).")

col3, col4 = st.columns(2)
with col3:
    plot_time_series(combined_df, 'CPU Package Power [W]', 'CPU Package Power Over Time [W]')
with col4:
    plot_distribution(combined_df, 'CPU Package Power [W]', 'CPU Package Power Distribution [W]')

st.subheader("Mean Power Consumption Breakdown")
st.markdown("A comparison of the average power draw from individual cores and the SoC.")
mean_power = combined_df.groupby('Source')[['Core 0 Power [W]', 'Core 1 Power [W]', 'Core 2 Power [W]', 'Core 3 Power [W]', 'CPU SoC Power (SVI2 TFN) [W]']].mean().reset_index()
mean_power = mean_power.melt(id_vars='Source', var_name='Power Component', value_name='Mean Power [W]')

fig_bar = px.bar(mean_power, x='Source', y='Mean Power [W]', color='Power Component',
                 title='Mean Power Consumption Breakdown',
                 height=450)
fig_bar.update_layout(yaxis_title="Mean Power [W]", legend_title="Power Component")
st.plotly_chart(fig_bar, width='stretch')

st.markdown("---")

# ----------------------------------------------------------------------
# --- 3. CORE VOLTAGE/FREQUENCY (VIDs) Comparison ---
# ----------------------------------------------------------------------
st.header("3. Core Voltage Comparison (Proxy for Core Clocks/Performance)")
st.markdown("The **Average Core VID [V]** is a good proxy for the voltage requested by the cores, often correlating with their clock speed and performance load.")

col5, col6 = st.columns(2)
with col5:
    plot_time_series(combined_df, 'Core VIDs (avg) [V]', 'Average Core VID Over Time [V]')
with col6:
    plot_distribution(combined_df, 'Core VIDs (avg) [V]', 'Average Core VID Distribution [V]')

st.markdown("---")

# ----------------------------------------------------------------------
# --- 4. Detailed Statistics Table ---
# ----------------------------------------------------------------------
st.header(f"4. Detailed Statistics for **{selected_file}**")
st.markdown("Summary statistics (Count, Mean, Min, Max, Quartiles) for key metrics.")
summary_stats = display_df[['CPU (Tctl/Tdie) [°C]', 'CPU Package Power [W]', 'Core VIDs (avg) [V]', 'CPU1 [RPM]', 'GPU Temperature [°C]', 'SoC Voltage (SVI2 TFN) [V]']].describe().T.round(2)
st.dataframe(summary_stats, width='stretch')

# ----------------------------------------------------------------------
# --- 5. Raw Data Display (Optional) ---
# ----------------------------------------------------------------------
if st.checkbox("Show Raw Data"):
    st.subheader("Raw Data")
    st.dataframe(combined_df, width='stretch')
