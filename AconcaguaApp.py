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


@st.cache_data(ttl=300)
def load_obs(file_id):
    url = GDRIVE_BASE + file_id
    df = pd.read_csv(url, index_col=0, parse_dates=True)
    df.index.name = "time_utc"
    return df


st.title("Aconcagua Observations")

station = st.sidebar.selectbox("Station", list(OBS_FILES.keys()))

variable = st.sidebar.selectbox(
    "Variable",
    {
        "Temperature": "sample_ta",
        "Wind speed": "mean_ws",
        "Pressure": "sample_bp",
        "Relative humidity": "rh_corr",
    }.keys(),
)

var_map = {
    "Temperature": ("sample_ta", "Temperature [°C]"),
    "Wind speed": ("mean_ws", "Wind speed [m s⁻¹]"),
    "Pressure": ("sample_bp", "Pressure [hPa]"),
    "Relative humidity": ("rh_corr", "Relative humidity [%]"),
}

col, ylabel = var_map[variable]

df = load_obs(OBS_FILES[station])

st.caption(f"Latest observation: {df.index.max():%Y-%m-%d %H:%M} UTC")

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(df.index, df[col], linewidth=1.5)

ax.set_title(f"{station}: {variable}")
ax.set_ylabel(ylabel)
ax.set_xlabel("Time [UTC]")
ax.grid(True, alpha=0.3)

ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
fig.autofmt_xdate()

st.pyplot(fig)

with st.expander("Show latest observations"):
    st.dataframe(df.tail(24), use_container_width=True)
