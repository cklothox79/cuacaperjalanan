import streamlit as st
import requests
from datetime import date
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")

st.title("🌤️ Cuaca Perjalanan")
st.write("Aplikasi ini membantu kamu melihat prakiraan cuaca berdasarkan lokasi dan tanggal tertentu.")

# Input tanggal
tanggal = st.date_input("📅 Pilih tanggal perjalanan:", min_value=date.today())

# Input kota manual
kota = st.text_input("📝 Masukkan nama kota (opsional):")

# Peta klik
st.markdown("### 🗺️ Atau klik lokasi pada peta:")

m = folium.Map(location=[-2.5, 117.0], zoom_start=5)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=300, width="100%")

lat, lon = None, None

# Dari peta
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Lokasi dari peta: {lat:.4f}, {lon:.4f}")

# Dari nama kota
def get_coordinates(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {"User-Agent": "cuaca-perjalanan-app"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data["lat"]), float(data["lon"])
    return None, None

if not lat and kota:
    lat, lon = get_coordinates(kota)
    if lat and lon:
        st.success(f"📍 Lokasi dari nama kota: {lat:.4f}, {lon:.4f}")
    else:
        st.error("❌ Kota tidak ditemukan.")

# Ambil cuaca
def get_weather(lat, lon, date_str):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        f"&start_date={date_str}&end_date={date_str}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Tampilkan cuaca dan grafik
if lat and lon and tanggal:
    cuaca = get_weather(lat, lon, tanggal.strftime("%Y-%m-%d"))
    if cuaca and "daily" in cuaca:
        daily = cuaca["daily"]
        st.subheader(f"📍 Cuaca pada {tanggal.strftime('%d %B %Y')}")
        st.write(f"🌡️ Suhu Minimum: {daily['temperature_2m_min'][0]}°C")
        st.write(f"🌡️ Suhu Maksimum: {daily['temperature_2m_max'][0]}°C")
        st.write(f"🌧️ Curah Hujan: {daily['precipitation_sum'][0]} mm")

        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[tanggal.strftime('%d %b')],
            y=[daily['temperature_2m_max'][0]],
            name='Suhu Maksimum (°C)',
            mode='lines+markers',
            line=dict(color='tomato')
        ))
        fig.add_trace(go.Scatter(
            x=[tanggal.strftime('%d %b')],
            y=[daily['temperature_2m_min'][0]],
            name='Suhu Minimum (°C)',
            mode='lines+markers',
            line=dict(color='royalblue')
        ))
        fig.add_trace(go.Bar(
            x=[tanggal.strftime('%d %b')],
            y=[daily['precipitation_sum'][0]],
            name='Curah Hujan (mm)',
            yaxis='y2',
            marker=dict(color='skyblue'),
            opacity=0.6
        ))
        fig.update_layout(
            title='Grafik Cuaca',
            yaxis=dict(title='Suhu (°C)'),
            yaxis2=dict(title='Curah Hujan (mm)', overlaying='y', side='right'),
            legend=dict(x=0, y=1),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Data cuaca tidak tersedia.")
