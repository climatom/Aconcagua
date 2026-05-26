import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# ============================================================
# Config
# ============================================================

GDRIVE_BASE = "https://drive.google.com/uc?id="

OBS_FILES = {
    "Summit": "1LN51hLQMm774HAMMOzaJDsNon6sN_m3A",
    "Nido": "1hhZB9nUUre50OX84Reoi28Kng8p9nFm5",
    "Mulas": "1Ag-eXDgUT0x0QoL-zX8BcYK3vDB5Q9VW",
}

FORECAST_FILE_ID = "17uXHC62XX9kmqA6HP2svy5dolpwHABpd"
LATEST_FORECAST_FILE_ID = "1sNCsYy68dG8ony5R3qHfQy4f1YjzS-cI"

VAR_MAP = {
    "Temperature": {
        "obs_col": "sample_ta",
        "obs_col_2": "sample_ta2",
        "fcst_median": "summit_t_C_median",
        "fcst_p10": "summit_t_C_p10",
        "fcst_p90": "summit_t_C_p90",
        "ylabel": "Temperature [°C]",
        "colour": "crimson",
    },
    "Wind speed": {
        "obs_col": "max_ws",
        "obs_col_2": "max_ws_2",
        "fcst_median": "summit_wspd_ms_median",
        "fcst_p10": "summit_wspd_ms_p10",
        "fcst_p90": "summit_wspd_ms_p90",
        "ylabel": "Wind speed [m s⁻¹]",
        "colour": "darkorange",
        "colour_2": "purple",
    },
    "Pressure": {
        "obs_col": "sample_bp",
        "obs_col_2": None,
        "fcst_median": "summit_p_hPa_median",
        "fcst_p10": "summit_p_hPa_p10",
        "fcst_p90": "summit_p_hPa_p90",
        "ylabel": "Pressure [hPa]",
        "colour": "royalblue",
    },
    "Relative humidity": {
        "obs_col": "rh_corr",
        "obs_col_2": None,
        "fcst_median": None,
        "fcst_p10": None,
        "fcst_p90": None,
        "ylabel": "Relative humidity [%]",
        "colour": "seagreen",
    },
}


# ============================================================
# Streamlit setup
# ============================================================

st.set_page_config(
    page_title="Aconcagua Observations and Forecast",
    layout="wide",
)

st.title("Aconcagua Observations and ECMWF Ensemble Forecast")


# ============================================================
# Helpers
# ============================================================

@st.cache_data(ttl=300)
def load_obs(file_id: str) -> pd.DataFrame:
    df = pd.read_csv(
        GDRIVE_BASE + file_id,
        index_col=0,
        parse_dates=True,
    )

    df.index.name = "time_utc"
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[df.index.notna()]
    df = df.sort_index()

    return df


@st.cache_data(ttl=300)
def load_forecast(file_id: str) -> pd.DataFrame:
    df = pd.read_csv(
        GDRIVE_BASE + file_id,
        parse_dates=["init_time_utc", "time_utc", "time_argentina"],
    )

    df["time_utc"] = pd.to_datetime(df["time_utc"], errors="coerce")
    df["init_time_utc"] = pd.to_datetime(df["init_time_utc"], errors="coerce")

    if "time_argentina" in df.columns:
        df["time_argentina"] = pd.to_datetime(df["time_argentina"], errors="coerce")
    else:
        df["time_argentina"] = df["time_utc"] - pd.Timedelta(hours=3)

    df = df.dropna(subset=["time_utc"])
    df = df.sort_values("time_utc")

    return df


def to_argentina_time(t):
    return t - pd.Timedelta(hours=3)


# ============================================================
# Sidebar
# ============================================================

mode = st.sidebar.radio(
    "Display mode",
    ["Observations only", "Summit obs + ECMWF forecast"],
)

station = st.sidebar.selectbox(
    "Station",
    list(OBS_FILES.keys()),
)

variable = st.sidebar.selectbox(
    "Variable",
    list(VAR_MAP.keys()),
)

ndays = st.sidebar.slider(
    "Past days to plot",
    min_value=1,
    max_value=60,
    value=10,
)

