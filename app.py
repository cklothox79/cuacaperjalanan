import streamlit as st
import requests
from datetime import date, datetime
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")
st.title("🌤️ Cuaca Perjalanan")
st.write("Grafik prakiraan cuaca multi‑hari: suhu, hujan, awan, dan potensi ekstrem.")

# Input tanggal rentang
tanggal_awal, tanggal_akhir = st.date_input(
    "📅 Pilih rentang tanggal:",
    value=(date.today(), date.today()),
    min_value=date.today()
)
kota = st.text_input("📝 Nama kota (opsional):")
st.markdown("### 🗺️ Atau klik lokasi di peta:")
m = folium.Map(location=[-2.5, 117.0], zoom_start=5)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=400, width=900)
lat = lon = None
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]; lon = map_data["last_clicked"]["lng"]
elif kota:
    def get_coordinates(city_name):
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {"User-Agent": "cuaca-perjalanan-app"}
        r = requests.get(url, headers=headers)
        return (float(r.json()[0]["lat"]), float(r.json()[0]["lon"])) if r.status_code==200 and r.json() else (None,None)
    lat, lon = get_coordinates(kota)
if lat and lon and tanggal_awal and tanggal_akhir:
    cuaca = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,cloudcover_mean,weathercode"
        f"&timezone=auto&start_date={tanggal_awal}&end_date={tanggal_akhir}"
    ).json()
    if "daily" in cuaca:
        d = cuaca["daily"]
        dates = [datetime.strptime(t,"%Y-%m-%d").strftime("%d %b") for t in d["time"]]
        tmin = d["temperature_2m_min"]
        tmax = d["temperature_2m_max"]
        rain = d["precipitation_sum"]
        cloud = d["cloudcover_mean"]
        wc = d["weathercode"]
        
        # Tampilkan grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=tmax, name="Tmax", line=dict(color="firebrick")))
        fig.add_trace(go.Scatter(x=dates, y=tmin, name="Tmin", line=dict(color="royalblue")))
        fig.add_trace(go.Bar(x=dates, y=rain, name="Hujan (mm)", yaxis="y2", marker_color="skyblue", opacity=0.6))
        fig.add_trace(go.Bar(x=dates, y=cloud, name="Awan (%)", yaxis="y3", marker_color="gray", opacity=0.4))
        fig.update_layout(
            title="Cuaca Multi‑Hari",
            yaxis=dict(title="Suhu (°C)"),
            yaxis2=dict(title="Hujan (mm)", overlaying="y", side="right"),
            yaxis3=dict(title="Awan (%)", overlaying="y", side="right", position=1.1),
            legend=dict(yanchor="top", y=0.99, x=0.01),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Deteksi kejadian ekstrem (kode cuaca >= 80)
        extremes = [dates[i] for i,code in enumerate(wc) if code>=80]
        if extremes:
            st.warning(f"⚠️ Potensi cuaca ekstrem pada: {', '.join(extremes)}")
    else:
        st.error("Data cuaca tidak tersedia.")
