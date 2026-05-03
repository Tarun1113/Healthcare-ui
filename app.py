"""
╔══════════════════════════════════════════════════════════════════╗
║   Healthcare Management System                                   ║
║   Databricks Custom App — Production Ready                       ║
║   Upload: app.py + requirements.txt → GitHub → Databricks App    ║
║   Database: SQLite (self-contained, zero setup)                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import sqlite3
import pandas as pd
import uuid
import os
from datetime import datetime, date, timedelta

# ─── Database ────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "healthcare.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name  TEXT NOT NULL,
        dob        TEXT,
        gender     TEXT,
        blood_type TEXT,
        phone      TEXT,
        email      TEXT,
        address    TEXT,
        emergency  TEXT,
        allergies  TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS appointments (
        appt_id    TEXT PRIMARY KEY,
        patient_id TEXT,
        doctor     TEXT,
        department TEXT,
        appt_date  TEXT,
        appt_time  TEXT,
        appt_type  TEXT,
        status     TEXT,
        fee        REAL,
        notes      TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS medical_records (
        record_id   TEXT PRIMARY KEY,
        patient_id  TEXT,
        appt_id     TEXT,
        doctor      TEXT,
        visit_date  TEXT,
        diagnosis   TEXT,
        symptoms    TEXT,
        prescription TEXT,
        bp          TEXT,
        temp        TEXT,
        weight      REAL,
        notes       TEXT,
        follow_up   TEXT,
        created_at  TEXT
    );
    CREATE TABLE IF NOT EXISTS medications (
        med_id       TEXT PRIMARY KEY,
        patient_id   TEXT,
        record_id    TEXT,
        med_name     TEXT,
        dosage       TEXT,
        frequency    TEXT,
        prescribed_by TEXT,
        start_date   TEXT,
        end_date     TEXT,
        instructions TEXT,
        status       TEXT,
        created_at   TEXT
    );
    """)
    # Seed demo data once
    if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
        t = str(date.today())
        conn.executemany("INSERT INTO patients VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", [
            ("PT-001","Ananya","Reddy","1990-05-14","Female","B+","9876543210","ananya@mail.com","12 MG Road, Bengaluru","Raj Reddy · 9876543211","Penicillin",t),
            ("PT-002","Kiran","Patil","1985-11-22","Male","O+","9845123456","kiran@mail.com","45 Station Rd, Dharwad","Sunita Patil · 9845123457","None",t),
            ("PT-003","Meera","Joshi","2000-03-08","Female","A+","9900001234","meera@mail.com","7 Tilak Nagar, Belgaum","Ravi Joshi · 9900001235","Sulfa drugs",t),
            ("PT-004","Suresh","Nair","1972-09-15","Male","AB+","9811122233","suresh@mail.com","22 Park Ave, Mysuru","Leela Nair · 9811122234","None",t),
        ])
        conn.executemany("INSERT INTO appointments VALUES(?,?,?,?,?,?,?,?,?,?,?)", [
            ("APT-001","PT-001","Dr. Anil Kumar","Cardiology",str(date.today()+timedelta(1)),"10:00","Consultation","Scheduled",800,"Chest pain & breathlessness",t),
            ("APT-002","PT-002","Dr. Priya Sharma","General Medicine",str(date.today()+timedelta(2)),"11:30","Follow-up","Confirmed",500,"BP & sugar follow-up",t),
            ("APT-003","PT-003","Dr. Rahul Mehta","Orthopaedics",str(date.today()+timedelta(3)),"09:00","Consultation","Scheduled",700,"Left knee pain",t),
            ("APT-004","PT-004","Dr. Kavita Iyer","Neurology",str(date.today()+timedelta(5)),"14:00","Routine Check-up","Confirmed",900,"Annual neuro checkup",t),
        ])
        conn.executemany("INSERT INTO medical_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
            ("REC-001","PT-001","APT-001","Dr. Anil Kumar",str(date.today()-timedelta(30)),"Hypertension Stage 1","Persistent headache, dizziness","Amlodipine 5mg once daily","145/90","98.6",72.5,"Reduce sodium intake, monitor BP weekly",str(date.today()+timedelta(30)),t),
            ("REC-002","PT-002","APT-002","Dr. Priya Sharma",str(date.today()-timedelta(15)),"Type 2 Diabetes Mellitus","Fatigue, frequent urination","Metformin 500mg twice daily","130/85","98.4",85.0,"HbA1c test in 3 months, low-carb diet",str(date.today()+timedelta(60)),t),
            ("REC-003","PT-003","APT-003","Dr. Rahul Mehta",str(date.today()-timedelta(7)),"Patellofemoral Pain Syndrome","Left knee pain on climbing stairs","Ibuprofen 400mg SOS, physiotherapy","120/78","98.2",58.0,"Physiotherapy 3x/week, avoid stairs",str(date.today()+timedelta(21)),t),
        ])
        conn.executemany("INSERT INTO medications VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", [
            ("MED-001","PT-001","REC-001","Amlodipine","5mg","Once daily","Dr. Anil Kumar",str(date.today()-timedelta(30)),str(date.today()+timedelta(60)),"Take after breakfast","Active",t),
            ("MED-002","PT-002","REC-002","Metformin","500mg","Twice daily","Dr. Priya Sharma",str(date.today()-timedelta(15)),str(date.today()+timedelta(75)),"Take with meals — breakfast & dinner","Active",t),
            ("MED-003","PT-003","REC-003","Ibuprofen","400mg","As needed","Dr. Rahul Mehta",str(date.today()-timedelta(7)),str(date.today()+timedelta(14)),"Take only on pain, max 2 tablets/day","Active",t),
        ])
    conn.commit()
    conn.close()