future_days = st.sidebar.slider(
    "Future forecast days to plot",
    min_value=1,
    max_value=15,
    value=10,
)

time_axis = st.sidebar.selectbox(
    "Time axis",
    ["UTC", "Argentina"],
)

show_spread = st.sidebar.checkbox(
    "Show forecast 10–90% range",
    value=True,
)


# ============================================================
# Load data
# ============================================================

obs = load_obs(OBS_FILES[station])

info = VAR_MAP[variable]

obs_col = info["obs_col"]
obs_col_2 = info.get("obs_col_2")

ylabel = info["ylabel"]
colour = info["colour"]
colour_2 = info.get("colour_2", "purple")

fcst = None
latest_fcst = None

forecast_available = (
    mode == "Summit obs + ECMWF forecast"
    and station == "Summit"
    and info["fcst_median"] is not None
)

if mode == "Summit obs + ECMWF forecast" and station != "Summit":
    st.warning("Forecast comparison is currently summit-only. Showing observations only.")

if mode == "Summit obs + ECMWF forecast" and info["fcst_median"] is None:
    st.warning(f"No ECMWF forecast variable configured for {variable}. Showing observations only.")

if forecast_available:
    fcst = load_forecast(FORECAST_FILE_ID)
    latest_fcst = load_forecast(LATEST_FORECAST_FILE_ID)


# ============================================================
# Time window
# ============================================================

now_utc = pd.Timestamp.utcnow().tz_localize(None)

past_start_time = now_utc - pd.Timedelta(days=ndays)
future_end_time = now_utc + pd.Timedelta(days=future_days)

obs_plot = obs.loc[past_start_time:now_utc].copy()

fcst_plot = None
latest_fcst_plot = None

if fcst is not None:
    fcst_plot = fcst.loc[
        (fcst["time_utc"] >= past_start_time)
        & (fcst["time_utc"] <= now_utc)
    ].copy()

if latest_fcst is not None:
    latest_fcst_plot = latest_fcst.loc[
        (latest_fcst["time_utc"] >= now_utc)
        & (latest_fcst["time_utc"] <= future_end_time)
    ].copy()


# ============================================================
# Time axis
# ============================================================

if time_axis == "Argentina":
    obs_x = to_argentina_time(obs_plot.index)
    xlabel = "Time [Argentina, UTC−3]"
    now_x = to_argentina_time(now_utc)

    if fcst_plot is not None:
        fcst_x = fcst_plot["time_argentina"]

    if latest_fcst_plot is not None:
        latest_fcst_x = latest_fcst_plot["time_argentina"]

else:
    obs_x = obs_plot.index
    xlabel = "Time [UTC]"
    now_x = now_utc

    if fcst_plot is not None:
        fcst_x = fcst_plot["time_utc"]

    if latest_fcst_plot is not None:
        latest_fcst_x = latest_fcst_plot["time_utc"]


# ============================================================
# Metadata
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Station", station)
c2.metric("Variable", variable)

if obs.empty:
    c3.metric("Latest obs", "No observations")
else:
    c3.metric("Latest obs", f"{obs.index.max():%Y-%m-%d %H:%M} UTC")

c4.metric("Window", f"{ndays} days past + {future_days} days future")

if fcst_plot is not None and len(fcst_plot) > 0:
    st.caption(
        "Historical forecast archive: best available ECMWF ENS forecast by valid time. "
        f"Latest archive init in plotted past window: "
        f"{fcst_plot['init_time_utc'].max():%Y-%m-%d %H:%M} UTC"
    )

if latest_fcst_plot is not None and len(latest_fcst_plot) > 0:
    st.caption(
        "Latest future forecast file: "
        f"init {latest_fcst_plot['init_time_utc'].max():%Y-%m-%d %H:%M} UTC; "
        f"valid from {latest_fcst_plot['time_utc'].min():%Y-%m-%d %H:%M} "
        f"to {latest_fcst_plot['time_utc'].max():%Y-%m-%d %H:%M} UTC."
    )


# ============================================================
# Warnings
# ============================================================

if obs_plot.empty:
    st.warning("No observations available in the selected past time window.")

if obs_col not in obs.columns:
    st.warning(f"Observation column '{obs_col}' is not available for {station}.")

