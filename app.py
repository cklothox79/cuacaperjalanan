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
        data = response.j
