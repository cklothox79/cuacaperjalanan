import streamlit as st
import requests
from datetime import date
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")

st.title("🌤️ Cuaca Perjalanan")
st.write("Aplikasi ini membantu kamu melihat prakiraan cuaca berdasarkan lokasi dan tanggal tertentu.")

# Input tanggal perjalanan
tanggal = st.date_input("📅 Pilih tanggal perjalanan:", min_value=date.today())

# Input nama kota manual (opsional)
kota = st.text_input("📝 Masukkan nama kota (opsional):")

# Input koordinat via peta
st.markdown("### 🗺️ Atau klik lokasi pada peta di bawah:")

m = folium.Map(location=[-2.5, 117.0], zoom_start=5)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=400, width=700)

# Koordinat default: None
lat, lon = None, None

# Ambil dari peta kalau ada klik
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Lokasi dari peta: {lat:.4f}, {lon:.4f}")

# Kalau belum ada koordinat dan nama kota diisi, pakai geocoding
if not lat and kota:
    def get_coordinates(city_name):
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {"User-Agent": "cuaca-perjalanan-app"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data["lat"]), float(data["lon"])
        else:
            return None, None

    lat, lon = get_coordinates(kota)
    if lat and lon:
        st.success(f"📍 Lokasi dari nama kota: {lat:.4f}, {lon:.4f}")
    else:
        st.error("❌ Lokasi tidak ditemukan. Coba cek ejaan kota.")

# Ambil data cuaca dari Open-Meteo
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

# Tampilkan cuaca jika semua input valid
if lat and lon and tanggal:
    cuaca = get_weather(lat, lon, tanggal.strftime("%Y-%m-%d"))
    if cuaca and "daily" in cuaca:
        daily = cuaca["daily"]
        st.subheader(f"📍 Cuaca di lokasi {lat:.2f}, {lon:.2f} pada {tanggal.strftime('%d %B %Y')}")
        st.write(f"🌡️ Suhu Minimum: {daily['temperature_2m_min'][0]}°C")
        st.write(f"🌡️ Suhu Maksimum: {daily['temperature_2m_max'][0]}°C")
        st.write(f"🌧️ Curah Hujan: {daily['precipitation_sum'][0]} mm")
    else:
        st.error("❌ Data cuaca tidak tersedia.")
