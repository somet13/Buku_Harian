import io
import re
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
# 1. KONFIGURASI HALAMAN & CUSTOM CSS AWAL
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

    .stApp {
        background-color: #EAE4D6;
        max-width: 480px;
        margin: 0 auto;
        font-family: 'IBM Plex Mono', monospace;
        color: #2A241D;
    }

    /* Header Struk Retro */
    .app-header {
        text-align: center;
        padding: 16px 8px;
        background: #FBF8F1;
        border: 2px solid #2A241D;
        border-bottom: 2px dashed #2A241D;
        border-radius: 8px 8px 0 0;
        margin-bottom: 12px;
    }
    .app-title {
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        font-size: 20px;
        letter-spacing: 2px;
        color: #2A241D;
        margin: 0;
    }
    .app-subtitle {
        font-size: 11px;
        color: #6B6151;
        letter-spacing: 1px;
        margin-top: 4px;
        font-weight: 600;
    }

    /* Banner Saldo Utama */
    .saldo-banner {
        background: #2A241D;
        color: #FFC23D;
        padding: 16px;
        border-radius: 6px;
        text-align: center;
        font-family: 'Space Mono', monospace;
        margin: 12px 0;
    }
    .saldo-banner-title {
        font-size: 11px;
        color: #D3C8B2;
        letter-spacing: 1px;
    }
    .saldo-banner-value {
        font-size: 24px;
        font-weight: 700;
        margin-top: 4px;
    }

    /* Card Stat Ringkasan Clean */
    .stat-card {
        background: #FBF8F1;
        border: 1.5px solid #2A241D;
        border-left: 4px solid #2A241D;
        padding: 10px 12px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .stat-card.in { border-left-color: #1E7A4C; }
    .stat-card.out { border-left-color: #C2402A; }
    .stat-label { font-size: 11px; color: #6B6151; }
    .stat-value { font-size: 16px; font-weight: 700; margin-top: 2px; }

    /* Item Transaksi Struk */
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
        padding: 2px 6px;
        border-radius: 4px;
    }
    .tx-desc { font-size: 13px; font-weight: 600; color: #2A241D; margin-top: 4px; }
    .tx-cat { font-size: 10px; color: #6B6151; border: 1px solid #D3C8B2; padding: 1px 4px; border-radius: 3px; }
    .tx-amount-masuk { color: #1E7A4C; font-weight: 700; font-size: 14px; }
    .tx-amount-keluar { color: #C2402A; font-weight: 700; font-size: 14px; }
    .tx-saldo { font-size: 11px; color: #6B6151; text-align: right; margin-top: 2px; }

    /* Button Retro Style */
    .stButton>button, .stDownloadButton>button {
        background-color: #2A241D !important;
        color: #FFC23D !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        width: 100%;
        padding: 8px !important;
        border: None !important;
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
# 2. HELPER & INTEGRASI DATABASE LOKAL + GOOGLE SHEETS
# ==========================================
def get_db():
    return sqlite3.connect("buku_kas.db")


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY,
            tanggal TEXT,
            waktu TEXT,
            kategori TEXT,
            keterangan TEXT,
            jenis TEXT,
            jumlah REAL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def clean_amount(val):
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val)
    digits = re.sub(r"[^\d]", "", val_str)
    return float(digits) if digits else 0.0


def clean_date_str(d_str):
    d_str = str(d_str or "").strip()
    if "GMT" in d_str or len(d_str) > 10:
        m = re.search(r"\d{4}-\d{2}-\d{2}", d_str)
        if m:
            return m.group(0)
    return d_str[:10] if d_str else str(datetime.now(WIB).date())


def clean_time_str(t_str):
    t_str = str(t_str or "").strip()
    m = re.search(r"\d{2}:\d{2}", t_str)
    if m:
        return m.group(0)
    return "00:00"


def fetch_from_sheets():
    if API_URL and "script.google.com" in API_URL:
        try:
            res = requests.get(API_URL, timeout=6)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
    return None


def force_sync_with_sheets():
    """Smart-Sync: Memperbarui database dari Google Sheets tanpa menghapus data lokal yang belum sempat masuk ke Sheets"""
    if API_URL:
        sheets_data = fetch_from_sheets()
        if sheets_data and isinstance(sheets_data, dict):
            txs = sheets_data.get("transaksi", [])
            if isinstance(txs, list):
                conn = get_db()
                c = conn.cursor()
                
                # Masukkan/perbarui data yang ada di Google Sheets
                for item in txs:
                    try:
                        tx_id = int(item.get("id"))
                        tgl = clean_date_str(item.get("tanggal", ""))
                        waktu = clean_time_str(item.get("waktu", ""))
                        kategori = str(item.get("kategori", ""))
                        keterangan = str(item.get("keterangan", ""))
                        jenis = str(item.get("jenis", "")).lower().strip()
                        jumlah = clean_amount(item.get("jumlah", 0))

                        c.execute(
                            "INSERT OR REPLACE INTO transaksi (id, tanggal, waktu, kategori, keterangan, jenis, jumlah) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (tx_id, tgl, waktu, kategori, keterangan, jenis, jumlah),
                        )
                    except Exception:
                        continue
                conn.commit()
                conn.close()


def load_data():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id ASC", conn)
    conn.close()

    # Jika SQLite kosong, tarik data awal dari Google Sheets
    if df.empty and API_URL:
        force_sync_with_sheets()
        conn = get_db()
        df = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id ASC", conn)
        conn.close()

    if not df.empty:
        df["jumlah"] = pd.to_numeric(df["jumlah"], errors="coerce").fillna(0.0)
        df["jenis"] = df["jenis"].astype(str).str.strip().str.lower()

        # HITUNG SALDO KONTINU DARI TRANSAKSI PERTAMA SAMPAI TERAKHIR
        running_saldo = 0.0
        saldos = []
        for _, row in df.iterrows():
            amt = float(row["jumlah"])
            if row["jenis"] == "masuk":
                running_saldo += amt
            else:
                running_saldo -= amt
            saldos.append(running_saldo)
        df["saldo"] = saldos

    return df


def format_rupiah(n):
    return f"Rp {float(n or 0):,.0f}".replace(",", ".")


def add_data(tgl_str, waktu_str, kategori, keterangan, jenis, jumlah):
    new_id = int(time.time() * 1000)

    # 1. Simpan LANGSUNG ke Database Lokal SQLite (Dijamin Langsung Muncul & Aman)
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transaksi (id, tanggal, waktu, kategori, keterangan, jenis, jumlah) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (new_id, tgl_str, waktu_str, kategori, keterangan, jenis, float(jumlah)),
    )
    conn.commit()
    conn.close()

    # 2. Kirim Cadangan ke Google Sheets di Background
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
                "jumlah": format_rupiah(jumlah),
            }
            requests.post(API_URL, json=payload, timeout=4)
        except Exception:
            pass


def delete_data(tx_id):
    # 1. Hapus dari Database Lokal
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM transaksi WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()

    # 2. Hapus dari Google Sheets
    if API_URL and "script.google.com" in API_URL:
        try:
            payload = {"action": "DELETE", "id": tx_id}
            requests.post(API_URL, json=payload, timeout=4)
        except Exception:
            pass


# FUNGSI CETAK PDF
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
        ["Saldo Awal Periode", format_rupiah(s_awal)],
        ["Total Pemasukan (+)", format_rupiah(total_in)],
        ["Total Pengeluaran (-)", format_rupiah(total_out)],
        ["Saldo Akhir Periode", format_rupiah(s_akhir)],
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
# 3. HEADER
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
today_str = str(datetime.now(WIB).date())

# ==========================================
# 4. TAB NAVIGASI UTAMA
# ==========================================
tab1, tab2, tab3 = st.tabs(["Dashboard", "Transaksi", "Input"])

# ------------------------------------------
# TAB 1: DASHBOARD
# ------------------------------------------
with tab1:
    view_type = st.radio(
        "Tampilan Ringkasan:",
        ["Hari Ini", "Keseluruhan"],
        horizontal=True,
    )

    if view_type == "Hari Ini":
        if not df.empty:
            df_today = df[df["tanggal"] == today_str]
            df_before = df[df["tanggal"] < today_str]

            saldo_awal_today = (
                float(df_before.iloc[-1]["saldo"]) if not df_before.empty else 0.0
            )
            masuk_today = (
                float(df_today[df_today["jenis"] == "masuk"]["jumlah"].sum())
                if not df_today.empty
                else 0.0
            )
            keluar_today = (
                float(df_today[df_today["jenis"] == "keluar"]["jumlah"].sum())
                if not df_today.empty
                else 0.0
            )
            saldo_akhir_today = float(df.iloc[-1]["saldo"])
        else:
            saldo_awal_today = 0.0
            masuk_today = 0.0
            keluar_today = 0.0
            saldo_akhir_today = 0.0

        st.markdown(
            f"""
        <div class="saldo-banner">
            <div class="saldo-banner-title">SALDO KAS HARI INI ({today_str})</div>
            <div class="saldo-banner-value">{format_rupiah(saldo_akhir_today)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Saldo Awal Hari Ini (Sisa Kemarin)</div>
            <div class="stat-value">{format_rupiah(saldo_awal_today)}</div>
        </div>
        <div class="stat-card in">
            <div class="stat-label">Pemasukan Hari Ini (+)</div>
            <div class="stat-value" style="color:#1E7A4C;">{format_rupiah(masuk_today)}</div>
        </div>
        <div class="stat-card out">
            <div class="stat-label">Pengeluaran Hari Ini (-)</div>
            <div class="stat-value" style="color:#C2402A;">{format_rupiah(keluar_today)}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        total_masuk = 0.0
        total_keluar = 0.0
        saldo_total = 0.0

        if not df.empty:
            total_masuk = float(df[df["jenis"] == "masuk"]["jumlah"].sum())
            total_keluar = float(df[df["jenis"] == "keluar"]["jumlah"].sum())
            saldo_total = float(df.iloc[-1]["saldo"])

        st.markdown(
            f"""
        <div class="saldo-banner">
            <div class="saldo-banner-title">TOTAL SALDO KAS AKUMULATIF</div>
            <div class="saldo-banner-value">{format_rupiah(saldo_total)}</div>
        </div>
        <div class="stat-card in">
            <div class="stat-label">Total Pemasukan Keseluruhan (+)</div>
            <div class="stat-value" style="color:#1E7A4C;">{format_rupiah(total_masuk)}</div>
        </div>
        <div class="stat-card out">
            <div class="stat-label">Total Pengeluaran Keseluruhan (-)</div>
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
# TAB 2: TRANSAKSI HARIAN
# ------------------------------------------
with tab2:
    if st.button("🔄 SINKRONKAN DENGAN GOOGLE SHEETS"):
        force_sync_with_sheets()
        st.rerun()

    if not df.empty:
        opsi_tgl = ["Semua tanggal"] + sorted(
            list(df["tanggal"].unique()), reverse=True
        )
        pilihan_tgl = st.selectbox("Filter Tanggal Transaksi", opsi_tgl)

        if pilihan_tgl != "Semua tanggal":
            df_filtered = df[df["tanggal"] == pilihan_tgl]

            df_before = df[df["tanggal"] < pilihan_tgl]
            saldo_awal_hari = (
                float(df_before.iloc[-1]["saldo"]) if not df_before.empty else 0.0
            )

            total_masuk_hari = float(
                df_filtered[df_filtered["jenis"] == "masuk"]["jumlah"].sum()
            )
            total_keluar_hari = float(
                df_filtered[df_filtered["jenis"] == "keluar"]["jumlah"].sum()
            )
            saldo_akhir_hari = float(df_filtered.iloc[-1]["saldo"])

            st.markdown(
                f"""
            <div class="saldo-banner">
                <div class="saldo-banner-title">SALDO AKHIR TANGGAL {pilihan_tgl}</div>
                <div class="saldo-banner-value">{format_rupiah(saldo_akhir_hari)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Saldo Awal (Sisa Sebelum Tanggal Ini)</div>
                <div class="stat-value">{format_rupiah(saldo_awal_hari)}</div>
            </div>
            <div class="stat-card in">
                <div class="stat-label">Pemasukan Tanggal Ini (+)</div>
                <div class="stat-value" style="color:#1E7A4C;">{format_rupiah(total_masuk_hari)}</div>
            </div>
            <div class="stat-card out">
                <div class="stat-label">Pengeluaran Tanggal Ini (-)</div>
                <div class="stat-value" style="color:#C2402A;">{format_rupiah(total_keluar_hari)}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            df_visible = df_filtered
        else:
            saldo_awal_hari = 0.0
            total_masuk_hari = float(df[df["jenis"] == "masuk"]["jumlah"].sum())
            total_keluar_hari = float(
                df[df["jenis"] == "keluar"]["jumlah"].sum()
            )
            saldo_akhir_hari = float(df.iloc[-1]["saldo"])

            st.markdown(
                f"""
            <div class="saldo-banner">
                <div class="saldo-banner-title">SALDO KAS SAAT INI (TOTAL)</div>
                <div class="saldo-banner-value">{format_rupiah(saldo_akhir_hari)}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            df_visible = df

        pdf_bytes = generate_pdf(
            df_visible,
            saldo_awal_hari,
            total_masuk_hari,
            total_keluar_hari,
            saldo_akhir_hari,
        )
        st.download_button(
            label="📄 CETAK / DOWNLOAD LAPORAN PDF",
            data=pdf_bytes,
            file_name=f"Laporan_Buku_Kas_{pilihan_tgl}.pdf",
            mime="application/pdf",
        )

        st.caption("--- DAFTAR TRANSAKSI ---")
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
                <div class="tx-saldo">Saldo Sisa: {format_rupiah(row['saldo'])}</div>
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
