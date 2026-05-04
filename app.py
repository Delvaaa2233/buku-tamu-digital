import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import base64
import io

# ================== CONFIG ==================
st.set_page_config(
    page_title="Buku Tamu Digital BAPPEDA",
    page_icon="📘",
    layout="wide"
)

# ================== STYLE ==================
st.markdown("""
<style>
.main {
    background-color: #f4f6f9;
}
.block-container {
    padding-top: 1rem;
}
.header-box {
    display: flex;
    align-items: center;
    gap: 15px;
}
.title-text {
    font-size: 24px;
    font-weight: 700;
    color: #2c3e50;
}
.subtitle-text {
    font-size: 14px;
    color: #7f8c8d;
}
.stButton>button {
    background-color: #2ecc71;
    color: white;
    border-radius: 10px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ================== GOOGLE SHEETS ==================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)
client = gspread.authorize(creds)

SPREADSHEET_ID = "1lBGe8ZTLBICZz5dbDgPqwNiv4FO-CEFmcSnczYNUxz8"
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# HEADER
header = [
    "tanggal","tanggal_spt","nama_lengkap","nip","jabatan","opd",
    "nomor_hp","bidang","maksud","foto","tanda_tangan","kesan"
]

if sheet.row_values(1) != header:
    sheet.insert_row(header, 1)

# ================== HEADER UI ==================
col1, col2 = st.columns([1,6])

with col1:
    st.image("logo.png", width=80)  # pastikan file logo ada

with col2:
    st.markdown("""
    <div class="title-text">Buku Tamu Digital</div>
    <div class="subtitle-text">BAPPEDA Kota Pariaman</div>
    """, unsafe_allow_html=True)

st.divider()

# ================== MENU ==================
menu = st.sidebar.radio("Menu", [
    "Input Tamu",
    "Statistik",
    "Daftar Tamu"
])

# ================== INPUT ==================
if menu == "Input Tamu":
    st.subheader("📝 Form Buku Tamu")

    with st.form("form_tamu", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            tanggal = st.date_input("Tanggal", value=date.today())
            nama = st.text_input("Nama Lengkap")
            nip = st.text_input("NIP")
            jabatan = st.text_input("Jabatan")

        with col2:
            opd = st.text_input("OPD")
            nomor_hp = st.text_input("Nomor HP")
            bidang = st.selectbox("Bidang", [
                "Sekretariat","Litbang","Ekonomi",
                "Sarana & Prasarana","Pemerintahan & Sosial"
            ])

        maksud = st.text_area("Maksud Kunjungan")
        kesan = st.text_area("Kesan & Pesan")

        # FOTO
        st.subheader("📷 Foto")
        foto = st.camera_input("Ambil Foto")
        foto_base64 = ""

        if foto:
            foto_bytes = foto.getvalue()
            foto_base64 = base64.b64encode(foto_bytes).decode()

        # TTD
        st.subheader("✍️ Tanda Tangan")
        canvas = st_canvas(
            height=200,
            width=400,
            drawing_mode="freedraw",
            key="canvas"
        )

        ttd_base64 = ""
        if canvas.image_data is not None:
            img = Image.fromarray(canvas.image_data.astype("uint8"))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            ttd_base64 = base64.b64encode(buf.getvalue()).decode()

        submit = st.form_submit_button("💾 Simpan")

        if submit:
            sheet.append_row([
                str(tanggal),"",nama,nip,jabatan,opd,
                nomor_hp,bidang,maksud,foto_base64,ttd_base64,kesan
            ])
            st.success("✅ Data berhasil disimpan")

# ================== STATISTIK ==================
elif menu == "Statistik":
    st.header("📊 Dashboard Statistik")

    data = sheet.get_all_values()

    if len(data) > 1:
        df = pd.DataFrame(data[1:], columns=data[0])
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")

        today = datetime.today().date()

        col1, col2, col3 = st.columns(3)

        col1.metric("Hari Ini", len(df[df['tanggal'].dt.date == today]))
        col2.metric("Bulan Ini", len(df[df['tanggal'].dt.month == today.month]))
        col3.metric("Tahun Ini", len(df[df['tanggal'].dt.year == today.year]))

        st.divider()

        st.subheader("📈 Grafik Kunjungan Harian")
        daily = df.groupby(df["tanggal"].dt.date).size()
        st.line_chart(daily)

        st.subheader("📊 Distribusi Bidang")
        bidang_chart = df["bidang"].value_counts()
        st.bar_chart(bidang_chart)

    else:
        st.info("Belum ada data")

# ================== DAFTAR ==================
elif menu == "Daftar Tamu":
    st.header("📑 Daftar Tamu")

    data = sheet.get_all_values()

    if len(data) > 1:
        df = pd.DataFrame(data[1:], columns=data[0])

        st.dataframe(df, use_container_width=True)

        st.subheader("📷 Detail Tamu")

        for _, row in df.iterrows():

            st.markdown(f"### 👤 {row['nama_lengkap']}")
            st.write(f"📅 {row['tanggal']}")

            col1, col2 = st.columns(2)

            # FOTO
            with col1:
                st.write("Foto")
                if row["foto"]:
                    image = base64.b64decode(row["foto"])
                    st.image(image, width=200)
                else:
                    st.caption("Tidak ada foto")

            # TTD
            with col2:
                st.write("Tanda Tangan")
                if row["tanda_tangan"]:
                    image = base64.b64decode(row["tanda_tangan"])
                    st.image(image, width=200)
                else:
                    st.caption("Tidak ada tanda tangan")

            st.divider()

    else:
        st.info("Belum ada data")