def run(sql, params=()):
    conn = get_conn()
    try:
        conn.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        conn.close()

def fetch(sql, params=()):
    conn = get_conn()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def one(sql, params=()):
    conn = get_conn()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def scalar(sql, params=()):
    conn = get_conn()
    try:
        return conn.execute(sql, params).fetchone()[0]
    finally:
        conn.close()

def uid(prefix):
    return f"{prefix}-{str(uuid.uuid4())[:6].upper()}"

# ─── Constants ────────────────────────────────────────────────────────────────
DOCTORS = [
    "Dr. Anil Kumar", "Dr. Priya Sharma", "Dr. Rahul Mehta",
    "Dr. Kavita Iyer", "Dr. Vikram Nair", "Dr. Sunita Patel",
    "Dr. Deepa Rao", "Dr. Arjun Singh",
]
DEPARTMENTS = [
    "General Medicine", "Cardiology", "Orthopaedics", "Gynaecology",
    "Paediatrics", "Neurology", "Dermatology", "ENT", "Ophthalmology",
]
APPT_STATUS = ["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"]
APPT_TYPES  = ["Consultation", "Follow-up", "Emergency", "Routine Check-up", "Lab Test"]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]
GENDERS     = ["Male", "Female", "Other", "Prefer not to say"]
FREQUENCIES = [
    "Once daily", "Twice daily", "Three times daily",
    "Every 8 hours", "Every 12 hours", "Weekly", "As needed",
]
MED_STATUS  = ["Active", "Completed", "Discontinued"]

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── App background ── */
.stApp { background: #f0f2f6 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0a1628 !important;
    border-right: none !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15);
}
[data-testid="stSidebar"] * { color: #b8c9e4 !important; }
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    display: flex; flex-direction: column; gap: 2px;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    padding: 11px 18px !important;
    border-radius: 10px !important;
    cursor: pointer !important;
    font-size: 13.5px !important;
    font-weight: 400 !important;
    letter-spacing: 0.1px !important;
    transition: all .2s ease !important;
    color: #8fa3c0 !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #e2eaf5 !important;
}
[data-testid="stSidebarContent"] hr { border-color: rgba(255,255,255,0.08) !important; }