if variable == "Wind speed" and obs_col_2 is not None and obs_col_2 not in obs.columns:
    st.info(f"Second wind-speed column '{obs_col_2}' is not available for {station}.")

if fcst_plot is not None and fcst_plot.empty:
    st.warning("No historical forecast data available in the selected past time window.")

if latest_fcst_plot is not None and latest_fcst_plot.empty:
    st.warning("No latest future forecast data available after the current time.")


# ============================================================
# Plot
# ============================================================

fig, ax = plt.subplots(figsize=(14, 6))

# Historical best-available forecast archive
if fcst_plot is not None and not fcst_plot.empty:
    fcst_median = info["fcst_median"]
    fcst_p10 = info["fcst_p10"]
    fcst_p90 = info["fcst_p90"]

    if show_spread:
        ax.fill_between(
            fcst_x,
            fcst_plot[fcst_p10],
            fcst_plot[fcst_p90],
            color="grey",
            alpha=0.22,
            label="Archive ECMWF ENS 10–90%",
            zorder=1,
        )

    ax.plot(
        fcst_x,
        fcst_plot[fcst_median],
        color="black",
        linewidth=2.4,
        label="Archive ECMWF ENS median",
        zorder=2,
    )


# Latest future forecast
if latest_fcst_plot is not None and not latest_fcst_plot.empty:
    fcst_median = info["fcst_median"]
    fcst_p10 = info["fcst_p10"]
    fcst_p90 = info["fcst_p90"]

    if show_spread:
        ax.fill_between(
            latest_fcst_x,
            latest_fcst_plot[fcst_p10],
            latest_fcst_plot[fcst_p90],
            color="lightskyblue",
            alpha=0.32,
            label="Latest ECMWF ENS 10–90%",
            zorder=1,
        )

    ax.plot(
        latest_fcst_x,
        latest_fcst_plot[fcst_median],
        color="navy",
        linewidth=3.0,
        label="Latest ECMWF ENS median",
        zorder=2,
    )


# Primary observations
if not obs_plot.empty and obs_col in obs_plot.columns:
    ax.plot(
        obs_x,
        obs_plot[obs_col],
        color=colour,
        linewidth=2.6,
        alpha=0.9,
        label=f"Observed {obs_col}",
        zorder=3,
    )

    ax.scatter(
        obs_x,
        obs_plot[obs_col],
        color=colour,
        edgecolors="black",
        linewidths=0.5,
        s=42,
        alpha=0.95,
        zorder=4,
    )


# Optional second observed wind-speed series
if (
    variable == "Wind speed"
    and obs_col_2 is not None
    and not obs_plot.empty
    and obs_col_2 in obs_plot.columns
):
    ax.plot(
        obs_x,
        obs_plot[obs_col_2],
        color=colour_2,
        linewidth=2.2,
        alpha=0.85,
        linestyle="--",
        label=f"Observed {obs_col_2}",
        zorder=3,
    )

    ax.scatter(
        obs_x,
        obs_plot[obs_col_2],
        color=colour_2,
        edgecolors="black",
        linewidths=0.4,
        s=34,
        alpha=0.9,
        zorder=4,
    )


# Now divider
ax.axvline(
    now_x,
    color="black",
    linestyle="--",
    linewidth=1.2,
    alpha=0.7,
    label="Now",
)


ax.set_title(
    f"Aconcagua {station}: {variable}",
    fontsize=15,
    fontweight="bold",
)

ax.set_ylabel(ylabel)
ax.set_xlabel(xlabel)

ax.grid(True, alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

handles, labels = ax.get_legend_handles_labels()
if handles:
    ax.legend(loc="best")

ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
fig.autofmt_xdate()

plt.tight_layout()

st.pyplot(fig)


# ============================================================
# Tables
# ============================================================

with st.expander("Show recent observations"):
    st.dataframe(obs_plot.tail(72), use_container_width=True)

if fcst_plot is not None:
    with st.expander("Show historical best-available forecast rows"):
        st.dataframe(fcst_plot, use_container_width=True)

if latest_fcst_plot is not None:
    with st.expander("Show latest future forecast rows"):
        st.dataframe(latest_fcst_plot, use_container_width=True)
