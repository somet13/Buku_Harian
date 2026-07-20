import io
import sqlite3
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# Import untuk Pembuatan PDF (ReportLab)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ==========================================
# 1. KONFIGURASI HALAMAN & CUSTOM CSS DESAIN (FONT & TOMBOL DIPERBESAR)
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

    /* Background Utama */
    .stApp {
        background-color: #EAE4D6;
        max-width: 580px;
        margin: 0 auto;
        font-family: 'IBM Plex Mono', monospace;
        color: #2A241D;
    }

    /* Header Struk Retro */
    .app-header {
        text-align: center;
        padding: 24px 12px 14px 12px;
        background: #FBF8F1;
        border: 2px solid #2A241D;
        border-bottom: 2px dashed #2A241D;
        border-radius: 10px 10px 0 0;
        box-shadow: 0 4px 12px rgba(40,32,20,0.1);
    }
    .app-title {
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        font-size: 28px; /* Diperbesar dari 24px */
        letter-spacing: 3px;
        color: #2A241D;
        margin: 0;
        text-transform: uppercase;
    }
    .app-subtitle {
        font-size: 13px; /* Diperbesar dari 11px */
        color: #948A78;
        letter-spacing: 1px;
        margin-top: 6px;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* Kustomisasi Tab Navigasi (Diperbesar) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #EAE4D6;
        padding: 10px 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; /* Diperbesar dari 42px */
        background-color: #DFD7C4;
        border: 1.5px solid #948A78;
        border-bottom: none;
        border-radius: 8px 8px 0 0;
        color: #786E5C;
        font-family: 'Space Mono', monospace;
        font-size: 14px; /* Diperbesar dari 11px */
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FBF8F1 !important;
        color: #2A241D !important;
        border: 2px solid #2A241D !important;
        border-bottom: none !important;
    }

    /* Stat Grid Cards (Dashboard) */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin: 18px 0;
    }
    .stat-card {
        background: #FBF8F1;
        border: 2px solid #2A241D;
        border-left: 5px solid #2A241D;
        padding: 12px 10px;
        box-shadow: 2px 3px 0px #2A241D;
        border-radius: 6px;
    }
    .stat-card.in { border-left-color: #1E7A4C; }
    .stat-card.out { border-left-color: #C2402A; }
    .stat-label {
        font-size: 11px; /* Diperbesar dari 8.5px */
        color: #807563;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .stat-value {
        font-size: 14px; /* Diperbesar dari 12px */
        font-weight: 700;
        margin-top: 6px;
        word-break: break-all;
    }
    .stat-card.in .stat-value { color: #1E7A4C; }
    .stat-card.out .stat-value { color: #C2402A; }

    /* Saldo Akhir Banner Prominance */
    .saldo-banner {
        background: #2A241D;
        color: #FFC23D;
        padding: 16px 20px; /* Diperbesar */
        border-radius: 8px;
        text-align: center;
        font-family: 'Space Mono', monospace;
        margin: 12px 0 18px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .saldo-banner-title {
        font-size: 12px; /* Diperbesar dari 10px */
        color: #C2B8A5;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-weight: 700;
    }
    .saldo-banner-value {
        font-size: 26px; /* Diperbesar dari 20px */
        font-weight: 700;
        margin-top: 4px;
        letter-spacing: 1px;
    }

    /* Tampilan Kartu Item Transaksi */
    .tx-item {
        background: #FBF8F1;
        border: 1.5px dashed #948A78;
        padding: 12px 14px; /* Diperbesar */
        margin-bottom: 10px;
        border-radius: 6px;
    }
    .tx-item:hover {
        border-color: #2A241D;
        box-shadow: 2px 2px 0px #2A241D;
    }
    .tx-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .tx-time-badge {
        font-size: 12px; /* Diperbesar dari 10px */
        font-weight: 700;
        color: #2A241D;
        background-color: #EAE4D6;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: 'Space Mono', monospace;
    }
    .tx-desc { 
        font-size: 15px; /* Diperbesar dari 13px */
        font-weight: 700; 
        color: #2A241D;
    }
    .tx-cat { 
        font-size: 11px; /* Diperbesar dari 9.5px */
        color: #6B6151; 
        border: 1px solid #948A78; 
        padding: 2px 7px;
        border-radius: 3px;
        text-transform: uppercase;
        font-weight: 600;
    }
    .tx-amount-masuk { color: #1E7A4C; font-weight: 700; font-size: 16px; } /* Diperbesar dari 13px */
    .tx-amount-keluar { color: #C2402A; font-weight: 700; font-size: 16px; } /* Diperbesar dari 13px */
    .tx-saldo { font-size: 12px; color: #807563; text-align: right; margin-top: 6px; font-weight: 600; }

    /* Custom Input Fields & Form Labels (Diperbesar) */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stTimeInput label, .stRadio label {
        font-size: 14px !important;
        font-weight: 700 !important;
        color: #2A241D !important;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #FBF8F1 !important;
        border: 1.5px solid #948A78 !important;
        color: #2A241D !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 15px !important; /* Diperbesar */
        padding: 8px 12px !important;
    }

    /* Tombol Utama (Diperbesar Menonjol) */
    .stButton>button {
        background-color: #2A241D !important;
        color: #FFC23D !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 15px !important; /* Diperbesar */
        font-weight: 700 !important;
        border-radius: 6px !important;
        border: 2px solid #2A241D !important;
        width: 100%;
        padding: 12px 16px !important; /* Diperbesar */
        letter-spacing: 1px;
        box-shadow: 2px 3px 0px #948A78 !important;
    }
    .stButton>button:hover {
        background-color: #3A332C !important;
        color: #FFE082 !important;
        box-shadow: 2px 3px 0px #2A241D !important;
    }
    
    /* Caption & Sub-headers */
    .stCaption {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #2A241D !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# AMBIL URL GOOGLE SHEETS
try:
    API_URL = st.secrets["connections"]["gsheets"]["api_url"]
except Exception:
    API_URL = ""


# ==========================================
# 2. DATABASE SQLITE & PENGIRIM GOOGLE SHEETS
# ==========================================
def get_db():
    conn = sqlite3.connect("buku_kas.db")
    return conn


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

    # 1. Simpan ke SQLite
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transaksi (id, tanggal, waktu, kategori, keterangan, jenis, jumlah) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (new_id, tgl_str, waktu_str, kategori, keterangan, jenis, float(jumlah)),
    )
    conn.commit()
    conn.close()

    # 2. Sync ke Google Sheets
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


# ==========================================
# 3. FUNGSI GENERATE LAPORAN PDF
# ==========================================
def generate_pdf(df_data, saldo_awal, total_masuk, total_keluar, saldo_akhir):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#2A241D"),
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#948A78"),
    )
    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#2A241D"),
    )
    cell_header = ParagraphStyle(
        "CellHeader",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    elements = []

    # Header PDF
    elements.append(Paragraph("<b>LAPORAN BUKU KAS HARIAN</b>", title_style))
    elements.append(
        Paragraph(
            f"Dicetak pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 15))

    # Ringkasan Kas
    summary_data = [
        ["Keterangan", "Nominal (Rp)"],
        ["Saldo Awal Periode", format_rupiah(saldo_awal)],
        ["Total Pemasukan (+)", format_rupiah(total_masuk)],
        ["Total Pengeluaran (-)", format_rupiah(total_keluar)],
        ["SALDO AKHIR", format_rupiah(saldo_akhir)],
    ]
    t_summary = Table(summary_data, colWidths=[250, 250])
    t_summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#2A241D")),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
                ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DED5C1")),
                ("BACKGROUND", (0, 4), (1, 4), colors.HexColor("#E2DAC8")),
                ("FONTNAME", (0, 4), (1, 4), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(t_summary)
    elements.append(Spacer(1, 20))

    # Detail Tabel
    elements.append(Paragraph("<b>RINCIAN TRANSAKSI</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    headers = [
        Paragraph("<b>TGL & WAKTU</b>", cell_header),
        Paragraph("<b>KATEGORI</b>", cell_header),
        Paragraph("<b>KETERANGAN</b>", cell_header),
        Paragraph("<b>JENIS</b>", cell_header),
        Paragraph("<b>JUMLAH</b>", cell_header),
        Paragraph("<b>SALDO</b>", cell_header),
    ]

    table_data = [headers]

    for idx, row in df_data.iterrows():
        is_masuk = row["jenis"] == "masuk"
        jenis_str = "Masuk" if is_masuk else "Keluar"
        sign = "+" if is_masuk else "-"

        table_data.append(
            [
                Paragraph(f"{row['tanggal']}<br/>{row['waktu']}", cell_style),
                Paragraph(row["kategori"], cell_style),
                Paragraph(row["keterangan"] or "-", cell_style),
                Paragraph(jenis_str, cell_style),
                Paragraph(f"{sign}{format_rupiah(row['jumlah'])}", cell_style),
                Paragraph(format_rupiah(row["saldo"]), cell_style),
            ]
        )

    t_detail = Table(table_data, colWidths=[80, 80, 140, 50, 85, 85])
    t_detail.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2A241D")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DED5C1")),
            ]
        )
    )
    elements.append(t_detail)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================================
# 4. KODE UTAMA & HEADER VINTAGE
# ==========================================
st.markdown(
    """
<div class="app-header">
    <div class="app-title">BUKU KAS</div>
    <div class="app-subtitle">Laporan Keuangan Harian</div>
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
# 5. TAB NAVIGASI UTAMA
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
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-label">Saldo Awal</div>
            <div class="stat-value">{format_rupiah(saldo_awal_db)}</div>
        </div>
        <div class="stat-card in">
            <div class="stat-label">Total Masuk</div>
            <div class="stat-value">{format_rupiah(total_masuk)}</div>
        </div>
        <div class="stat-card out">
            <div class="stat-label">Total Keluar</div>
            <div class="stat-value">{format_rupiah(total_keluar)}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not df.empty:
        st.caption("--- TREN SALDO BERJALAN ---")
        fig, ax = plt.subplots(figsize=(6, 2.3))
        fig.patch.set_facecolor("#FBF8F1")
        ax.set_facecolor("#FBF8F1")
        ax.plot(
            df["tanggal"].astype(str),
            df["saldo"],
            marker="o",
            color="#2A241D",
            linewidth=2.5,
            markersize=5,
        )
        plt.xticks(rotation=45, fontsize=8.5)
        plt.yticks(fontsize=8.5)
        plt.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig)

        st.caption("--- PEMASUKAN VS PENGELUARAN ---")
        grouped = (
            df.groupby(["tanggal", "jenis"])["jumlah"]
            .sum()
            .unstack(fill_value=0)
        )
        if "masuk" not in grouped.columns:
            grouped["masuk"] = 0
        if "keluar" not in grouped.columns:
            grouped["keluar"] = 0
        st.bar_chart(grouped[["masuk", "keluar"]], color=["#1E7A4C", "#C2402A"])
    else:
        st.info("Belum ada data transaksi.")

# ------------------------------------------
# TAB 2: TRANSAKSI & CETAK LAPORAN
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
        col_dl1, col_dl2 = st.columns(2)

        csv = df.to_csv(index=False).encode("utf-8")
        col_dl1.download_button(
            "📊 Unduh CSV/Excel",
            data=csv,
            file_name=f"laporan_kas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        pdf_data = generate_pdf(
            df, saldo_awal_db, total_masuk, total_keluar, saldo_saat_ini
        )
        col_dl2.download_button(
            "📄 Cetak PDF",
            data=pdf_data,
            file_name=f"laporan_kas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.divider()

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
                <div class="tx-header">
                    <span class="tx-time-badge">📅 {row['tanggal']} | ⏱️ {row['waktu']}</span>
                    <span class="tx-desc">{row['keterangan'] or '-'}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                    <span class="tx-cat">{row['kategori']}</span>
                    <span class="{cls_amt}">{sign}{format_rupiah(row['jumlah'])}</span>
                </div>
                <div class="tx-saldo">Saldo Akhir: {format_rupiah(row['saldo'])}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("✕ Hapus Transaksi", key=f"del_{row['id']}"):
                delete_data(row["id"])
                st.rerun()
    else:
        st.info("Belum ada transaksi.")

# ------------------------------------------
# TAB 3: INPUT TRANSAKSI
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

    with st.form("form_tx", clear_on_submit=True):
        col_t, col_jam = st.columns(2)
        tanggal = col_t.date_input("Tanggal Transaksi", datetime.now())
        jam = col_jam.time_input("Waktu Transaksi", datetime.now().time())

        kategori = st.selectbox("Kategori", kategori_list)
        keterangan = st.text_input(
            "Keterangan Transaksi", placeholder="mis. Jual nasi goreng 5 porsi"
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
                st.success(f"Transaksi Berhasil Dicatat ({tgl_str} {waktu_str}) ✓")
                st.rerun()