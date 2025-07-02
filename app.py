import streamlit as st
import requests
from datetime import date, datetime
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go

st.set_page_config(page_title="Cuaca Perjalanan", layout="centered")
st.title("🌤️ Cuaca Perjalanan")
st.write("Lihat prakiraan suhu, hujan, awan, dan potensi cuaca ekstrem dari lokasi dan rentang waktu yang kamu pilih.")

# Input tanggal
tanggal_awal, tanggal_akhir = st.date_input(
    "📅 Pilih rentang tanggal:",
    value=(date.today(), date.today()),
    min_value=date.today()
)

# Input lokasi manual
kota = st.text_input("📝 Masukkan nama kota (opsional):")

# Peta lokasi
st.markdown("### 🗺️ Atau klik lokasi di peta:")
m = folium.Map(location=[-2.5, 117.0], zoom_start=5)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=400, width=900)

lat = lon = None
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Lokasi dari peta: {lat:.4f}, {lon:.4f}")

# Fungsi koordinat dari kota
def get_coordinates(nama_kota):
    url = f"https://nominatim.openstreetmap.org/search?q={nama_kota}&format=json&limit=1"
    headers = {"User-Agent": "cuaca-perjalanan-app"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200 and r.json():
        data = r.json()[0]
        return float(data["lat"]), float(data["lon"])
    return None, None

# Jika belum ada koordinat, ambil dari nama kota
if not lat and kota:
    lat, lon = get_coordinates(kota)
    if lat and lon:
        st.success(f"📍 Lokasi dari kota: {lat:.4f}, {lon:.4f}")
    else:
        st.error("❌ Kota tidak ditemukan.")

# Fungsi ambil data cuaca
def get_weather(lat, lon, start_date, end_date):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,cloudcover_mean,weathercode"
        f"&timezone=auto&start_date={start_date}&end_date={end_date}"
    )
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# Tampilkan grafik jika lengkap
if lat and lon and tanggal_awal and tanggal_akhir:
    start = tanggal_awal.strftime("%Y-%m-%d")
    end = tanggal_akhir.strftime("%Y-%m-%d")
    data = get_weather(lat, lon, start, end)

    if data and "daily" in data:
        d = data["daily"]
        tanggal = [datetime.strptime(t, "%Y-%m-%d").strftime("%d %b") for t in d["time"]]
        tmax = d["temperature_2m_max"]
        tmin = d["temperature_2m_min"]
        hujan = d["precipitation_sum"]
        awan = d["cloudcover_mean"]
        weathercode = d["weathercode"]

        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tanggal, y=tmax, name="Tmax (°C)", line=dict(color="red")))
        fig.add_trace(go.Scatter(x=tanggal, y=tmin, name="Tmin (°C)", line=dict(color="blue")))
        fig.add_trace(go.Bar(x=tanggal, y=hujan, name="Hujan (mm)", yaxis="y2", marker_color="skyblue", opacity=0.6))
        fig.add_trace(go.Bar(x=tanggal, y=awan, name="Awan (%)", yaxis="y2", marker_color="gray", opacity=0.4))

        fig.update_layout(
            title="📈 Grafik Prakiraan Cuaca",
            xaxis=dict(title="Tanggal"),
            yaxis=dict(title="Suhu (°C)"),
            yaxis2=dict(
                title="Hujan / Awan",
                overlaying="y",
                side="right"
            ),
            legend=dict(x=0.01, y=0.99),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # Deteksi potensi ekstrem
        ekstrem_hari = [tanggal[i] for i, kode in enumerate(weathercode) if kode >= 80]
        if ekstrem_hari:
            st.warning(f"⚠️ Cuaca ekstrem diperkirakan pada: {', '.join(ekstrem_hari)}")
    else:
        st.error("❌ Data cuaca tidak tersedia.")