/* ── Page header banner ── */
.page-header {
    background: linear-gradient(135deg, #0a1628 0%, #1a3356 50%, #0d2548 100%);
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid rgba(255,255,255,0.06);
}
.ph-icon { font-size: 30px; }
.ph-title { font-size: 20px; font-weight: 600; color: #ffffff; letter-spacing: -0.3px; }
.ph-sub   { font-size: 13px; color: #64a0d4; margin-top: 3px; font-weight: 400; }

/* ── Metric cards ── */
.metrics-row { display: flex; gap: 16px; margin-bottom: 28px; }
.metric-card {
    flex: 1;
    background: #ffffff;
    border-radius: 16px;
    padding: 22px 24px;
    border: 1px solid #e8ecf3;
    position: relative;
    overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.metric-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 0 0 16px 16px;
}
.mc-blue::after   { background: linear-gradient(90deg, #2563eb, #60a5fa); }
.mc-green::after  { background: linear-gradient(90deg, #16a34a, #4ade80); }
.mc-amber::after  { background: linear-gradient(90deg, #d97706, #fbbf24); }
.mc-rose::after   { background: linear-gradient(90deg, #e11d48, #fb7185); }
.metric-emoji { font-size: 26px; margin-bottom: 12px; }
.metric-label { font-size: 11.5px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; }
.metric-value { font-size: 36px; font-weight: 700; color: #0f172a; line-height: 1.1; margin-top: 4px; }

/* ── Section cards ── */
.section-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 0;
    border: 1px solid #e8ecf3;
    overflow: hidden;
    margin-bottom: 20px;
}
.section-card-header {
    padding: 16px 22px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 8px;
    background: #fafbfc;
}
.section-card-body { padding: 20px 22px; }

/* ── Form layout ── */
.form-wrapper {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px 26px;
    border: 1px solid #e8ecf3;
    margin-bottom: 16px;
}

/* ── Streamlit overrides ── */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    letter-spacing: 0.1px !important;
    height: 42px !important;
    transition: all .2s ease !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0a1628, #1a3356) !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(10,22,40,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(10,22,40,0.3) !important;
}
.stButton > button[kind="secondary"] {
    border-color: #e2e8f0 !important;
    color: #475569 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f8f9fc;
    border-radius: 12px;
    padding: 5px 6px;
    gap: 3px;
    border: 1px solid #e8ecf3;
    margin-bottom: 20px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    color: #64748b !important;
    transition: all .15s !important;
}
.stTabs [aria-selected="true"] {
    background: #0a1628 !important;
    color: #ffffff !important;
    box-shadow: 0 2px 8px rgba(10,22,40,0.2) !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea,
.stSelectbox > div > div,
.stNumberInput input, .stDateInput input {
    border-radius: 10px !important;
    border-color: #dde2ed !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13.5px !important;
    background: #fafbfc !important;
    transition: border-color .15s !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #2563eb !important;
    background: #ffffff !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}

/* ── Alerts ── */
.ok-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 12px 18px;
    color: #15803d;
    font-weight: 600;
    font-size: 13.5px;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 10px 0;
}
.err-box {
    background: #fff1f2;
    border: 1px solid #fca5a5;
    border-radius: 12px;
    padding: 12px 18px;
    color: #b91c1c;
    font-weight: 600;
    font-size: 13.5px;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 10px 0;
}
.info-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 12px 18px;
    color: #1d4ed8;
    font-size: 13px;
    margin: 10px 0;
    line-height: 1.5;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #e8ecf3 !important;
}
[data-testid="stDataFrame"] thead th {
    background: #0a1628 !important;
    color: #ffffff !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.4px !important;
    text-transform: uppercase !important;
    padding: 12px 16px !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) { background: #f8fafc !important; }
[data-testid="stDataFrame"] tbody tr:hover { background: #eff6ff !important; }

/* ── Dividers ── */
hr { border-color: #e8ecf3 !important; margin: 20px 0 !important; }

/* ── Labels ── */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label,
.stDateInput label, .stTimeInput label {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #374151 !important;
    letter-spacing: 0.1px !important;
}

/* ── Warning ── */
.stWarning {
    border-radius: 12px !important;
    border-left-color: #f59e0b !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Init DB ─────────────────────────────────────────────────────────────────
if "db_init" not in st.session_state:
    init_db()
    st.session_state.db_init = True

# ─── Helpers ─────────────────────────────────────────────────────────────────
def ok(msg):   st.markdown(f'<div class="ok-box">✅ {msg}</div>', unsafe_allow_html=True)
def err(msg):  st.markdown(f'<div class="err-box">❌ {msg}</div>', unsafe_allow_html=True)
def info(msg): st.markdown(f'<div class="info-box">ℹ️ {msg}</div>', unsafe_allow_html=True)

def page_header(icon, title, sub):
    st.markdown(f"""
    <div class="page-header">
        <div class="ph-icon">{icon}</div>
        <div>
            <div class="ph-title">{title}</div>
            <div class="ph-sub">{sub}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def patient_exists(pid):
    return one("SELECT patient_id FROM patients WHERE patient_id=?", (pid,)) is not None

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:24px 20px 16px">
        <div style="font-size:24px;font-weight:700;color:#fff;letter-spacing:-0.5px;line-height:1">
            🏥 HMS
        </div>
        <div style="font-size:11.5px;color:#4a6fa5;margin-top:5px;font-weight:500;letter-spacing:0.5px;text-transform:uppercase">
            Healthcare Management
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio("", [
        "📊   Dashboard",
        "👤   Patients",
        "📅   Appointments",
        "🩺   Medical Records",
        "💊   Medications",
    ])

    st.markdown("---")
    st.markdown("""
    <div style="padding:0 8px">
        <div style="font-size:10.5px;color:#334e72;text-transform:uppercase;letter-spacing:0.8px;font-weight:600;margin-bottom:10px">
            System Info
        </div>
        <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px 14px;border:1px solid rgba(255,255,255,0.06)">
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#60a5fa;margin-bottom:6px">
                healthcare.db
            </div>
            <div style="font-size:11px;color:#334e72">SQLite · self-contained</div>
            <div style="font-size:11px;color:#334e72;margin-top:2px">No SQL Warehouse needed</div>
        </div>
        <div style="margin-top:10px;display:flex;flex-direction:column;gap:3px">
            <div style="font-size:11px;color:#334e72">· patients</div>
            <div style="font-size:11px;color:#334e72">· appointments</div>
            <div style="font-size:11px;color:#334e72">· medical_records</div>
            <div style="font-size:11px;color:#334e72">· medications</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    page_header("📊", "Dashboard", "Real-time overview of your healthcare system")

    today = str(date.today())
    n_patients  = scalar("SELECT COUNT(*) FROM patients")
    n_today     = scalar("SELECT COUNT(*) FROM appointments WHERE appt_date=?", (today,))
    n_records   = scalar("SELECT COUNT(*) FROM medical_records")
    n_active_med= scalar("SELECT COUNT(*) FROM medications WHERE status='Active'")

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-card mc-blue">
            <div class="metric-emoji">👤</div>
            <div class="metric-label">Total Patients</div>
            <div class="metric-value">{n_patients}</div>
        </div>
        <div class="metric-card mc-green">
            <div class="metric-emoji">📅</div>
            <div class="metric-label">Today's Appointments</div>
            <div class="metric-value">{n_today}</div>
        </div>
        <div class="metric-card mc-amber">
            <div class="metric-emoji">🩺</div>
            <div class="metric-label">Medical Records</div>
            <div class="metric-value">{n_records}</div>
        </div>
        <div class="metric-card mc-rose">
            <div class="metric-emoji">💊</div>
            <div class="metric-label">Active Medications</div>
            <div class="metric-value">{n_active_med}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        st.markdown('<div class="section-card"><div class="section-card-header">📅 Upcoming Appointments — Next 7 Days</div><div class="section-card-body">', unsafe_allow_html=True)
        end_week = str(date.today() + timedelta(7))
        df_upcoming = fetch(
            "SELECT appt_id AS ID, patient_id AS Patient, doctor AS Doctor, "
            "department AS Dept, appt_date AS Date, appt_time AS Time, status AS Status "
            "FROM appointments WHERE appt_date BETWEEN ? AND ? "
            "ORDER BY appt_date, appt_time LIMIT 10",
            (today, end_week)
        )
        if not df_upcoming.empty:
            st.dataframe(df_upcoming, use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming appointments in the next 7 days.")
        st.markdown('</div></div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-card"><div class="section-card-header">👤 Recently Registered Patients</div><div class="section-card-body">', unsafe_allow_html=True)
        df_recent = fetch(
            "SELECT patient_id AS ID, first_name||' '||last_name AS Name, "
            "blood_type AS Blood, gender AS Gender "
            "FROM patients ORDER BY created_at DESC LIMIT 6"
        )
        if not df_recent.empty:
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        else:
            st.info("No patients registered yet.")
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-card-header">💊 Active Medications</div><div class="section-card-body">', unsafe_allow_html=True)
        df_meds = fetch(
            "SELECT patient_id AS Patient, med_name AS Medication, dosage AS Dose, frequency AS Frequency "
            "FROM medications WHERE status='Active' ORDER BY created_at DESC LIMIT 5"
        )
        if not df_meds.empty:
            st.dataframe(df_meds, use_container_width=True, hide_index=True)
        else:
            st.info("No active medications.")
        st.markdown('</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PATIENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Patients" in page:
    page_header("👤", "Patient Management", "Create · Read · Update · Delete")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    # ── CREATE ────────────────────────────────────────────────────────────────
    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Register New Patient")
        st.markdown("")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            p_fn    = st.text_input("First Name *")
            p_dob   = st.date_input("Date of Birth", value=date(1990, 1, 1), min_value=date(1900,1,1), max_value=date.today())
            p_blood = st.selectbox("Blood Type", BLOOD_TYPES)
            p_phone = st.text_input("Phone Number")
        with c2:
            p_ln    = st.text_input("Last Name *")
            p_gen   = st.selectbox("Gender", GENDERS)
            p_email = st.text_input("Email Address")
            p_addr  = st.text_area("Address", height=72)

        c3, c4 = st.columns(2, gap="large")
        with c3:
            p_emerg   = st.text_input("Emergency Contact (Name · Phone)")
        with c4:
            p_allergy = st.text_input("Known Allergies", placeholder="e.g. Penicillin, Sulfa drugs")

        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🏥  Register Patient", type="primary", use_container_width=True):
            if not p_fn.strip() or not p_ln.strip():
                err("First Name and Last Name are required.")
            else:
                new_pid = uid("PT")
                if run(
                    "INSERT INTO patients VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (new_pid, p_fn.strip(), p_ln.strip(), str(p_dob), p_gen,
                     p_blood, p_phone.strip(), p_email.strip(),
                     p_addr.strip(), p_emerg.strip(), p_allergy.strip(), str(date.today()))
                ):
                    ok(f"Patient **{p_fn} {p_ln}** registered successfully! &nbsp;ID: `{new_pid}`")

    # ── READ ──────────────────────────────────────────────────────────────────
    with tab_r:
        c1, c2 = st.columns([4, 1], gap="medium")
        with c1:
            srch = st.text_input("🔍 Search by name, patient ID or phone number", placeholder="Type anything...")
        with c2:
            limit = st.selectbox("Show", [10, 25, 50, 100])

        if srch.strip():
            s = f"%{srch.strip()}%"
            df = fetch(
                "SELECT patient_id AS 'Patient ID', first_name AS 'First Name', last_name AS 'Last Name', "
                "dob AS DOB, gender AS Gender, blood_type AS Blood, phone AS Phone, email AS Email, allergies AS Allergies "
                "FROM patients WHERE patient_id LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? "
                "ORDER BY created_at DESC LIMIT ?",
                (s, s, s, s, limit)
            )
        else:
            df = fetch(
                "SELECT patient_id AS 'Patient ID', first_name AS 'First Name', last_name AS 'Last Name', "
                "dob AS DOB, gender AS Gender, blood_type AS Blood, phone AS Phone, email AS Email, allergies AS Allergies "
                "FROM patients ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )

        if not df.empty:
            st.success(f"Found **{len(df)}** patient(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No patients found. Try a different search term.")

    # ── UPDATE ────────────────────────────────────────────────────────────────
    with tab_u:
        uid_val = st.text_input("Enter Patient ID to edit (e.g. PT-001)")

        if uid_val.strip():
            row = one("SELECT * FROM patients WHERE patient_id=?", (uid_val.strip(),))
            if row:
                info(f"Editing record for: **{row['first_name']} {row['last_name']}** &nbsp;|&nbsp; Blood: {row['blood_type']} &nbsp;|&nbsp; DOB: {row['dob']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)

                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_fn  = st.text_input("First Name", value=row['first_name'])
                    u_ph  = st.text_input("Phone", value=row['phone'] or "")
                    u_bt  = st.selectbox("Blood Type", BLOOD_TYPES,
                                         index=BLOOD_TYPES.index(row['blood_type']) if row['blood_type'] in BLOOD_TYPES else 8)
                with c2:
                    u_ln  = st.text_input("Last Name", value=row['last_name'])
                    u_em  = st.text_input("Email", value=row['email'] or "")
                    u_ad  = st.text_area("Address", value=row['address'] or "", height=72)

                c3, c4 = st.columns(2, gap="large")
                with c3:
                    u_al  = st.text_input("Allergies", value=row['allergies'] or "")
                with c4:
                    u_ec  = st.text_input("Emergency Contact", value=row['emergency'] or "")

                st.markdown('</div>', unsafe_allow_html=True)

                if st.button("💾  Save Changes", type="primary", use_container_width=True):
                    if run(
                        "UPDATE patients SET first_name=?,last_name=?,phone=?,email=?,"
                        "blood_type=?,address=?,allergies=?,emergency=? WHERE patient_id=?",
                        (u_fn.strip(), u_ln.strip(), u_ph.strip(), u_em.strip(),
                         u_bt, u_ad.strip(), u_al.strip(), u_ec.strip(), uid_val.strip())
                    ):
                        ok("Patient record updated successfully!")
            else:
                err(f"No patient found with ID: `{uid_val.strip()}`")

    # ── DELETE ────────────────────────────────────────────────────────────────
    with tab_d:
        st.warning("⚠️ Deleting a patient permanently removes all their appointments, medical records and medications.")
        del_id = st.text_input("Enter Patient ID to delete")

        if del_id.strip():
            row = one("SELECT * FROM patients WHERE patient_id=?", (del_id.strip(),))
            if row:
                info(
                    f"**{row['first_name']} {row['last_name']}** &nbsp;|&nbsp; "
                    f"DOB: {row['dob']} &nbsp;|&nbsp; Blood: {row['blood_type']} &nbsp;|&nbsp; Phone: {row['phone']}"
                )
                confirm = st.checkbox("I confirm I want to permanently delete this patient and all related data")
                if confirm:
                    if st.button("🗑️  Delete Patient", type="primary", use_container_width=True):
                        for tbl in ["medications", "medical_records", "appointments"]:
                            run(f"DELETE FROM {tbl} WHERE patient_id=?", (del_id.strip(),))
                        if run("DELETE FROM patients WHERE patient_id=?", (del_id.strip(),)):
                            ok(f"Patient `{del_id.strip()}` and all related records deleted.")
            else:
                err(f"No patient found with ID: `{del_id.strip()}`")

# ═══════════════════════════════════════════════════════════════════════════════
# APPOINTMENTS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Appointments" in page:
    page_header("📅", "Appointment Management", "Create · Read · Update · Delete")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Schedule New Appointment")
        st.markdown("")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            a_pid   = st.text_input("Patient ID *", placeholder="e.g. PT-001")
            a_doc   = st.selectbox("Doctor *", DOCTORS)
            a_date  = st.date_input("Appointment Date *", value=date.today() + timedelta(1), min_value=date.today())
            a_type  = st.selectbox("Appointment Type", APPT_TYPES)
        with c2:
            a_dept  = st.selectbox("Department *", DEPARTMENTS)
            a_time  = st.time_input("Appointment Time *", value=datetime.strptime("09:00", "%H:%M").time())
            a_stat  = st.selectbox("Status", APPT_STATUS)
            a_fee   = st.number_input("Consultation Fee (₹)", min_value=0, value=500, step=50)

        a_notes = st.text_area("Notes / Chief Complaint", placeholder="Describe the patient's main complaint or reason for visit...", height=80)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("📅  Schedule Appointment", type="primary", use_container_width=True):
            if not a_pid.strip():
                err("Patient ID is required.")
            elif not patient_exists(a_pid.strip()):
                err(f"Patient `{a_pid.strip()}` not found. Please register them first under 👤 Patients.")
            else:
                new_aid = uid("APT")
                if run(
                    "INSERT INTO appointments VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (new_aid, a_pid.strip(), a_doc, a_dept, str(a_date),
                     str(a_time), a_type, a_stat, a_fee, a_notes.strip(), str(date.today()))
                ):
                    ok(f"Appointment scheduled! &nbsp;ID: `{new_aid}` &nbsp;|&nbsp; {a_doc} &nbsp;|&nbsp; {str(a_date)}")

    with tab_r:
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1: f_pid  = st.text_input("Filter by Patient ID", placeholder="e.g. PT-001")
        with c2: f_doc  = st.selectbox("Filter by Doctor", ["All"] + DOCTORS)
        with c3: f_stat = st.selectbox("Filter by Status", ["All"] + APPT_STATUS)

        sql  = ("SELECT appt_id AS ID, patient_id AS Patient, doctor AS Doctor, department AS Dept, "
                "appt_date AS Date, appt_time AS Time, appt_type AS Type, status AS Status, fee AS 'Fee ₹' "
                "FROM appointments WHERE 1=1")
        prms = []
        if f_pid.strip():    sql += " AND patient_id=?";  prms.append(f_pid.strip())
        if f_doc  != "All":  sql += " AND doctor=?";      prms.append(f_doc)
        if f_stat != "All":  sql += " AND status=?";      prms.append(f_stat)
        sql += " ORDER BY appt_date DESC, appt_time DESC LIMIT 100"

        df = fetch(sql, tuple(prms))
        if not df.empty:
            st.success(f"Found **{len(df)}** appointment(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No appointments found with the current filters.")

    with tab_u:
        upd_id = st.text_input("Enter Appointment ID to edit (e.g. APT-001)")
        if upd_id.strip():
            row = one("SELECT * FROM appointments WHERE appt_id=?", (upd_id.strip(),))
            if row:
                info(f"**{row['appt_id']}** &nbsp;|&nbsp; Patient: {row['patient_id']} &nbsp;|&nbsp; Doctor: {row['doctor']} &nbsp;|&nbsp; Date: {row['appt_date']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)

                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_doc  = st.selectbox("Doctor", DOCTORS,
                                          index=DOCTORS.index(row['doctor']) if row['doctor'] in DOCTORS else 0)
                    u_dept = st.selectbox("Department", DEPARTMENTS,
                                          index=DEPARTMENTS.index(row['department']) if row['department'] in DEPARTMENTS else 0)
                    u_stat = st.selectbox("Status", APPT_STATUS,
                                          index=APPT_STATUS.index(row['status']) if row['status'] in APPT_STATUS else 0)
                with c2:
                    u_date = st.date_input("Date", value=datetime.strptime(row['appt_date'], "%Y-%m-%d").date())
                    u_fee  = st.number_input("Fee (₹)", value=int(row['fee'] or 500), step=50)

                u_notes = st.text_area("Notes", value=row['notes'] or "", height=80)
                st.markdown('</div>', unsafe_allow_html=True)

                if st.button("💾  Update Appointment", type="primary", use_container_width=True):
                    if run(
                        "UPDATE appointments SET doctor=?,department=?,appt_date=?,status=?,fee=?,notes=? WHERE appt_id=?",
                        (u_doc, u_dept, str(u_date), u_stat, u_fee, u_notes.strip(), upd_id.strip())
                    ):
                        ok("Appointment updated successfully!")
            else:
                err(f"No appointment found with ID: `{upd_id.strip()}`")

    with tab_d:
        del_id = st.text_input("Enter Appointment ID to delete")
        if del_id.strip():
            row = one("SELECT * FROM appointments WHERE appt_id=?", (del_id.strip(),))
            if row:
                info(
                    f"**{row['appt_id']}** &nbsp;|&nbsp; Patient: {row['patient_id']} &nbsp;|&nbsp; "
                    f"Doctor: {row['doctor']} &nbsp;|&nbsp; Date: {row['appt_date']} &nbsp;|&nbsp; Status: {row['status']}"
                )
                if st.button("🗑️  Delete Appointment", type="primary", use_container_width=True):
                    if run("DELETE FROM appointments WHERE appt_id=?", (del_id.strip(),)):
                        ok(f"Appointment `{del_id.strip()}` deleted.")
            else:
                err(f"No appointment found with ID: `{del_id.strip()}`")

# ═══════════════════════════════════════════════════════════════════════════════
# MEDICAL RECORDS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Medical" in page:
    page_header("🩺", "Medical Records", "Create · Read · Update · Delete")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Add Medical Record")
        st.markdown("")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            r_pid  = st.text_input("Patient ID *", placeholder="e.g. PT-001")
            r_doc  = st.text_input("Attending Doctor *", placeholder="e.g. Dr. Anil Kumar")
            r_date = st.date_input("Visit Date", value=date.today())
            r_diag = st.text_area("Diagnosis *", placeholder="Primary diagnosis...", height=80)
        with c2:
            r_aid  = st.text_input("Appointment ID (optional)", placeholder="e.g. APT-001")
            r_bp   = st.text_input("Blood Pressure", placeholder="e.g. 120/80 mmHg")
            r_temp = st.text_input("Temperature (°F)", placeholder="e.g. 98.6")
            r_wt   = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, step=0.5)

        r_sym  = st.text_area("Symptoms", placeholder="Describe reported symptoms...", height=72)
        r_rx   = st.text_area("Prescription / Treatment Plan", placeholder="Medications prescribed, dosages, instructions...", height=72)
        r_note = st.text_area("Doctor's Notes & Observations", placeholder="Additional clinical notes...", height=72)
        r_fup  = st.date_input("Follow-up Date", value=date.today() + timedelta(14))
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("💾  Save Medical Record", type="primary", use_container_width=True):
            if not r_pid.strip() or not r_doc.strip() or not r_diag.strip():
                err("Patient ID, Doctor and Diagnosis are required.")
            elif not patient_exists(r_pid.strip()):
                err(f"Patient `{r_pid.strip()}` not found.")
            else:
                new_rid = uid("REC")
                if run(
                    "INSERT INTO medical_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (new_rid, r_pid.strip(), r_aid.strip(), r_doc.strip(),
                     str(r_date), r_diag.strip(), r_sym.strip(), r_rx.strip(),
                     r_bp.strip(), r_temp.strip(), r_wt, r_note.strip(),
                     str(r_fup), str(date.today()))
                ):
                    ok(f"Medical record saved! &nbsp;ID: `{new_rid}` &nbsp;|&nbsp; Follow-up: {str(r_fup)}")

    with tab_r:
        c1, c2 = st.columns(2, gap="medium")
        with c1: s_pid = st.text_input("Filter by Patient ID", placeholder="e.g. PT-001")
        with c2: s_doc = st.text_input("Filter by Doctor Name", placeholder="e.g. Dr. Anil")

        sql  = ("SELECT record_id AS 'Record ID', patient_id AS Patient, doctor AS Doctor, "
                "visit_date AS 'Visit Date', diagnosis AS Diagnosis, bp AS BP, "
                "weight AS 'Wt (kg)', follow_up AS 'Follow-up' "
                "FROM medical_records WHERE 1=1")
        prms = []
        if s_pid.strip(): sql += " AND patient_id=?";         prms.append(s_pid.strip())
        if s_doc.strip(): sql += " AND doctor LIKE ?";         prms.append(f"%{s_doc.strip()}%")
        sql += " ORDER BY visit_date DESC LIMIT 100"

        df = fetch(sql, tuple(prms))
        if not df.empty:
            st.success(f"Found **{len(df)}** record(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No medical records found.")

    with tab_u:
        upd_id = st.text_input("Enter Record ID to edit (e.g. REC-001)")
        if upd_id.strip():
            row = one("SELECT * FROM medical_records WHERE record_id=?", (upd_id.strip(),))
            if row:
                info(f"**{row['record_id']}** &nbsp;|&nbsp; Patient: {row['patient_id']} &nbsp;|&nbsp; Doctor: {row['doctor']} &nbsp;|&nbsp; Visit: {row['visit_date']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)

                u_diag = st.text_area("Diagnosis", value=row['diagnosis'] or "", height=80)
                u_rx   = st.text_area("Prescription / Treatment", value=row['prescription'] or "", height=80)

                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_bp   = st.text_input("Blood Pressure", value=row['bp'] or "")
                    u_wt   = st.number_input("Weight (kg)", value=float(row['weight'] or 0), step=0.5)
                with c2:
                    u_temp = st.text_input("Temperature (°F)", value=row['temp'] or "")
                    u_fup  = st.date_input("Follow-up Date")

                u_note = st.text_area("Doctor's Notes", value=row['notes'] or "", height=80)
                st.markdown('</div>', unsafe_allow_html=True)

                if st.button("💾  Update Record", type="primary", use_container_width=True):
                    if run(
                        "UPDATE medical_records SET diagnosis=?,prescription=?,bp=?,temp=?,"
                        "weight=?,notes=?,follow_up=? WHERE record_id=?",
                        (u_diag.strip(), u_rx.strip(), u_bp.strip(), u_temp.strip(),
                         u_wt, u_note.strip(), str(u_fup), upd_id.strip())
                    ):
                        ok("Medical record updated successfully!")
            else:
                err(f"No record found with ID: `{upd_id.strip()}`")

    with tab_d:
        del_id = st.text_input("Enter Record ID to delete")
        if del_id.strip():
            row = one("SELECT * FROM medical_records WHERE record_id=?", (del_id.strip(),))
            if row:
                info(
                    f"**{row['record_id']}** &nbsp;|&nbsp; Patient: {row['patient_id']} &nbsp;|&nbsp; "
                    f"Doctor: {row['doctor']} &nbsp;|&nbsp; Diagnosis: {(row['diagnosis'] or '')[:50]}..."
                )
                if st.button("🗑️  Delete Record", type="primary", use_container_width=True):
                    if run("DELETE FROM medical_records WHERE record_id=?", (del_id.strip(),)):
                        ok(f"Medical record `{del_id.strip()}` deleted.")
            else:
                err(f"No record found with ID: `{del_id.strip()}`")

# ═══════════════════════════════════════════════════════════════════════════════
# MEDICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Medications" in page:
    page_header("💊", "Medication Management", "Create · Read · Update · Delete")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Add Medication")
        st.markdown("")

        c1, c2 = st.columns(2, gap="large")
        with c1:
            m_pid   = st.text_input("Patient ID *", placeholder="e.g. PT-001")
            m_name  = st.text_input("Medication Name *", placeholder="e.g. Amlodipine")
            m_dos   = st.text_input("Dosage", placeholder="e.g. 5mg, 500mg, 10ml")
            m_freq  = st.selectbox("Frequency", FREQUENCIES)
        with c2:
            m_rid   = st.text_input("Medical Record ID (optional)", placeholder="e.g. REC-001")
            m_doc   = st.text_input("Prescribed By *", placeholder="e.g. Dr. Anil Kumar")
            m_start = st.date_input("Start Date", value=date.today())
            m_end   = st.date_input("End Date", value=date.today() + timedelta(30))

        m_inst  = st.text_area("Special Instructions", placeholder="e.g. Take after meals, avoid alcohol...", height=72)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("💊  Add Medication", type="primary", use_container_width=True):
            if not m_pid.strip() or not m_name.strip() or not m_doc.strip():
                err("Patient ID, Medication Name and Doctor are required.")
            elif not patient_exists(m_pid.strip()):
                err(f"Patient `{m_pid.strip()}` not found.")
            elif m_end < m_start:
                err("End Date cannot be before Start Date.")
            else:
                new_mid = uid("MED")
                if run(
                    "INSERT INTO medications VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (new_mid, m_pid.strip(), m_rid.strip(), m_name.strip(),
                     m_dos.strip(), m_freq, m_doc.strip(),
                     str(m_start), str(m_end), m_inst.strip(), "Active", str(date.today()))
                ):
                    ok(f"Medication added! &nbsp;ID: `{new_mid}` &nbsp;|&nbsp; {m_name} {m_dos} — {m_freq}")

    with tab_r:
        c1, c2 = st.columns(2, gap="medium")
        with c1: mf_pid  = st.text_input("Filter by Patient ID", placeholder="e.g. PT-001")
        with c2: mf_stat = st.selectbox("Filter by Status", ["All"] + MED_STATUS)

        sql  = ("SELECT med_id AS ID, patient_id AS Patient, med_name AS Medication, "
                "dosage AS Dose, frequency AS Frequency, prescribed_by AS 'Prescribed By', "
                "start_date AS Start, end_date AS End, status AS Status "
                "FROM medications WHERE 1=1")
        prms = []
        if mf_pid.strip():     sql += " AND patient_id=?"; prms.append(mf_pid.strip())
        if mf_stat != "All":   sql += " AND status=?";     prms.append(mf_stat)
        sql += " ORDER BY created_at DESC LIMIT 100"

        df = fetch(sql, tuple(prms))
        if not df.empty:
            st.success(f"Found **{len(df)}** medication(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No medications found.")

    with tab_u:
        upd_id = st.text_input("Enter Medication ID to edit (e.g. MED-001)")
        if upd_id.strip():
            row = one("SELECT * FROM medications WHERE med_id=?", (upd_id.strip(),))
            if row:
                info(f"**{row['med_name']}** &nbsp;|&nbsp; Patient: {row['patient_id']} &nbsp;|&nbsp; Dose: {row['dosage']} &nbsp;|&nbsp; Status: {row['status']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)

                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_dos  = st.text_input("Dosage", value=row['dosage'] or "")
                    u_freq = st.selectbox("Frequency", FREQUENCIES,
                                          index=FREQUENCIES.index(row['frequency']) if row['frequency'] in FREQUENCIES else 0)
                with c2:
                    u_end  = st.date_input("End Date",
                                           value=datetime.strptime(row['end_date'], "%Y-%m-%d").date()
                                           if row['end_date'] else date.today() + timedelta(30))
                    u_stat = st.selectbox("Status", MED_STATUS,
                                          index=MED_STATUS.index(row['status']) if row['status'] in MED_STATUS else 0)

                u_inst = st.text_area("Instructions", value=row['instructions'] or "", height=80)
                st.markdown('</div>', unsafe_allow_html=True)

                if st.button("💾  Update Medication", type="primary", use_container_width=True):
                    if run(
                        "UPDATE medications SET dosage=?,frequency=?,end_date=?,status=?,instructions=? WHERE med_id=?",
                        (u_dos.strip(), u_freq, str(u_end), u_stat, u_inst.strip(), upd_id.strip())
                    ):
                        ok("Medication updated successfully!")
            else:
                err(f"No medication found with ID: `{upd_id.strip()}`")

    with tab_d:
        del_id = st.text_input("Enter Medication ID to delete")
        if del_id.strip():
            row = one("SELECT * FROM medications WHERE med_id=?", (del_id.strip(),))
            if row:
                info(
                    f"**{row['med_name']}** {row['dosage']} &nbsp;|&nbsp; "
                    f"Patient: {row['patient_id']} &nbsp;|&nbsp; Status: {row['status']} &nbsp;|&nbsp; "
                    f"Prescribed by: {row['prescribed_by']}"
                )
                if st.button("🗑️  Delete Medication", type="primary", use_container_width=True):
                    if run("DELETE FROM medications WHERE med_id=?", (del_id.strip(),)):
                        ok(f"Medication `{del_id.strip()}` deleted.")
            else:
                err(f"No medication found with ID: `{del_id.strip()}`")
