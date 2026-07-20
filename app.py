import io
import sqlite3
import time
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# Import untuk Pembuatan PDF (ReportLab)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Set Zona Waktu WIB (UTC+7)
WIB = timezone(timedelta(hours=7))

# ==========================================
# 1. KONFIGURASI HALAMAN & CUSTOM CSS DESAIN (MOBILE FRIENDLY)
# ==========================================
st.set_page_config(
    page_title="Buku Kas Harian",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

    /* Background & Container Utama */
    .stApp {
        background-color: #EAE4D6;
        max-width: 100% !important;
        padding: 5px !important;
        font-family: 'IBM Plex Mono', monospace;
        color: #2A241D;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* Header Struk Retro */
    .app-header {
        text-align: center;
        padding: 16px 8px;
        background: #FBF8F1;
        border: 2px solid #2A241D;
        border-bottom: 2px dashed #2A241D;
        border-radius: 8px 8px 0 0;
        margin-bottom: 10px;
    }
    .app-title {
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        font-size: 22px;
        letter-spacing: 2px;
        color: #2A241D;
        margin: 0;
    }
    .app-subtitle {
        font-size: 11px;
        color: #6B6151;
        letter-spacing: 1px;
        margin-top: 4px;
        font-weight: 700;
    }

    /* KUSTOMISASI TAB NAVIGASI TEGAS UNTUK MOBILE */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 6px !important;
        background-color: transparent !important;
        padding: 4px 0 !important;
        display: flex !important;
        width: 100% !important;
    }

    div[data-testid="stTabs"] [data-baseweb="tab"] {
        flex: 1 !important;
        height: 48px !important;
        background-color: #D3C8B2 !important;
        border: 2px solid #2A241D !important;
        border-radius: 8px !important;
        padding: 0px 4px !important;
        margin: 0 !important;
    }

    div[data-testid="stTabs"] [data-baseweb="tab"] p {
        color: #2A241D !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        text-align: center !important;
        margin: 0 !important;
    }

    div[data-testid="stTabs"] [aria-selected="true"] {
        background-color: #2A241D !important;
        border: 2px solid #2A241D !important;
    }

    div[data-testid="stTabs"] [aria-selected="true"] p {
        color: #FFC23D !important;
        font-weight: 700 !important;
    }

    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Banner Saldo Utama */
    .saldo-banner {
        background: #2A241D;
        color: #FFC23D;
        padding: 14px;
        border-radius: 8px;
        text-align: center;
        font-family: 'Space Mono', monospace;
        margin: 10px 0;
    }
    .saldo-banner-title {
        font-size: 11px;
        color: #D3C8B2;
        letter-spacing: 1px;
        font-weight: 700;
    }
    .saldo-banner-value {
        font-size: 22px;
        font-weight: 700;
        margin-top: 4px;
    }

    /* Grid Ringkasan */
    .stat-card {
        background: #FBF8F1;
        border: 2px solid #2A241D;
        border-left: 5px solid #2A241D;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .stat-card.in { border-left-color: #1E7A4C; }
    .stat-card.out { border-left-color: #C2402A; }
    .stat-label {
        font-size: 11px;
        color: #6B6151;
        font-weight: 700;
    }
    .stat-value {
        font-size: 15px;
        font-weight: 700;
        margin-top: 2px;
    }

    /* Transaksi Item Card */
    .tx-item {
        background: #FBF8F1;
        border: 1.5px solid #2A241D;
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 6px;
    }
    .tx-time-badge {
        font-size: 11px;
        font-weight: 700;
        color: #2A241D;
        background-color: #EAE4D6;
        padding: 3px 6px;
        border-radius: 4px;
    }
    .tx-desc { 
        font-size: 14px;
        font-weight: 700; 
        color: #2A241D;
        margin-top: 4px;
    }
    .tx-cat { 
        font-size: 10px;
        color: #2A241D; 
        border: 1px solid #2A241D; 
        padding: 2px 6px;
        border-radius: 3px;
        font-weight: 700;
    }
    .tx-amount-masuk { color: #1E7A4C; font-weight: 700; font-size: 15px; }
    .tx-amount-keluar { color: #C2402A; font-weight: 700; font-size: 15px; }
    .tx-saldo { font-size: 11px; color: #6B6151; text-align: right; margin-top: 4px; font-weight: 600; }

    /* Label Input */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stTimeInput label, .stRadio label {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #2A241D !important;
    }
    
    .stButton>button, .stDownloadButton>button {
        background-color: #2A241D !important;
        color: #FFC23D !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        width: 100%;
        padding: 10px !important;
        margin-top: 5px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# AMBIL URL GOOGLE SHEETS DARI SECRETS
try:
    API_URL = st.secrets["connections"]["gsheets"]["api_url"]
except Exception:
    API_URL = ""


# ==========================================
# 2. DATABASE & FUNGSI AKSI
# ==========================================
def get_db():
    return sqlite3.connect("buku_kas.db")


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            waktu TEXT,
            kategori TEXT,
            keterangan TEXT,
            jenis TEXT,
            jumlah REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pengaturan (
            key TEXT PRIMARY KEY,
            val REAL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def load_data():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM transaksi ORDER BY id ASC", conn
    )
    conn.close()
    if not df.empty:
        df["jumlah"] = pd.to_numeric(df["jumlah"], errors="coerce").fillna(0.0)
        df["jenis"] = df["jenis"].astype(str).str.strip().str.lower()
    return df


def add_data(tgl_str, waktu_str, kategori, keterangan, jenis, jumlah):
    new_id = int(time.time() * 1000)
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transaksi (id, tanggal, waktu, kategori, keterangan, jenis, jumlah) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (new_id, tgl_str, waktu_str, kategori, keterangan, jenis, float(jumlah)),
    )
    conn.commit()
    conn.close()

    if API_URL and "script.google.com" in API_URL:
        try:
            payload = {
                "action": "ADD",
                "id": new_id,
                "tanggal": tgl_str,
                "waktu": waktu_str,
                "kategori": kategori,
                "keterangan": keterangan,
                "jenis": jenis,
                "jumlah": float(jumlah),
            }
            requests.post(API_URL, json=payload, timeout=5)
        except Exception:
            pass


def delete_data(tx_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM transaksi WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()


def get_saldo_awal():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT val FROM pengaturan WHERE key = 'saldo_awal'")
    row = c.fetchone()
    conn.close()
    return float(row[0]) if row else 200000000.0


def set_saldo_awal(val):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "REPLACE INTO pengaturan (key, val) VALUES ('saldo_awal', ?)",
        (float(val),),
    )
    conn.commit()
    conn.close()

    if API_URL and "script.google.com" in API_URL:
        try:
            payload = {
                "action": "UPDATE_SALDO_AWAL",
                "saldo_awal": float(val),
            }
            requests.post(API_URL, json=payload, timeout=5)
        except Exception:
            pass


def format_rupiah(n):
    return f"Rp {float(n or 0):,.0f}".replace(",", ".")


# FUNGSI MEMBUAT LAPORAN PDF
def generate_pdf(df_pdf, s_awal, total_in, total_out, s_akhir):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        alignment=1,
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        alignment=1,
        spaceAfter=20,
    )

    elements.append(Paragraph("BUKU KAS HARIAN", title_style))
    elements.append(
        Paragraph(
            f"Laporan Dicetak Pada: {datetime.now(WIB).strftime('%d-%m-%Y %H:%M:%S')} WIB",
            subtitle_style,
        )
    )

    summary_data = [
        ["Saldo Awal", format_rupiah(s_awal)],
        ["Total Pemasukan (+)", format_rupiah(total_in)],
        ["Total Pengeluaran (-)", format_rupiah(total_out)],
        ["Saldo Akhir Saat Ini", format_rupiah(s_akhir)],
    ]
    t_summary = Table(summary_data, colWidths=[200, 300])
    t_summary.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF8F1")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2A241D")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#2A241D")),
        ])
    )
    elements.append(t_summary)
    elements.append(Spacer(1, 15))

    table_data = [
        ["Tanggal", "Waktu", "Kategori", "Keterangan", "Jenis", "Nominal"]
    ]
    for idx, row in df_pdf.iterrows():
        table_data.append([
            str(row["tanggal"]),
            str(row["waktu"]),
            str(row["kategori"]),
            str(row["keterangan"]),
            str(row["jenis"]).upper(),
            format_rupiah(row["jumlah"]),
        ])

    t_tx = Table(table_data, colWidths=[65, 45, 80, 150, 60, 100])
    t_tx.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2A241D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FFC23D")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#2A241D")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
        ])
    )
    elements.append(t_tx)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 3. HEADER & KALKULASI DATA
