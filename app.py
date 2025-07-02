import streamlit as st
import requests
from datetime import date

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")

st.title("🌤️ Cuaca Perjalanan")
st.write("Aplikasi ini membantu kamu melihat prakiraan cuaca untuk lokasi dan tanggal tertentu.")

# Input lokasi (kota)
kota = st.text_input("Masukkan nama kota:")
tanggal = st.date_input("Pilih tanggal perjalanan:", min_value=date.today())

# Fungsi geocoding menggunakan Nominatim (OpenStreetMap) dengan User-Agent
def get_coordinates(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {"User-Agent": "cuaca-perjalanan-app"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data["lat"]), float(data["lon"])
    else:
        return None, None

# Fungsi ambil cuaca dari Open-Meteo
def get_weather(lat, lon, date_str):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto&start_date={date_str}&end_date={date_str}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Logika utama aplikasi
if kota and tanggal:
    lat, lon = get_coordinates(kota)
    if lat and lon:
        cuaca = get_weather(lat, lon, tanggal.strftime("%Y-%m-%d"))
        if cuaca and "daily" in cuaca:
            daily = cuaca["daily"]
            st.subheader(f"📍 Cuaca di {kota.title()} pada {tanggal.strftime('%d %B %Y')}")
            st.write(f"🌡️ Suhu Minimum: {daily['temperature_2m_min'][0]}°C")
            st.write(f"🌡️ Suhu Maksimum: {daily['temperature_2m_max'][0]}°C")
            st.write(f"🌧️ Curah Hujan: {daily['precipitation_sum'][0]} mm")
        else:
            st.error("Data cuaca tidak ditemukan.")
    else:
        st.error("Lokasi tidak ditemukan. Coba cek ejaannya.")
