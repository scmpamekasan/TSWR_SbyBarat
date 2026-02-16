import streamlit as st
import pandas as pd
import json
import pydeck as pdk
import os

st.title("Peta Titik Koordinat + Batas Wilayah Surabaya Barat")

st.markdown("""
Masukkan daftar koordinat (longitude, latitude) satu per baris.  
Format: lng, lat (dipisah koma atau spasi)  
Contoh:  
112.7368, -7.2575
""")

raw_input = st.text_area(
    "Koordinat (lng, lat)",
    height=150,
    value="""112.7368, -7.2575
112.7680, -7.2650
112.7200, -7.2900
112.7500, -7.2500"""
)

points = []
for line in raw_input.strip().split("\n"):
    line = line.strip()
    if not line:
        continue
    try:
        parts = [float(x.strip()) for x in line.replace(";", ",").split(",") if x.strip()]
        if len(parts) >= 2:
            lng, lat = parts[0], parts[1]
            points.append({"lon": lng, "lat": lat})
    except Exception:
        st.warning(f"Baris salah format (dilewati): {line}")

if points:
    df = pd.DataFrame(points)
    df['lon'] = df['lon'].astype(float)  # Pastikan tipe data float
    df['lat'] = df['lat'].astype(float)

    # ────────────────────────────────────────────────
    # Load batas wilayah Surabaya Barat dari GeoJSON
    # ────────────────────────────────────────────────
    geojson_path = os.path.join("Map", "Surabaya Barat.geojson")

    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            batas_geojson = json.load(f)

        st.success("Batas wilayah Surabaya Barat berhasil dimuat!")

        # Debug: Tampilkan info data
        st.write("Jumlah titik:", len(df))
        if not df.empty:
            st.write("Contoh titik pertama:", df.iloc[0].to_dict())
            st.write("Rata-rata lokasi (untuk cek apakah di Surabaya Barat):")
            st.write(f"Lat rata-rata: {df['lat'].mean():.4f}")
            st.write(f"Lon rata-rata: {df['lon'].mean():.4f}")
        else:
            st.warning("DataFrame kosong – parsing gagal?")

        # Layer 1: Batas wilayah (polygon / MultiPolygon)
        boundary_layer = pdk.Layer(
            "GeoJsonLayer",
            data=batas_geojson,
            opacity=0.15,                     # transparan agar titik kelihatan
            stroked=True,
            filled=True,
            get_fill_color=[255, 255, 100, 60],  # Kuning semi-transparan
            get_line_color=[180, 0, 0],
            line_width_min_pixels=1,
            pickable=True
        )

        # Layer 2: Titik koordinat (diperbesar untuk visibilitas)
        points_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position=["lon", "lat"],
            get_radius=500,                      # dalam meter (naikkan ini kalau masih tak kelihatan, misal 500)
            get_fill_color=[59, 130, 246, 240],   # Biru full opacity
            get_line_color=[204, 153, 0, 200],       # Kuning agak gelap
            line_width_min_pixels=2,
            radius_min_pixels=1,                 # minimal 8 pixel agar tak hilang saat zoom out
            radius_max_pixels=2,                # batas max saat zoom in
            pickable=True
        )

        # View state (pusat otomatis berdasarkan titik input kalau ada)
        if not df.empty:
            center_lat = df['lat'].mean()
            center_lon = df['lon'].mean()
        else:
            center_lat = -7.03
            center_lon = 112.75

        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=12,  # Naikkan zoom agar titik lebih kelihatan
            pitch=0
        )

        # Gabungkan layers
        deck = pdk.Deck(
    layers=[boundary_layer, points_layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>Kecamatan:</b> {nm_kecamatan}",
        "style": {
            "background": "rgba(255, 255, 255, 0.96)",
            "color": "#111",
            "padding": "10px",
            "borderRadius": "6px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.25)",
            "fontFamily": "Arial, sans-serif",
            "fontSize": "14px",
            "lineHeight": "0.5"
        }
    },
    map_style=None  # atau 'light' jika ingin lebih terang
)
        st.subheader("Peta Titik + Batas Wilayah")
        st.pydeck_chart(deck, use_container_width=True, height=650)

        st.subheader("Data Koordinat")
        st.dataframe(df)

        # Opsional: tampilkan GeoJSON titik
        point_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [row.lon, row.lat]},
                    "properties": {"id": i+1}
                }
                for i, row in df.iterrows()
            ]
        }
        with st.expander("GeoJSON Titik (untuk debug)"):
            st.json(point_geojson)

    except FileNotFoundError:
        st.error(
            f"File GeoJSON tidak ditemukan di: `{geojson_path}`\n\n"
            "Pastikan:\n"
            "• Folder 'Map' ada di root repo\n"
            "• File bernama persis 'Bangkalan_BangkalanKota.geojson'\n"
            "• Sudah commit + push ke GitHub\n"
            "• Deploy ulang app di Streamlit Cloud"
        )
    except json.JSONDecodeError:
        st.error("File GeoJSON rusak atau format tidak valid. Cek di geojson.io")
    except Exception as e:
        st.error(f"Error saat memproses peta: {str(e)}")

else:
    st.info("Masukkan setidaknya satu koordinat yang valid di atas.")