# ==========================================
st.markdown(
    """
<div class="app-header">
    <div class="app-title">BUKU KAS</div>
    <div class="app-subtitle">Pencatatan Keuangan Harian</div>
</div>
""",
    unsafe_allow_html=True,
)

df = load_data()
saldo_awal_db = get_saldo_awal()

total_masuk = 0.0
total_keluar = 0.0
saldo_saat_ini = saldo_awal_db

if not df.empty:
    total_masuk = float(df[df["jenis"] == "masuk"]["jumlah"].sum())
    total_keluar = float(df[df["jenis"] == "keluar"]["jumlah"].sum())
    saldo_saat_ini = saldo_awal_db + total_masuk - total_keluar

    running = saldo_awal_db
    saldos = []
    for idx, row in df.iterrows():
        amt = float(row["jumlah"])
        if row["jenis"] == "masuk":
            running += amt
        else:
            running -= amt
        saldos.append(running)
    df["saldo"] = saldos

# ==========================================
# 4. TAB NAVIGASI UTAMA
# ==========================================
tab1, tab2, tab3 = st.tabs(["Dashboard", "Transaksi", "Input"])

# ------------------------------------------
# TAB 1: DASHBOARD
# ------------------------------------------
with tab1:
    st.markdown(
        f"""
    <div class="saldo-banner">
        <div class="saldo-banner-title">SALDO AKHIR SAAT INI</div>
        <div class="saldo-banner-value">{format_rupiah(saldo_saat_ini)}</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Saldo Awal Periode</div>
        <div class="stat-value">{format_rupiah(saldo_awal_db)}</div>
    </div>
    <div class="stat-card in">
        <div class="stat-label">Total Pemasukan (+)</div>
        <div class="stat-value" style="color:#1E7A4C;">{format_rupiah(total_masuk)}</div>
    </div>
    <div class="stat-card out">
        <div class="stat-label">Total Pengeluaran (-)</div>
        <div class="stat-value" style="color:#C2402A;">{format_rupiah(total_keluar)}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not df.empty:
        st.caption("--- TREN SALDO BERJALAN ---")
        fig, ax = plt.subplots(figsize=(5, 2.5))
        fig.patch.set_facecolor("#FBF8F1")
        ax.set_facecolor("#FBF8F1")
        ax.plot(
            df["tanggal"].astype(str),
            df["saldo"],
            marker="o",
            color="#2A241D",
            linewidth=2,
            markersize=4,
        )
        plt.xticks(rotation=45, fontsize=7)
        plt.yticks(fontsize=7)
        plt.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig)

# ------------------------------------------
# TAB 2: TRANSAKSI & CETAK PDF
# ------------------------------------------
with tab2:
    new_saldo_awal = st.number_input(
        "Atur Saldo Awal Periode (Rp):",
        value=float(saldo_awal_db),
        step=50000.0,
    )
    if new_saldo_awal != saldo_awal_db:
        set_saldo_awal(new_saldo_awal)
        st.rerun()

    st.markdown(
        f"""
    <div class="saldo-banner">
        <div class="saldo-banner-title">SALDO AKHIR PERIODE</div>
        <div class="saldo-banner-value">{format_rupiah(saldo_saat_ini)}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not df.empty:
        # TOMBOL DOWNLOAD LAPORAN PDF
        pdf_bytes = generate_pdf(
            df, saldo_awal_db, total_masuk, total_keluar, saldo_saat_ini
        )
        st.download_button(
            label="📄 CETAK / DOWNLOAD LAPORAN PDF",
            data=pdf_bytes,
            file_name=f"Laporan_Buku_Kas_{datetime.now(WIB).strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )

        st.caption("--- DAFTAR TRANSAKSI ---")
        opsi_tgl = ["Semua tanggal"] + sorted(
            list(df["tanggal"].unique()), reverse=True
        )
        pilihan_tgl = st.selectbox("Filter Tanggal", opsi_tgl)

        df_visible = (
            df[df["tanggal"] == pilihan_tgl]
            if pilihan_tgl != "Semua tanggal"
            else df
        )

        for idx, row in df_visible.iloc[::-1].iterrows():
            is_masuk = row["jenis"] == "masuk"
            cls_amt = "tx-amount-masuk" if is_masuk else "tx-amount-keluar"
            sign = "+" if is_masuk else "-"

            st.markdown(
                f"""
            <div class="tx-item">
                <div>
                    <span class="tx-time-badge">📅 {row['tanggal']} | ⏱️ {row['waktu']} WIB</span>
                </div>
                <div class="tx-desc">{row['keterangan'] or '-'}</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <span class="tx-cat">{row['kategori']}</span>
                    <span class="{cls_amt}">{sign}{format_rupiah(row['jumlah'])}</span>
                </div>
                <div class="tx-saldo">Saldo: {format_rupiah(row['saldo'])}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("✕ Hapus", key=f"del_{row['id']}"):
                delete_data(row["id"])
                st.rerun()
    else:
        st.info("Belum ada transaksi.")

# ------------------------------------------
# TAB 3: INPUT TRANSAKSI (REAL-TIME WIB)
# ------------------------------------------
with tab3:
    st.caption("— FORM INPUT TRANSAKSI —")
    kategori_list = [
        "Penjualan",
        "Modal/Setoran",
        "Piutang Tertagih",
        "Belanja Bahan",
        "Operasional",
        "Gaji/Upah",
        "Lainnya",
    ]

    now_wib = datetime.now(WIB)

    with st.form("form_tx", clear_on_submit=True):
        tanggal = st.date_input("Tanggal Transaksi", value=now_wib.date())
        jam = st.time_input("Waktu Transaksi (WIB)", value=now_wib.time())

        kategori = st.selectbox("Kategori", kategori_list)
        keterangan = st.text_input(
            "Keterangan", placeholder="mis. Jual nasi goreng 5 porsi"
        )
        jenis = st.radio(
            "Jenis Transaksi",
            ["masuk", "keluar"],
            format_func=lambda x: (
                "↓ Pemasukan" if x == "masuk" else "↑ Pengeluaran"
            ),
            horizontal=True,
        )
        jumlah = st.number_input("Jumlah Nominal (Rp)", min_value=0.0, step=10000.0)

        submit = st.form_submit_button("+ SIMPAN TRANSAKSI")

        if submit:
            if jumlah <= 0:
                st.error("Isi nominal jumlah transaksi terlebih dahulu.")
            else:
                tgl_str = str(tanggal)
                waktu_str = jam.strftime("%H:%M")
                add_data(tgl_str, waktu_str, kategori, keterangan, jenis, jumlah)
                st.success(f"Transaksi Berhasil Dicatat ({tgl_str} {waktu_str} WIB) ✓")
                st.rerun()
