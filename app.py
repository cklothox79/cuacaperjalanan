import streamlit as st
import requests
from datetime import date, datetime
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go

st.set_page_config(page_title="Cuaca Perjalanan (Per Jam)", layout="centered")
st.title("🕓 Cuaca Perjalanan Per Jam")
st.write("Lihat prakiraan suhu, hujan, awan, dan cuaca ekstrem setiap jam untuk lokasi dan tanggal yang kamu pilih.")

# Input tanggal tunggal
tanggal = st.date_input("📅 Pilih tanggal perjalanan:", value=date.today(), min_value=date.today())

# Input kota
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

# Fungsi ambil data cuaca per jam
def get_hourly_weather(lat, lon, tanggal):
    tgl = tanggal.strftime("%Y-%m-%d")
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,cloudcover,weathercode"
        f"&timezone=auto&start_date={tgl}&end_date={tgl}"
    )
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# Tampilkan grafik dan deteksi ekstrem
if lat and lon and tanggal:
    data = get_hourly_weather(lat, lon, tanggal)
    if data and "hourly" in data:
        d = data["hourly"]
        waktu = d["time"]
        jam_labels = [w[-5:] for w in waktu]  # ambil "HH:MM"
        suhu = d["temperature_2m"]
        hujan = d["precipitation"]
        awan = d["cloudcover"]
        kode = d["weathercode"]

        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=jam_labels, y=suhu, name="Suhu (°C)", line=dict(color="red")))
        fig.add_trace(go.Bar(x=jam_labels, y=hujan, name="Hujan (mm)", yaxis="y2", marker_color="skyblue", opacity=0.6))
        fig.add_trace(go.Bar(x=jam_labels, y=awan, name="Awan (%)", yaxis="y2", marker_color="gray", opacity=0.4))

        fig.update_layout(
            title="📈 Grafik Cuaca per Jam",
            xaxis=dict(title="Jam"),
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

        # Deteksi jam ekstrem
        ekstrem = [
            f"{w.replace('T', ' ')}"
            for i, w in enumerate(waktu) if kode[i] >= 80
        ]
        if ekstrem:
            daftar = "\n".join(f"• {e}" for e in ekstrem)
            st.warning(f"⚠️ Cuaca ekstrem diperkirakan pada:\n\n{daftar}")
        else:
            st.success("✅ Tidak ada cuaca ekstrem yang terdeteksi.")
    else:
        st.error("❌ Data cuaca tidak tersedia.")
