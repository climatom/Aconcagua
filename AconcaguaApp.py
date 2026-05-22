import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st


GDRIVE_BASE = "https://drive.google.com/uc?id="

# Replace with Google Drive file IDs
OBS_FILES = {
    "Summit": "1LN51hLQMm774HAMMOzaJDsNon6sN_m3A",
    "Nido": "1hhZB9nUUre50OX84Reoi28Kng8p9nFm5",
    "Mulas": "1Ag-eXDgUT0x0QoL-zX8BcYK3vDB5Q9VW",
}
VAR_MAP = {
    "Temperature": {
        "column": "sample_ta",
        "ylabel": "Temperature [°C]",
        "colour": "crimson",
    },
    "Wind speed": {
        "column": "max_ws",
        "ylabel": "Wind speed [m s⁻¹]",
        "colour": "darkorange",
    },
    "Pressure": {
        "column": "sample_bp",
        "ylabel": "Pressure [hPa]",
        "colour": "royalblue",
    },
    "Relative humidity": {
        "column": "rh_corr",
        "ylabel": "Relative humidity [%]",
        "colour": "seagreen",
    },
}


# ============================================================
# Streamlit setup
# ============================================================

st.set_page_config(
    page_title="Aconcagua Observations",
    layout="wide",
)

st.title("Aconcagua Observations")


# ============================================================
# Helpers
# ============================================================

@st.cache_data(ttl=300)
def load_obs(file_id: str) -> pd.DataFrame:
    url = GDRIVE_BASE + file_id

    df = pd.read_csv(
        url,
        index_col=0,
        parse_dates=True,
    )

    df.index.name = "time_utc"
    df = df.sort_index()

    return df


# ============================================================
# Sidebar
# ============================================================

station = st.sidebar.selectbox(
    "Station",
    list(OBS_FILES.keys()),
)

variable = st.sidebar.selectbox(
    "Variable",
    list(VAR_MAP.keys()),
)

ndays = st.sidebar.slider(
    "Days to plot",
    min_value=1,
    max_value=60,
    value=10,
)


# ============================================================
# Load and subset data
# ============================================================

df = load_obs(OBS_FILES[station])

end_time = df.index.max()
start_time = end_time - pd.Timedelta(days=ndays)

df_plot = df.loc[start_time:end_time].copy()

var_info = VAR_MAP[variable]
col = var_info["column"]
ylabel = var_info["ylabel"]
colour = var_info["colour"]


# ============================================================
# Metadata
# ============================================================

col1, col2, col3 = st.columns(3)

col1.metric("Station", station)
col2.metric("Latest observation", f"{end_time:%Y-%m-%d %H:%M} UTC")
col3.metric("Window", f"Last {ndays} days")


# ============================================================
# Plot
# ============================================================

fig, ax = plt.subplots(figsize=(13, 5.8))

# Connecting line
ax.plot(
    df_plot.index,
    df_plot[col],
    color=colour,
    linewidth=2.6,
    alpha=0.9,
    zorder=2,
)

# Observation points
ax.scatter(
    df_plot.index,
    df_plot[col],
    color=colour,
    s=38,
    edgecolors="black",
    linewidths=0.5,
    alpha=0.95,
    zorder=3,
)

ax.set_title(
    f"{station}: {variable}",
    fontsize=15,
    fontweight="bold",
)

ax.set_ylabel(ylabel, fontsize=12)
ax.set_xlabel("Time [UTC]", fontsize=12)

ax.grid(True, alpha=0.25, linewidth=0.8)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.xaxis.set_major_formatter(
    mdates.DateFormatter("%d %b\n%H:%M")
)

fig.autofmt_xdate()

plt.tight_layout()

st.pyplot(fig)

# ============================================================
# Table
# ============================================================

with st.expander("Show recent observations"):
    st.dataframe(
        df_plot.tail(48),
        use_container_width=True,
    )
