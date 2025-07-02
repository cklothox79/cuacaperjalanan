import streamlit as st
import requests
from datetime import date, datetime
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go
import pandas as pd
import os

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")

st.title("🌤️ Cuaca Perjalanan")
st.write("Aplikasi ini membantu kamu melihat prakiraan cuaca berdasarkan lokasi dan tanggal tertentu.")

tanggal = st.date_input("📅 Pilih tanggal perjalanan:", min_value=date.today())
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

if lat and lon and tanggal:
    cuaca = get_weather(lat, lon, tanggal.strftime("%Y-%m-%d"))
    if cuaca and "daily" in cuaca:
        daily = cuaca["daily"]
        suhu_min = daily['temperature_2m_min'][0]
        suhu_max = daily['temperature_2m_max'][0]
        curah_hujan = daily['precipitation_sum'][0]

        st.subheader(f"📍 Cuaca pada {tanggal.strftime('%d %B %Y')}")
        st.write(f"🌡️ Suhu Minimum: {suhu_min}°C")
        st.write(f"🌡️ Suhu Maksimum: {suhu_max}°C")
        st.write(f"🌧️ Curah Hujan: {curah_hujan} mm")

        # Grafik
        fig = go.Figure()
        label_tanggal = tanggal.strftime('%d %b')
        fig.add_trace(go.Scatter(x=[label_tanggal], y=[suhu_max], name='Suhu Maksimum (°C)', mode='lines+markers', line=dict(color='tomato')))
        fig.add_trace(go.Scatter(x=[label_tanggal], y=[suhu_min], name='Suhu Minimum (°C)', mode='lines+markers', line=dict(color='royalblue')))
        fig.add_trace(go.Bar(x=[label_tanggal], y=[curah_hujan], name='Curah Hujan (mm)', yaxis='y2', marker=dict(color='skyblue'), opacity=0.6))
        fig.update_layout(
            title='Grafik Cuaca',
            yaxis=dict(title='Suhu (°C)'),
            yaxis2=dict(title='Curah Hujan (mm)', overlaying='y', side='right'),
            legend=dict(x=0, y=1),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Simpan riwayat
        riwayat = {
            "waktu_pencarian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tanggal_perjalanan": tanggal.strftime("%Y-%m-%d"),
            "kota": kota if kota else "-",
            "latitude": lat,
            "longitude": lon,
            "suhu_min": suhu_min,
            "suhu_max": suhu_max,
            "curah_hujan": curah_hujan
        }

        riwayat_file = "riwayat.csv"
        if os.path.exists(riwayat_file):
            df = pd.read_csv(riwayat_file)
            df = pd.concat([df, pd.DataFrame([riwayat])], ignore_index=True)
        else:
            df = pd.DataFrame([riwayat])

        df.to_csv(riwayat_file, index=False)
        st.success("✅ Riwayat pencarian disimpan ke *riwayat.csv*")

    else:
        st.error("❌ Data cuaca tidak tersedia.")
