import streamlit as st
import requests
from datetime import date, datetime
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")
st.title("🌤️ Cuaca Perjalanan")
st.write("Aplikasi ini menampilkan prakiraan cuaca berbasis lokasi dan rentang tanggal dalam bentuk grafik.")

# Input tanggal
tanggal_awal, tanggal_akhir = st.date_input(
    "📅 Pilih rentang tanggal perjalanan:",
    value=(date.today(), date.today()),
    min_value=date.today()
)

# Input kota
kota = st.text_input("📝 Masukkan nama kota (opsional):")

# Peta
st.markdown("### 🗺️ Atau klik lokasi pada peta:")
m = folium.Map(location=[-2.5, 117.0], zoom_start=5)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=400, width=900)

lat, lon = None, None
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Lokasi dari peta: {lat:.4f}, {lon:.4f}")

# Fungsi ambil koordinat dari nama kota
def get_coordinates(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {"User-Agent": "cuaca-perjalanan-app"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data["lat"]), float(data["lon"])
    return None, None

# Jika belum dapat koordinat dari peta, pakai nama kota
if not lat and kota:
    lat, lon = get_coordinates(kota)
    if lat and lon:
        st.success(f"📍 Lokasi dari kota: {lat:.4f}, {lon:.4f}")
    else:
        st.error("❌ Kota tidak ditemukan.")

# Fungsi ambil data cuaca
def get_weather(lat, lon, start_date, end_date):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        f"&start_date={start_date}&end_date={end_date}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Jika koordinat dan tanggal tersedia
if lat and lon and tanggal_awal and tanggal_akhir:
    start_str = tanggal_awal.strftime("%Y-%m-%d")
    end_str = tanggal_akhir.strftime("%Y-%m-%d")
    cuaca = get_weather(lat, lon, start_str, end_str)

    if cuaca and "daily" in cuaca:
        daily = cuaca["daily"]

        tanggal_list = [
            datetime.strptime(t, "%Y-%m-%d").strftime("%d %b")
            for t in daily["time"]
        ]
        suhu_min_list = daily["temperature_2m_min"]
        suhu_max_list = daily["temperature_2m_max"]
        hujan_list = daily["precipitation_sum"]

        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tanggal_list, y=suhu_max_list, name='Suhu Maksimum (°C)', line=dict(color='crimson')))
        fig.add_trace(go.Scatter(x=tanggal_list, y=suhu_min_list, name='Suhu Minimum (°C)', line=dict(color='royalblue')))
        fig.add_trace(go.Bar(x=tanggal_list, y=hujan_list, name='Curah Hujan (mm)', yaxis='y2', marker=dict(color='lightblue'), opacity=0.6))

        fig.update_layout(
            title='Grafik Prakiraan Cuaca',
            yaxis=dict(title='Suhu (°C)'),
            yaxis2=dict(title='Curah Hujan (mm)', overlaying='y', side='right'),
            height=450,
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❌ Data cuaca tidak tersedia.")
