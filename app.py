import io
import json
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

# ReportLab untuk PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

WIB = timezone(timedelta(hours=7))

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS DARK MODERN
# ==========================================
st.set_page_config(
    page_title="KasKu - Buku Kas Harian",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Global Theme */
    html, body, [class*="css"], .stApp {
        background-color: #0b111e !important;
        color: #94a3b8 !important;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Hilangkan padding default streamlit */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 680px !important;
    }

    /* Modal / Card Login Dark */
    .login-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 32px 24px;
        max-width: 380px;
        margin: 40px auto 20px auto;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .login-icon {
        width: 54px;
        height: 54px;
        background: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        margin-bottom: 16px;
    }
    .login-title {
        color: #ffffff;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .login-desc {
        font-size: 12px;
        color: #64748b;
        margin-bottom: 20px;
    }

    /* Top Navigation Bar */
    .navbar {
        background-color: #0d1527;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 18px;
    }
    .brand-title {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-title span { color: #3b82f6; }

    /* Summary Dashboard Cards */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-bottom: 18px;
    }
    @media (max-width: 600px) {
        .summary-grid { grid-template-columns: 1fr; }
    }
    .summary-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px 16px;
    }
    .card-title {
        font-size: 11px;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .card-value {
        font-size: 17px;
        font-weight: 700;
    }
    .card-value.balance { color: #3b82f6; }
    .card-value.income { color: #10b981; }
    .card-value.expense { color: #ef4444; }

    /* Form Container Dark */
    .form-box {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
    }

    /* Input Streamlit Styling */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stDateInput"] input,
    div[data-testid="stTimeInput"] input {
        background-color: #131b2e !important;
        border: 1px solid #1e293b !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-size: 13px !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stTimeInput"] label,
    div[data-testid="stRadio"] label {
        color: #94a3b8 !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }

    /* Tombol Biru KasKu */
    div[data-testid="stFormSubmitButton"] button, 
    .stButton>button, 
    .stDownloadButton>button {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 16px !important;
        width: 100% !important;
        transition: 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover, 
    .stButton>button:hover,
    .stDownloadButton>button:hover {
        background-color: #2563eb !important;
    }

    /* Tabel Transaksi Dark */
    .tx-table-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .user-name-tag {
        color: #38bdf8;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .tx-desc-text {
        color: #f1f5f9;
        font-size: 13px;
        font-weight: 600;
        margin-top: 2px;
    }
    .tx-sub-info {
        font-size: 11px;
        color: #64748b;
    }
    .badge-in {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .badge-out {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. SISTEM LOGIN / PIN AKUN
# ==========================================
USER_ACCOUNTS = {
    "admin": {"password": "admin123", "nama": "Administrator", "role": "admin"},
    "firmansyah": {"password": "user123", "nama": "Firmansyah", "role": "user"},
    "melia": {"password": "user123", "nama": "Melia", "role": "user"},
    "mamah": {"password": "user123", "nama": "Mamah", "role": "user"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_name = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown(
        """
    <div class="login-card">
        <div class="login-icon"><i class="fa-solid fa-lock"></i></div>
        <div class="login-title">Kunci Aplikasi Kas</div>
        <div class="login-desc">Masukkan Username & Password untuk membuka catatan kas harian kamu.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    with st.form("form_login"):
        u_input = st.text_input("Username", placeholder="Masukkan username")
        p_input = st.text_input("Password", type="password", placeholder="Masukkan password")
        btn_login = st.form_submit_button("Buka Kunci")

        if btn_login:
            clean_u = u_input.strip().lower()
            clean_p = p_input.strip()
            if clean_u in USER_ACCOUNTS and USER_ACCOUNTS[clean_u]["password"] == clean_p:
                st.session_state.logged_in = True
                st.session_state.username = clean_u
                st.session_state.user_name = USER_ACCOUNTS[clean_u]["nama"]
                st.session_state.role = USER_ACCOUNTS[clean_u]["role"]
                st.rerun()
            else:
                st.error("Username atau Password salah!")
    st.stop()

# ==========================================
# 3. KONEKSI GOOGLE SHEETS & DATABASE
# ==========================================
try:
    API_URL = st.secrets["connections"]["gsheets"]["api_url"]
except Exception:
    API_URL = ""

def get_db():
    return sqlite3.connect("buku_kas.db", check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id TEXT PRIMARY KEY,
            nama TEXT,
            tanggal TEXT,
            waktu TEXT,
            kategori TEXT,
            keterangan TEXT,
            jenis TEXT,
            jumlah REAL
        )
    """)
    conn.commit()

    c.execute("PRAGMA table_info(transaksi)")
    cols = [col[1] for col in c.fetchall()]
    if "nama" not in cols:
        try:
            c.execute("ALTER TABLE transaksi ADD COLUMN nama TEXT DEFAULT '-'")
            conn.commit()
        except Exception:
            pass

    conn.close()

init_db()

def clean_amount(val):
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val)
    digits = re.sub(r"[^\d.]", "", val_str)
    try:
        return float(digits) if digits else 0.0
    except Exception:
        return 0.0

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
            res = requests.get(API_URL, timeout=8, allow_redirects=True)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
    return None

def force_mirror_sheets():
    if API_URL:
        sheets_data = fetch_from_sheets()
        if sheets_data is not None:
            if isinstance(sheets_data, list):
                txs = sheets_data
            elif isinstance(sheets_data, dict):
                txs = sheets_data.get("transaksi", sheets_data.get("data", []))
            else:
                txs = []

            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM transaksi")

            for idx, item in enumerate(txs):
                if isinstance(item, dict):
                    try:
                        tx_id = str(item.get("id") or (idx + 1))
                        nama = str(item.get("nama", "-")).strip()
                        tgl = clean_date_str(item.get("tanggal", ""))
                        waktu = clean_time_str(item.get("waktu", ""))
                        kategori = str(item.get("kategori", ""))
                        keterangan = str(item.get("keterangan", ""))
                        jenis = str(item.get("jenis", "")).lower().strip()
                        jumlah = clean_amount(item.get("jumlah", 0))

                        c.execute(
                            "INSERT OR REPLACE INTO transaksi (id, nama, tanggal, waktu, kategori, keterangan, jenis, jumlah) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (tx_id, nama, tgl, waktu, kategori, keterangan, jenis, jumlah),
                        )
                    except Exception:
                        continue
            conn.commit()
            conn.close()

def load_data():
    if API_URL:
        force_mirror_sheets()

    conn = get_db()
    try:
        df = pd.read_sql_query("SELECT * FROM transaksi", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()

    if not df.empty:
        df["jumlah"] = pd.to_numeric(df["jumlah"], errors="coerce").fillna(0.0)
        df["jenis"] = df["jenis"].astype(str).str.strip().str.lower()
        if "nama" not in df.columns:
            df["nama"] = "-"

        if st.session_state.role != "admin":
            target = st.session_state.user_name.lower().strip()
            df = df[df["nama"].astype(str).str.lower().str.strip() == target].copy()

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
    else:
        df = pd.DataFrame(columns=["id", "nama", "tanggal", "waktu", "kategori", "keterangan", "jenis", "jumlah", "saldo"])

    return df

def format_rupiah(n):
    return f"Rp {float(n or 0):,.0f}".replace(",", ".")

def add_data(nama_str, tgl_str, waktu_str, kategori, keterangan, jenis, jumlah):
    new_id = str(int(time.time() * 1000))
    
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO transaksi (id, nama, tanggal, waktu, kategori, keterangan, jenis, jumlah) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (new_id, str(nama_str), str(tgl_str), str(waktu_str), str(kategori), str(keterangan), str(jenis), float(jumlah)),
    )
    conn.commit()
    conn.close()

    if API_URL and "script.google.com" in API_URL:
        try:
            payload = {
                "action": "ADD",
                "id": new_id,
                "nama": nama_str,
                "tanggal": tgl_str,
                "waktu": waktu_str,
                "kategori": kategori,
                "keterangan": keterangan,
                "jenis": jenis,
                "jumlah": float(jumlah),
            }
            headers = {"Content-Type": "application/json"}
            requests.post(
                API_URL, 
                data=json.dumps(payload), 
                headers=headers, 
                timeout=10, 
                allow_redirects=True
            )
        except Exception:
            pass

def delete_data(tx_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM transaksi WHERE id = ?", (str(tx_id),))
    conn.commit()
    conn.close()

    if API_URL and "script.google.com" in API_URL:
        try:
            payload = {"action": "DELETE", "id": str(tx_id)}
            headers = {"Content-Type": "application/json"}
            requests.post(
                API_URL, 
                data=json.dumps(payload), 
                headers=headers, 
                timeout=10, 
                allow_redirects=True
            )
        except Exception:
            pass

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
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#1e293b")),
        ])
    )
    elements.append(t_summary)
    elements.append(Spacer(1, 15))

    table_data = [
        ["Nama", "Tanggal", "Waktu", "Kategori", "Keterangan", "Jenis", "Nominal"]
    ]
    if not df_pdf.empty:
        for idx, row in df_pdf.iterrows():
            table_data.append([
                str(row.get("nama", "-")),
                str(row["tanggal"]),
                str(row["waktu"]),
                str(row["kategori"]),
                str(row["keterangan"]),
                str(row["jenis"]).upper(),
                format_rupiah(row["jumlah"]),
            ])

    t_tx = Table(table_data, colWidths=[75, 55, 40, 75, 120, 50, 85])
    t_tx.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#38bdf8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_tx)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. NAVBAR HEADER APLIKASI
# ==========================================
df = load_data()
today_str = str(datetime.now(WIB).date())

col_n1, col_n2 = st.columns([3, 1])
with col_n1:
    st.markdown(
        f"""
    <div class="brand-title">
        <i class="fa-solid fa-wallet" style="color:#3b82f6;"></i> Kas<span>Ku</span>
        <span style="font-size:12px; color:#64748b; font-weight:400; margin-left:6px;">({st.session_state.user_name})</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
with col_n2:
    if st.button("🔒 Kunci"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_name = ""
        st.session_state.role = ""
        st.rerun()

# ==========================================
# 5. RINGKASAN SALDO (SUMMARY CARDS)
# ==========================================
total_masuk = float(df[df["jenis"] == "masuk"]["jumlah"].sum()) if not df.empty else 0.0
total_keluar = float(df[df["jenis"] == "keluar"]["jumlah"].sum()) if not df.empty else 0.0
saldo_total = float(df.iloc[-1]["saldo"]) if not df.empty else 0.0

st.markdown(
    f"""
<div class="summary-grid">
    <div class="summary-card">
        <div class="card-title">Sisa Saldo Kas</div>
        <div class="card-value balance">{format_rupiah(saldo_total)}</div>
    </div>
    <div class="summary-card">
        <div class="card-title">Total Pemasukan</div>
        <div class="card-value income">{format_rupiah(total_masuk)}</div>
    </div>
    <div class="summary-card">
        <div class="card-title">Total Pengeluaran</div>
        <div class="card-value expense">{format_rupiah(total_keluar)}</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 6. TAB NAVIGASI UTAMA
# ==========================================
tab_input, tab_history = st.tabs(["➕ Catat Transaksi", "📜 Riwayat Kas"])

# ------------------------------------------
# TAB 1: FORM INPUT TRANSAKSI
# ------------------------------------------
with tab_input:
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
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.session_state.role == "admin":
                nama = st.text_input("Nama / Pihak Terkait", placeholder="Contoh: Firmansyah / Toko Ani")
            else:
                nama = st.text_input("Nama / Pihak Terkait", value=st.session_state.user_name, disabled=True)
        with col_f2:
            kategori = st.selectbox("Kategori", kategori_list)

        keterangan = st.text_input("Keterangan", placeholder="Contoh: Iuran Kas / Beli ATK")

        col_f3, col_f4 = st.columns(2)
        with col_f3:
            jumlah = st.number_input("Nominal (Rp)", min_value=0.0, step=10000.0)
        with col_f4:
            jenis = st.selectbox(
                "Jenis", 
                ["masuk", "keluar"], 
                format_func=lambda x: "Pemasukan (+)" if x == "masuk" else "Pengeluaran (-)"
            )

        submit = st.form_submit_button("➕ Simpan Transaksi")

        if submit:
            final_nama = st.session_state.user_name if st.session_state.role != "admin" else nama.strip()
            if not final_nama:
                st.error("Isi Nama terlebih dahulu.")
            elif jumlah <= 0:
                st.error("Isi nominal transaksi terlebih dahulu.")
            else:
                tgl_str = today_str
                waktu_str = now_wib.strftime("%H:%M")
                add_data(final_nama, tgl_str, waktu_str, kategori, keterangan or "-", jenis, jumlah)
                st.success(f"Transaksi atas nama {final_nama} berhasil dicatat! ✓")
                st.rerun()

# ------------------------------------------
# TAB 2: RIWAYAT & TABEL TRANSAKSI
# ------------------------------------------
with tab_history:
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🔄 Sinkronkan Data"):
            force_mirror_sheets()
            st.rerun()

    if not df.empty and len(df) > 0:
        pdf_bytes = generate_pdf(df, 0.0, total_masuk, total_keluar, saldo_total)
        with col_btn2:
            st.download_button(
                label="📄 Unduh Laporan PDF",
                data=pdf_bytes,
                file_name=f"Laporan_Kas_{today_str}.pdf",
                mime="application/pdf",
            )

        st.caption(f"Daftar Transaksi ({len(df)} Data)")
        for idx, row in df.iloc[::-1].iterrows():
            is_masuk = row["jenis"] == "masuk"
            badge_cls = "badge-in" if is_masuk else "badge-out"
            sign = "+" if is_masuk else "-"
            color_amt = "#34d399" if is_masuk else "#f87171"

            col_card, col_del = st.columns([6, 1])
            with col_card:
                st.markdown(
                    f"""
                <div class="tx-table-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="user-name-tag">
                            <i class="fa-regular fa-user"></i> {row.get('nama', '-')}
                        </div>
                        <span class="{badge_cls}">{'Pemasukan' if is_masuk else 'Pengeluaran'}</span>
                    </div>
                    <div class="tx-desc-text">{row['keterangan'] or '-'}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                        <span class="tx-sub_info" style="font-size:11px; color:#64748b;">📅 {row['tanggal']} • {row['waktu']} WIB • <em style="color:#94a3b8;">{row['kategori']}</em></span>
                        <span style="color:{color_amt}; font-weight:700; font-size:13px;">{sign}{format_rupiah(row['jumlah'])}</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            with col_del:
                st.write("")
                if st.button("🗑️", key=f"del_{row['id']}", help="Hapus transaksi"):
                    delete_data(row["id"])
                    st.rerun()
    else:
        st.info("Belum ada catatan transaksi kas.")
