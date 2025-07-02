import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go

st.set_page_config(page_title="Cuaca Perjalanan (Per Jam)", layout="centered")
st.title("🕓 Cuaca Perjalanan Per Jam")
st.write("Lihat prakiraan suhu, hujan, awan, kelembapan, dan angin setiap jam untuk lokasi dan tanggal yang kamu pilih.")

# Input tanggal
tanggal = st.date_input("📅 Pilih tanggal perjalanan:", value=date.today(), min_value=date.today())

# Input kota
kota = st.text_input("📝 Masukkan nama kota (opsional):")

# Fungsi ambil koordinat dari kota
def get_coordinates(nama_kota):
    url = f"https://nominatim.openstreetmap.org/search?q={nama_kota}&format=json&limit=1"
    headers = {"User-Agent": "cuaca-perjalanan-app"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200 and r.json():
        data = r.json()[0]
        return float(data["lat"]), float(data["lon"])
    return None, None

# Inisialisasi koordinat
lat = lon = None
lokasi_sumber = ""

# Jika pengguna klik peta
st.markdown("### 🗺️ Klik lokasi di peta atau masukkan nama kota")
default_location = [ -2.5, 117.0 ]
m = folium.Map(location=default_location, zoom_start=5)

# Ambil koordinat dari kota (jika diisi)
if kota:
    lat, lon = get_coordinates(kota)
    if lat and lon:
        lokasi_sumber = "Kota"
        folium.Marker([lat, lon], tooltip=f"📍 {kota.title()}").add_to(m)
        m.location = [lat, lon]
        m.zoom_start = 9

# Tampilkan peta dan ambil klik
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, height=400, width=900)

# Jika pengguna klik di peta
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    lokasi_sumber = "Peta"
    st.success(f"📍 Lokasi dari peta: {lat:.4f}, {lon:.4f}")

# Fungsi ambil data cuaca
def get_hourly_weather(lat, lon, tanggal):
    tgl = tanggal.strftime("%Y-%m-%d")
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,cloudcover,weathercode,"
        f"relativehumidity_2m,windspeed_10m,winddirection_10m"
        f"&timezone=auto&start_date={tgl}&end_date={tgl}"
    )
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# Jika lokasi dan tanggal valid
if lat and lon and tanggal:
    data = get_hourly_weather(lat, lon, tanggal)
    if data and "hourly" in data:
        d = data["hourly"]
        waktu = d["time"]
        jam_labels = [w[-5:] for w in waktu]  # jam:menit
        suhu = d["temperature_2m"]
        hujan = d["precipitation"]
        awan = d["cloudcover"]
        kode = d["weathercode"]
        rh = d["relativehumidity_2m"]
        angin_speed = d["windspeed_10m"]
        angin_dir = d["winddirection_10m"]

        # Buat DataFrame untuk tabel & unduhan
        df = pd.DataFrame({
            "Waktu": waktu,
            "Suhu (°C)": suhu,
            "Hujan (mm)": hujan,
            "Awan (%)": awan,
            "RH (%)": rh,
            "Kecepatan Angin (m/s)": angin_speed,
            "Arah Angin (°)": angin_dir,
            "Kode Cuaca": kode
        })

        # Grafik suhu, hujan, awan
        st.subheader("📈 Grafik Suhu, Hujan & Awan")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=jam_labels, y=suhu, name="Suhu (°C)", line=dict(color="red")))
        fig.add_trace(go.Bar(x=jam_labels, y=hujan, name="Hujan (mm)", yaxis="y2", marker_color="skyblue", opacity=0.6))
        fig.add_trace(go.Bar(x=jam_labels, y=awan, name="Awan (%)", yaxis="y2", marker_color="gray", opacity=0.4))
        fig.update_layout(
            xaxis=dict(title="Jam"),
            yaxis=dict(title="Suhu (°C)"),
            yaxis2=dict(
                title="Hujan / Awan",
                overlaying="y",
                side="right"
            ),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # Visualisasi arah dan kecepatan angin
        st.subheader("🧭 Arah & Kecepatan Angin")
        fig_angin = go.Figure()
        fig_angin.add_trace(go.Barpolar(
            r=angin_speed,
            theta=angin_dir,
            width=[10]*len(angin_speed),
            marker_color="royalblue",
            opacity=0.7,
            name="Kecepatan Angin"
        ))
        fig_angin.update_layout(
            polar=dict(
                angularaxis=dict(direction="clockwise", rotation=90),
                radialaxis=dict(title="m/s")
            ),
            showlegend=False,
            height=450
        )
        st.plotly_chart(fig_angin, use_container_width=True)

        # Deteksi jam ekstrem
        ekstrem = [w.replace("T", " ") for i, w in enumerate(waktu) if kode[i] >= 80]
        if ekstrem:
            daftar = "\n".join(f"• {e}" for e in ekstrem)
            st.warning(f"⚠️ Cuaca ekstrem diperkirakan pada:\n\n{daftar}")
        else:
            st.success("✅ Tidak ada cuaca ekstrem yang terdeteksi.")

        # Tampilkan tabel dan tombol unduh
        st.markdown("### 📊 Tabel Data Cuaca")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Unduh Data (CSV)", data=csv, file_name="cuaca_per_jam.csv", mime="text/csv")

    else:
        st.error("❌ Data cuaca tidak tersedia.")
