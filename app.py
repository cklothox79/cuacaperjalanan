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
st.write("Aplikasi ini membantu kamu melihat prakiraan cuaca berdasarkan lokasi dan rentang tanggal tertentu.")

# Input tanggal rentang
tanggal_awal, tanggal_akhir = st.date_input(
    "📅 Pilih rentang tanggal perjalanan:",
    value=(date.today(), date.today()),
    min_value=date.today()
)

kota = st.text_input("📝 Masukkan nama kota (opsional):")

# Peta interaktif
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

if lat and lon and tanggal_awal and tanggal_akhir:
    start_str = tanggal_awal.strftime("%Y-%m-%d")
    end_str = tanggal_akhir.strftime("%Y-%m-%d")
    cuaca = get_weather(lat, lon, start_str, end_str)

    if cuaca and "daily" in cuaca:
        daily = cuaca["daily"]
        st.subheader(f"📍 Prakiraan Cuaca dari {tanggal_awal.strftime('%d %B')} sampai {tanggal_akhir.strftime('%d %B %Y')}")

        suhu_min_list = []
        suhu_max_list = []
        hujan_list = []
        tanggal_list = []

        for i in range(len(daily['time'])):
            tgl = daily['time'][i]
            tgl_tampil = datetime.strptime(tgl, "%Y-%m-%d").strftime("%d %B")
            tmin = daily['temperature_2m_min'][i]
            tmax = daily['temperature_2m_max'][i]
            rain = daily['precipitation_sum'][i]

            st.write(f"📅 **{tgl_tampil}** — 🌡️ Min: {tmin}°C | 🌡️ Max: {tmax}°C | 🌧️ Hujan: {rain} mm")

            tanggal_list.append(tgl_tampil)
            suhu_min_list.append(tmin)
            suhu_max_list.append(tmax)
            hujan_list.append(rain)

            # simpan ke riwayat
            riwayat = {
                "waktu_pencarian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tanggal_perjalanan": tgl,
                "kota": kota if kota else "-",
                "latitude": lat,
                "longitude": lon,
                "suhu_min": tmin,
                "suhu_max": tmax,
                "curah_hujan": rain
            }

            riwayat_file = "riwayat.csv"
            if os.path.exists(riwayat_file):
                df = pd.read_csv(riwayat_file)
                df = pd.concat([df, pd.DataFrame([riwayat])], ignore_index=True)
            else:
                df = pd.DataFrame([riwayat])
            df.to_csv(riwayat_file, index=False)

        # grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tanggal_list, y=suhu_max_list, name='Suhu Maksimum (°C)', line=dict(color='tomato')))
        fig.add_trace(go.Scatter(x=tanggal_list, y=suhu_min_list, name='Suhu Minimum (°C)', line=dict(color='royalblue')))
        fig.add_trace(go.Bar(x=tanggal_list, y=hujan_list, name='Curah Hujan (mm)', yaxis='y2', marker=dict(color='skyblue'), opacity=0.6))

        fig.update_layout(
            title='Grafik Cuaca Multi-Hari',
            yaxis=dict(title='Suhu (°C)'),
            yaxis2=dict(title='Curah Hujan (mm)', overlaying='y', side='right'),
            height=450,
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.success("✅ Semua data berhasil ditampilkan dan disimpan.")
    else:
        st.error("❌ Data cuaca tidak tersedia.")
