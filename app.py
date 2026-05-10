"""
Healthcare Management System
Databricks Custom App — Unity Catalog Edition
CRUD via: Streamlit UI → SQL Warehouse → Unity Catalog Delta Tables
"""

import os
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date, timedelta
from databricks import sql as dbsql

# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION  (env vars auto-injected by Databricks Apps runtime)
# ─────────────────────────────────────────────────────────────────────────────
HOST      = os.environ.get("DATABRICKS_HOST", "").replace("https://", "")
HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "")
TOKEN     = os.environ.get("DATABRICKS_TOKEN", "")
CATALOG   = os.environ.get("DATABRICKS_CATALOG", "main")
SCHEMA    = os.environ.get("DATABRICKS_SCHEMA",  "healthcare_db")
TBL       = lambda t: f"`{CATALOG}`.`{SCHEMA}`.`{t}`"

@st.cache_resource(show_spinner="Connecting to Databricks…")
def get_conn():
    return dbsql.connect(
        server_hostname=HOST,
        http_path=HTTP_PATH,
        access_token=TOKEN,
        session_configuration={"spark.sql.ansi.enabled": "false"},
    )

def run_sql(sql: str, fetch: bool = False):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if fetch:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=cols)
            return True
    except Exception as e:
        st.error(f"❌ SQL Error: {e}")
        return pd.DataFrame() if fetch else False

def qdf(sql):  return run_sql(sql, fetch=True)
def qrun(sql): return run_sql(sql, fetch=False)
def esc(v):    return str(v).replace("'", "''") if v else ""
def uid(p):    return f"{p}-{str(uuid.uuid4())[:6].upper()}"

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DOCTORS     = ["Dr. Anil Kumar","Dr. Priya Sharma","Dr. Rahul Mehta","Dr. Kavita Iyer",
               "Dr. Vikram Nair","Dr. Sunita Patel","Dr. Deepa Rao","Dr. Arjun Singh"]
DEPARTMENTS = ["General Medicine","Cardiology","Orthopaedics","Gynaecology",
               "Paediatrics","Neurology","Dermatology","ENT","Ophthalmology"]
APPT_STATUS = ["Scheduled","Confirmed","Completed","Cancelled","No Show"]
APPT_TYPES  = ["Consultation","Follow-up","Emergency","Routine Check-up","Lab Test"]
BLOOD_TYPES = ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"]
GENDERS     = ["Male","Female","Other","Prefer not to say"]
FREQUENCIES = ["Once daily","Twice daily","Three times daily",
               "Every 8 hours","Every 12 hours","Weekly","As needed"]
MED_STATUS  = ["Active","Completed","Discontinued"]

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html,body,[class*="css"],.stApp{font-family:'Plus Jakarta Sans',sans-serif!important}
.stApp{background:#f0f2f6!important}

[data-testid="stSidebar"]{background:#0a1628!important;border-right:none!important;box-shadow:4px 0 20px rgba(0,0,0,.15)}
[data-testid="stSidebar"] *{color:#b8c9e4!important}
[data-testid="stSidebar"] .stRadio>label{display:none}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"]{display:flex;flex-direction:column;gap:2px}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label{padding:11px 18px!important;border-radius:10px!important;cursor:pointer!important;font-size:13.5px!important;font-weight:400!important;color:#8fa3c0!important;transition:all .2s!important}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover{background:rgba(255,255,255,.07)!important;color:#e2eaf5!important}
[data-testid="stSidebarContent"] hr{border-color:rgba(255,255,255,.08)!important}

.page-header{background:linear-gradient(135deg,#0a1628,#1a3356);border-radius:16px;padding:22px 28px;margin-bottom:24px;display:flex;align-items:center;gap:16px;border:1px solid rgba(255,255,255,.06)}
.ph-icon{font-size:30px}
.ph-title{font-size:20px;font-weight:600;color:#fff;letter-spacing:-.3px}
.ph-sub{font-size:13px;color:#64a0d4;margin-top:3px}
.ph-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.1);border-radius:20px;padding:4px 12px;font-size:11px;color:#93c5fd;margin-top:8px}

.metrics-row{display:flex;gap:16px;margin-bottom:28px}
.metric-card{flex:1;background:#fff;border-radius:16px;padding:22px 24px;border:1px solid #e8ecf3;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s}
.metric-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.08)}
.metric-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;border-radius:0 0 16px 16px}
.mc-blue::after{background:linear-gradient(90deg,#2563eb,#60a5fa)}
.mc-green::after{background:linear-gradient(90deg,#16a34a,#4ade80)}
.mc-amber::after{background:linear-gradient(90deg,#d97706,#fbbf24)}
.mc-rose::after{background:linear-gradient(90deg,#e11d48,#fb7185)}
.metric-emoji{font-size:26px;margin-bottom:12px}
.metric-label{font-size:11.5px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.8px}
.metric-value{font-size:36px;font-weight:700;color:#0f172a;line-height:1.1;margin-top:4px}

.section-card{background:#fff;border-radius:16px;border:1px solid #e8ecf3;overflow:hidden;margin-bottom:20px}
.section-card-header{padding:16px 22px;border-bottom:1px solid #f1f5f9;font-size:14px;font-weight:600;color:#1e293b;display:flex;align-items:center;gap:8px;background:#fafbfc}
.section-card-body{padding:20px 22px}

.form-wrapper{background:#fff;border-radius:16px;padding:24px 26px;border:1px solid #e8ecf3;margin-bottom:16px}

.stButton>button{border-radius:10px!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:600!important;font-size:13.5px!important;height:42px!important;transition:all .2s!important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#0a1628,#1a3356)!important;border:none!important;box-shadow:0 2px 8px rgba(10,22,40,.25)!important}
.stButton>button[kind="primary"]:hover{transform:translateY(-1px)!important;box-shadow:0 6px 18px rgba(10,22,40,.3)!important}
.stButton>button[kind="secondary"]{border-color:#e2e8f0!important;color:#475569!important}

.stTabs [data-baseweb="tab-list"]{background:#f8f9fc;border-radius:12px;padding:5px 6px;gap:3px;border:1px solid #e8ecf3;margin-bottom:20px}
.stTabs [data-baseweb="tab"]{border-radius:9px!important;font-size:13px!important;font-weight:500!important;padding:8px 18px!important;color:#64748b!important;transition:all .15s!important}
.stTabs [aria-selected="true"]{background:#0a1628!important;color:#fff!important;box-shadow:0 2px 8px rgba(10,22,40,.2)!important}

.stTextInput input,.stTextArea textarea,.stSelectbox>div>div,.stNumberInput input,.stDateInput input{border-radius:10px!important;border-color:#dde2ed!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-size:13.5px!important;background:#fafbfc!important}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:#2563eb!important;background:#fff!important;box-shadow:0 0 0 3px rgba(37,99,235,.1)!important}

.ok-box{background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:12px 18px;color:#15803d;font-weight:600;font-size:13.5px;display:flex;align-items:center;gap:8px;margin:10px 0}
.err-box{background:#fff1f2;border:1px solid #fca5a5;border-radius:12px;padding:12px 18px;color:#b91c1c;font-weight:600;font-size:13.5px;display:flex;align-items:center;gap:8px;margin:10px 0}
.info-box{background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px 18px;color:#1d4ed8;font-size:13px;margin:10px 0;line-height:1.5}

[data-testid="stDataFrame"]{border-radius:12px!important;overflow:hidden!important;border:1px solid #e8ecf3!important}
[data-testid="stDataFrame"] thead th{background:#0a1628!important;color:#fff!important;font-size:12px!important;font-weight:600!important;letter-spacing:.4px!important;text-transform:uppercase!important;padding:12px 16px!important}
[data-testid="stDataFrame"] tbody tr:nth-child(even){background:#f8fafc!important}
[data-testid="stDataFrame"] tbody tr:hover{background:#eff6ff!important}

.stTextInput label,.stTextArea label,.stSelectbox label,.stNumberInput label,.stDateInput label,.stTimeInput label{font-size:13px!important;font-weight:600!important;color:#374151!important;letter-spacing:.1px!important}
hr{border-color:#e8ecf3!important;margin:20px 0!important}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def ok(msg):   st.markdown(f'<div class="ok-box">✅ {msg}</div>', unsafe_allow_html=True)
def err(msg):  st.markdown(f'<div class="err-box">❌ {msg}</div>', unsafe_allow_html=True)
def info(msg): st.markdown(f'<div class="info-box">ℹ️ {msg}</div>', unsafe_allow_html=True)

def page_header(icon, title, sub, badge=None):
    b = f'<div class="ph-badge">🗄️ {badge}</div>' if badge else ""
    st.markdown(f"""
    <div class="page-header">
        <div class="ph-icon">{icon}</div>
        <div>
            <div class="ph-title">{title}</div>
            <div class="ph-sub">{sub}</div>
            {b}
        </div>
    </div>""", unsafe_allow_html=True)

def patient_exists(pid):
    df = qdf(f"SELECT patient_id FROM {TBL('patients')} WHERE patient_id='{esc(pid)}' LIMIT 1")
    return not df.empty

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:24px 20px 16px">
        <div style="font-size:24px;font-weight:700;color:#fff;letter-spacing:-.5px">🏥 HMS</div>
        <div style="font-size:11px;color:#4a6fa5;margin-top:5px;font-weight:500;text-transform:uppercase;letter-spacing:.5px">Healthcare Management</div>
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
    st.markdown(f"""
    <div style="padding:0 8px">
        <div style="font-size:10px;color:#334e72;text-transform:uppercase;letter-spacing:.8px;font-weight:600;margin-bottom:10px">Unity Catalog</div>
        <div style="background:rgba(255,255,255,.05);border-radius:10px;padding:12px 14px;border:1px solid rgba(255,255,255,.06)">
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#60a5fa;margin-bottom:6px">{CATALOG}.{SCHEMA}</div>
            <div style="font-size:11px;color:#334e72">Delta tables · persistent</div>
        </div>
        <div style="margin-top:10px;display:flex;flex-direction:column;gap:4px">
            {''.join([f'<div style="font-size:11px;color:#334e72">· {t}</div>' for t in ['patients','appointments','medical_records','medications']])}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
if "Dashboard" in page:
    page_header("📊", "Dashboard", "Live overview from Unity Catalog tables",
                f"{CATALOG}.{SCHEMA}")

    today = str(date.today())

    r_patients  = qdf(f"SELECT COUNT(*) AS n FROM {TBL('patients')}")
    r_today     = qdf(f"SELECT COUNT(*) AS n FROM {TBL('appointments')} WHERE appt_date='{today}'")
    r_records   = qdf(f"SELECT COUNT(*) AS n FROM {TBL('medical_records')}")
    r_meds      = qdf(f"SELECT COUNT(*) AS n FROM {TBL('medications')} WHERE status='Active'")

    n_p = int(r_patients['n'][0]) if not r_patients.empty else 0
    n_a = int(r_today['n'][0])    if not r_today.empty    else 0
    n_r = int(r_records['n'][0])  if not r_records.empty  else 0
    n_m = int(r_meds['n'][0])     if not r_meds.empty     else 0

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-card mc-blue">
            <div class="metric-emoji">👤</div>
            <div class="metric-label">Total Patients</div>
            <div class="metric-value">{n_p}</div>
        </div>
        <div class="metric-card mc-green">
            <div class="metric-emoji">📅</div>
            <div class="metric-label">Today's Appointments</div>
            <div class="metric-value">{n_a}</div>
        </div>
        <div class="metric-card mc-amber">
            <div class="metric-emoji">🩺</div>
            <div class="metric-label">Medical Records</div>
            <div class="metric-value">{n_r}</div>
        </div>
        <div class="metric-card mc-rose">
            <div class="metric-emoji">💊</div>
            <div class="metric-label">Active Medications</div>
            <div class="metric-value">{n_m}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown('<div class="section-card"><div class="section-card-header">📅 Upcoming Appointments — Next 7 Days</div><div class="section-card-body">', unsafe_allow_html=True)
        end = str(date.today() + timedelta(7))
        df = qdf(f"""SELECT appt_id AS ID, patient_id AS Patient, doctor AS Doctor,
                         department AS Dept, appt_date AS Date, appt_time AS Time, status AS Status
                     FROM {TBL('appointments')}
                     WHERE appt_date BETWEEN '{today}' AND '{end}'
                     ORDER BY appt_date, appt_time LIMIT 10""")
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.info("No upcoming appointments.")
        st.markdown('</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-card"><div class="section-card-header">👤 Recent Patients</div><div class="section-card-body">', unsafe_allow_html=True)
        df = qdf(f"""SELECT patient_id AS ID, concat(first_name,' ',last_name) AS Name,
                         blood_type AS Blood, gender AS Gender
                     FROM {TBL('patients')} ORDER BY created_at DESC LIMIT 5""")
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.info("No patients yet.")
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card"><div class="section-card-header">💊 Active Medications</div><div class="section-card-body">', unsafe_allow_html=True)
        df = qdf(f"""SELECT patient_id AS Patient, med_name AS Medication, dosage AS Dose
                     FROM {TBL('medications')} WHERE status='Active' LIMIT 5""")
        st.dataframe(df, use_container_width=True, hide_index=True) if not df.empty else st.info("No active medications.")
        st.markdown('</div></div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PATIENTS
# ═════════════════════════════════════════════════════════════════════════════
elif "Patients" in page:
    page_header("👤", "Patient Management", "Create · Read · Update · Delete",
                f"{CATALOG}.{SCHEMA}.patients")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    # ── CREATE ────────────────────────────────────────────────────────────────
    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Register New Patient")
        st.markdown("")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            p_fn    = st.text_input("First Name *")
            p_dob   = st.date_input("Date of Birth", value=date(1990,1,1), min_value=date(1900,1,1), max_value=date.today())
            p_blood = st.selectbox("Blood Type", BLOOD_TYPES)
            p_phone = st.text_input("Phone Number")
        with c2:
            p_ln    = st.text_input("Last Name *")
            p_gen   = st.selectbox("Gender", GENDERS)
            p_email = st.text_input("Email Address")
            p_addr  = st.text_area("Address", height=72)
        c3, c4 = st.columns(2, gap="large")
        with c3: p_emerg   = st.text_input("Emergency Contact (Name · Phone)")
        with c4: p_allergy = st.text_input("Known Allergies", placeholder="e.g. Penicillin, Sulfa drugs")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🏥  Register Patient", type="primary", use_container_width=True):
            if not p_fn.strip() or not p_ln.strip():
                err("First Name and Last Name are required.")
            else:
                new_id = uid("PT")
                sql = f"""INSERT INTO {TBL('patients')} VALUES (
                    '{new_id}','{esc(p_fn)}','{esc(p_ln)}','{p_dob}','{p_gen}',
                    '{p_blood}','{esc(p_phone)}','{esc(p_email)}','{esc(p_addr)}',
                    '{esc(p_emerg)}','{esc(p_allergy)}', current_timestamp()
                )"""
                if qrun(sql):
                    ok(f"Patient **{p_fn} {p_ln}** registered! &nbsp; ID: `{new_id}`")

    # ── READ ──────────────────────────────────────────────────────────────────
    with tab_r:
        c1, c2 = st.columns([4,1], gap="medium")
        with c1: srch = st.text_input("🔍 Search by name, patient ID or phone")
        with c2: lim  = st.selectbox("Show", [10,25,50,100])

        where = ""
        if srch.strip():
            s = esc(srch.strip())
            where = f"WHERE patient_id LIKE '%{s}%' OR first_name LIKE '%{s}%' OR last_name LIKE '%{s}%' OR phone LIKE '%{s}%'"

        df = qdf(f"""SELECT patient_id AS 'ID', first_name AS 'First Name', last_name AS 'Last Name',
                         dob AS 'DOB', gender AS 'Gender', blood_type AS 'Blood',
                         phone AS 'Phone', email AS 'Email', allergies AS 'Allergies'
                     FROM {TBL('patients')} {where}
                     ORDER BY created_at DESC LIMIT {lim}""")
        if not df.empty:
            st.success(f"Found **{len(df)}** patient(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No patients found.")

    # ── UPDATE ────────────────────────────────────────────────────────────────
    with tab_u:
        upd_id = st.text_input("Enter Patient ID to edit (e.g. PT-001)")
        if upd_id.strip():
            df = qdf(f"SELECT * FROM {TBL('patients')} WHERE patient_id='{esc(upd_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"Editing: **{r['first_name']} {r['last_name']}** &nbsp;|&nbsp; Blood: {r['blood_type']} &nbsp;|&nbsp; DOB: {r['dob']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_fn  = st.text_input("First Name", value=str(r['first_name'] or ""))
                    u_ph  = st.text_input("Phone",      value=str(r['phone'] or ""))
                    u_bt  = st.selectbox("Blood Type", BLOOD_TYPES,
                                         index=BLOOD_TYPES.index(r['blood_type']) if r['blood_type'] in BLOOD_TYPES else 8)
                with c2:
                    u_ln  = st.text_input("Last Name",  value=str(r['last_name'] or ""))
                    u_em  = st.text_input("Email",      value=str(r['email'] or ""))
                    u_ad  = st.text_area("Address",     value=str(r['address'] or ""), height=72)
                c3, c4 = st.columns(2, gap="large")
                with c3: u_al = st.text_input("Allergies",         value=str(r['allergies'] or ""))
                with c4: u_ec = st.text_input("Emergency Contact", value=str(r['emergency'] or ""))
                st.markdown('</div>', unsafe_allow_html=True)

                if st.button("💾  Save Changes", type="primary", use_container_width=True):
                    sql = f"""UPDATE {TBL('patients')} SET
                        first_name='{esc(u_fn)}', last_name='{esc(u_ln)}',
                        phone='{esc(u_ph)}', email='{esc(u_em)}',
                        blood_type='{u_bt}', address='{esc(u_ad)}',
                        allergies='{esc(u_al)}', emergency='{esc(u_ec)}'
                        WHERE patient_id='{esc(upd_id.strip())}'"""
                    if qrun(sql): ok("Patient record updated successfully!")
            else:
                err(f"No patient found with ID: `{upd_id.strip()}`")

    # ── DELETE ────────────────────────────────────────────────────────────────
    with tab_d:
        st.warning("⚠️ Deleting a patient also removes their appointments, records and medications.")
        del_id = st.text_input("Enter Patient ID to delete")
        if del_id.strip():
            df = qdf(f"SELECT * FROM {TBL('patients')} WHERE patient_id='{esc(del_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['first_name']} {r['last_name']}** &nbsp;|&nbsp; DOB: {r['dob']} &nbsp;|&nbsp; Blood: {r['blood_type']} &nbsp;|&nbsp; Phone: {r['phone']}")
                confirm = st.checkbox("I confirm permanent deletion of this patient and all their data")
                if confirm and st.button("🗑️  Delete Patient", type="primary", use_container_width=True):
                    pid = esc(del_id.strip())
                    for t in ["medications","medical_records","appointments"]:
                        qrun(f"DELETE FROM {TBL(t)} WHERE patient_id='{pid}'")
                    if qrun(f"DELETE FROM {TBL('patients')} WHERE patient_id='{pid}'"):
                        ok(f"Patient `{del_id.strip()}` and all related records deleted.")
            else:
                err(f"No patient found with ID: `{del_id.strip()}`")

# ═════════════════════════════════════════════════════════════════════════════
# APPOINTMENTS
# ═════════════════════════════════════════════════════════════════════════════
elif "Appointments" in page:
    page_header("📅", "Appointment Management", "Create · Read · Update · Delete",
                f"{CATALOG}.{SCHEMA}.appointments")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Schedule New Appointment")
        st.markdown("")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            a_pid  = st.text_input("Patient ID *", placeholder="e.g. PT-001")
            a_doc  = st.selectbox("Doctor *", DOCTORS)
            a_date = st.date_input("Date *", value=date.today()+timedelta(1), min_value=date.today())
            a_type = st.selectbox("Type", APPT_TYPES)
        with c2:
            a_dept = st.selectbox("Department *", DEPARTMENTS)
            a_time = st.time_input("Time *", value=datetime.strptime("09:00","%H:%M").time())
            a_stat = st.selectbox("Status", APPT_STATUS)
            a_fee  = st.number_input("Consultation Fee (₹)", min_value=0, value=500, step=50)
        a_notes = st.text_area("Notes / Chief Complaint", height=80)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("📅  Schedule Appointment", type="primary", use_container_width=True):
            if not a_pid.strip():
                err("Patient ID is required.")
            elif not patient_exists(a_pid.strip()):
                err(f"Patient `{a_pid.strip()}` not found. Register them first under 👤 Patients.")
            else:
                new_id = uid("APT")
                sql = f"""INSERT INTO {TBL('appointments')} VALUES (
                    '{new_id}','{esc(a_pid)}','{a_doc}','{a_dept}',
                    '{a_date}','{a_time}','{a_type}','{a_stat}',
                    {a_fee},'{esc(a_notes)}', current_timestamp()
                )"""
                if qrun(sql): ok(f"Appointment scheduled! &nbsp;ID: `{new_id}` &nbsp;| {a_doc} | {a_date}")

    with tab_r:
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1: f_pid  = st.text_input("Filter by Patient ID")
        with c2: f_doc  = st.selectbox("Filter by Doctor", ["All"]+DOCTORS)
        with c3: f_stat = st.selectbox("Filter by Status", ["All"]+APPT_STATUS)

        conds = ["1=1"]
        if f_pid.strip():   conds.append(f"patient_id='{esc(f_pid.strip())}'")
        if f_doc  != "All": conds.append(f"doctor='{f_doc}'")
        if f_stat != "All": conds.append(f"status='{f_stat}'")
        where = "WHERE " + " AND ".join(conds)

        df = qdf(f"""SELECT appt_id AS ID, patient_id AS Patient, doctor AS Doctor,
                         department AS Dept, appt_date AS Date, appt_time AS Time,
                         appt_type AS Type, status AS Status, fee AS 'Fee ₹'
                     FROM {TBL('appointments')} {where}
                     ORDER BY appt_date DESC LIMIT 100""")
        if not df.empty:
            st.success(f"Found **{len(df)}** appointment(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No appointments found.")

    with tab_u:
        upd_id = st.text_input("Enter Appointment ID (e.g. APT-001)")
        if upd_id.strip():
            df = qdf(f"SELECT * FROM {TBL('appointments')} WHERE appt_id='{esc(upd_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['appt_id']}** &nbsp;|&nbsp; Patient: {r['patient_id']} &nbsp;|&nbsp; Doctor: {r['doctor']} &nbsp;|&nbsp; Date: {r['appt_date']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_doc  = st.selectbox("Doctor", DOCTORS, index=DOCTORS.index(r['doctor']) if r['doctor'] in DOCTORS else 0)
                    u_dept = st.selectbox("Department", DEPARTMENTS, index=DEPARTMENTS.index(r['department']) if r['department'] in DEPARTMENTS else 0)
                    u_stat = st.selectbox("Status", APPT_STATUS, index=APPT_STATUS.index(r['status']) if r['status'] in APPT_STATUS else 0)
                with c2:
                    u_date = st.date_input("Date", value=datetime.strptime(str(r['appt_date']),"%Y-%m-%d").date())
                    u_fee  = st.number_input("Fee (₹)", value=int(float(r['fee'] or 500)), step=50)
                u_notes = st.text_area("Notes", value=str(r['notes'] or ""), height=80)
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("💾  Update Appointment", type="primary", use_container_width=True):
                    sql = f"""UPDATE {TBL('appointments')} SET
                        doctor='{u_doc}', department='{u_dept}', appt_date='{u_date}',
                        status='{u_stat}', fee={u_fee}, notes='{esc(u_notes)}'
                        WHERE appt_id='{esc(upd_id.strip())}'"""
                    if qrun(sql): ok("Appointment updated!")
            else:
                err(f"Appointment `{upd_id.strip()}` not found.")

    with tab_d:
        del_id = st.text_input("Enter Appointment ID to delete")
        if del_id.strip():
            df = qdf(f"SELECT * FROM {TBL('appointments')} WHERE appt_id='{esc(del_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['appt_id']}** &nbsp;|&nbsp; Patient: {r['patient_id']} &nbsp;|&nbsp; Doctor: {r['doctor']} &nbsp;|&nbsp; Date: {r['appt_date']} &nbsp;|&nbsp; Status: {r['status']}")
                if st.button("🗑️  Delete Appointment", type="primary", use_container_width=True):
                    if qrun(f"DELETE FROM {TBL('appointments')} WHERE appt_id='{esc(del_id.strip())}'"):
                        ok(f"Appointment `{del_id.strip()}` deleted.")
            else:
                err(f"Appointment `{del_id.strip()}` not found.")

# ═════════════════════════════════════════════════════════════════════════════
# MEDICAL RECORDS
# ═════════════════════════════════════════════════════════════════════════════
elif "Medical" in page:
    page_header("🩺", "Medical Records", "Create · Read · Update · Delete",
                f"{CATALOG}.{SCHEMA}.medical_records")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Add Medical Record")
        st.markdown("")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            r_pid  = st.text_input("Patient ID *", placeholder="e.g. PT-001")
            r_doc  = st.text_input("Attending Doctor *")
            r_date = st.date_input("Visit Date", value=date.today())
            r_diag = st.text_area("Diagnosis *", height=80)
        with c2:
            r_aid  = st.text_input("Appointment ID (optional)")
            r_bp   = st.text_input("Blood Pressure", placeholder="e.g. 120/80")
            r_temp = st.text_input("Temperature (°F)", placeholder="e.g. 98.6")
            r_wt   = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, step=0.5)
        r_sym  = st.text_area("Symptoms", height=72)
        r_rx   = st.text_area("Prescription / Treatment Plan", height=72)
        r_note = st.text_area("Doctor's Notes", height=72)
        r_fup  = st.date_input("Follow-up Date", value=date.today()+timedelta(14))
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("💾  Save Medical Record", type="primary", use_container_width=True):
            if not r_pid.strip() or not r_doc.strip() or not r_diag.strip():
                err("Patient ID, Doctor and Diagnosis are required.")
            elif not patient_exists(r_pid.strip()):
                err(f"Patient `{r_pid.strip()}` not found.")
            else:
                new_id = uid("REC")
                sql = f"""INSERT INTO {TBL('medical_records')} VALUES (
                    '{new_id}','{esc(r_pid)}','{esc(r_aid)}','{esc(r_doc)}',
                    '{r_date}','{esc(r_diag)}','{esc(r_sym)}','{esc(r_rx)}',
                    '{esc(r_bp)}','{esc(r_temp)}',{r_wt},'{esc(r_note)}',
                    '{r_fup}', current_timestamp()
                )"""
                if qrun(sql): ok(f"Medical record saved! &nbsp;ID: `{new_id}`")

    with tab_r:
        c1, c2 = st.columns(2, gap="medium")
        with c1: s_pid = st.text_input("Filter by Patient ID")
        with c2: s_doc = st.text_input("Filter by Doctor")

        conds = ["1=1"]
        if s_pid.strip(): conds.append(f"patient_id='{esc(s_pid.strip())}'")
        if s_doc.strip(): conds.append(f"doctor LIKE '%{esc(s_doc.strip())}%'")
        where = "WHERE " + " AND ".join(conds)

        df = qdf(f"""SELECT record_id AS ID, patient_id AS Patient, doctor AS Doctor,
                         visit_date AS 'Visit Date', diagnosis AS Diagnosis,
                         bp AS BP, weight AS 'Wt(kg)', follow_up AS 'Follow-up'
                     FROM {TBL('medical_records')} {where}
                     ORDER BY visit_date DESC LIMIT 100""")
        if not df.empty:
            st.success(f"Found **{len(df)}** record(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No records found.")

    with tab_u:
        upd_id = st.text_input("Enter Record ID (e.g. REC-001)")
        if upd_id.strip():
            df = qdf(f"SELECT * FROM {TBL('medical_records')} WHERE record_id='{esc(upd_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['record_id']}** &nbsp;|&nbsp; Patient: {r['patient_id']} &nbsp;|&nbsp; Doctor: {r['doctor']} &nbsp;|&nbsp; Visit: {r['visit_date']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
                u_diag = st.text_area("Diagnosis",              value=str(r['diagnosis'] or ""), height=80)
                u_rx   = st.text_area("Prescription/Treatment", value=str(r['prescription'] or ""), height=80)
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_bp   = st.text_input("Blood Pressure", value=str(r['bp'] or ""))
                    u_wt   = st.number_input("Weight (kg)",  value=float(r['weight'] or 0), step=0.5)
                with c2:
                    u_temp = st.text_input("Temperature",    value=str(r['temp'] or ""))
                    u_fup  = st.date_input("Follow-up Date")
                u_note = st.text_area("Doctor's Notes", value=str(r['notes'] or ""), height=80)
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("💾  Update Record", type="primary", use_container_width=True):
                    sql = f"""UPDATE {TBL('medical_records')} SET
                        diagnosis='{esc(u_diag)}', prescription='{esc(u_rx)}',
                        bp='{esc(u_bp)}', temp='{esc(u_temp)}',
                        weight={u_wt}, notes='{esc(u_note)}', follow_up='{u_fup}'
                        WHERE record_id='{esc(upd_id.strip())}'"""
                    if qrun(sql): ok("Medical record updated!")
            else:
                err(f"Record `{upd_id.strip()}` not found.")

    with tab_d:
        del_id = st.text_input("Enter Record ID to delete")
        if del_id.strip():
            df = qdf(f"SELECT * FROM {TBL('medical_records')} WHERE record_id='{esc(del_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['record_id']}** &nbsp;|&nbsp; Patient: {r['patient_id']} &nbsp;|&nbsp; Diagnosis: {str(r['diagnosis'] or '')[:60]}...")
                if st.button("🗑️  Delete Record", type="primary", use_container_width=True):
                    if qrun(f"DELETE FROM {TBL('medical_records')} WHERE record_id='{esc(del_id.strip())}'"):
                        ok(f"Record `{del_id.strip()}` deleted.")
            else:
                err(f"Record `{del_id.strip()}` not found.")

# ═════════════════════════════════════════════════════════════════════════════
# MEDICATIONS
# ═════════════════════════════════════════════════════════════════════════════
elif "Medications" in page:
    page_header("💊", "Medication Management", "Create · Read · Update · Delete",
                f"{CATALOG}.{SCHEMA}.medications")

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕  Create", "🔍  Read / Search", "✏️  Update", "🗑️  Delete"])

    with tab_c:
        st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
        st.markdown("#### 📋 Add Medication")
        st.markdown("")
        c1, c2 = st.columns(2, gap="large")
        with c1:
            m_pid   = st.text_input("Patient ID *",       placeholder="e.g. PT-001")
            m_name  = st.text_input("Medication Name *",  placeholder="e.g. Amlodipine")
            m_dos   = st.text_input("Dosage",             placeholder="e.g. 5mg")
            m_freq  = st.selectbox("Frequency", FREQUENCIES)
        with c2:
            m_rid   = st.text_input("Medical Record ID (optional)")
            m_doc   = st.text_input("Prescribed By *",    placeholder="e.g. Dr. Anil Kumar")
            m_start = st.date_input("Start Date", value=date.today())
            m_end   = st.date_input("End Date",   value=date.today()+timedelta(30))
        m_inst = st.text_area("Special Instructions", height=72)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("💊  Add Medication", type="primary", use_container_width=True):
            if not m_pid.strip() or not m_name.strip() or not m_doc.strip():
                err("Patient ID, Medication Name and Doctor are required.")
            elif not patient_exists(m_pid.strip()):
                err(f"Patient `{m_pid.strip()}` not found.")
            elif m_end < m_start:
                err("End Date cannot be before Start Date.")
            else:
                new_id = uid("MED")
                sql = f"""INSERT INTO {TBL('medications')} VALUES (
                    '{new_id}','{esc(m_pid)}','{esc(m_rid)}','{esc(m_name)}',
                    '{esc(m_dos)}','{m_freq}','{esc(m_doc)}',
                    '{m_start}','{m_end}','{esc(m_inst)}','Active', current_timestamp()
                )"""
                if qrun(sql): ok(f"Medication added! &nbsp;ID: `{new_id}` &nbsp;| {m_name} {m_dos} — {m_freq}")

    with tab_r:
        c1, c2 = st.columns(2, gap="medium")
        with c1: mf_pid  = st.text_input("Filter by Patient ID")
        with c2: mf_stat = st.selectbox("Filter by Status", ["All"]+MED_STATUS)

        conds = ["1=1"]
        if mf_pid.strip():     conds.append(f"patient_id='{esc(mf_pid.strip())}'")
        if mf_stat != "All":   conds.append(f"status='{mf_stat}'")
        where = "WHERE " + " AND ".join(conds)

        df = qdf(f"""SELECT med_id AS ID, patient_id AS Patient, med_name AS Medication,
                         dosage AS Dose, frequency AS Frequency, prescribed_by AS 'Prescribed By',
                         start_date AS Start, end_date AS End, status AS Status
                     FROM {TBL('medications')} {where}
                     ORDER BY created_at DESC LIMIT 100""")
        if not df.empty:
            st.success(f"Found **{len(df)}** medication(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No medications found.")

    with tab_u:
        upd_id = st.text_input("Enter Medication ID (e.g. MED-001)")
        if upd_id.strip():
            df = qdf(f"SELECT * FROM {TBL('medications')} WHERE med_id='{esc(upd_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['med_name']}** &nbsp;|&nbsp; Patient: {r['patient_id']} &nbsp;|&nbsp; Dose: {r['dosage']} &nbsp;|&nbsp; Status: {r['status']}")
                st.markdown('<div class="form-wrapper">', unsafe_allow_html=True)
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    u_dos  = st.text_input("Dosage", value=str(r['dosage'] or ""))
                    u_freq = st.selectbox("Frequency", FREQUENCIES,
                                          index=FREQUENCIES.index(r['frequency']) if r['frequency'] in FREQUENCIES else 0)
                with c2:
                    u_end  = st.date_input("End Date",
                                           value=datetime.strptime(str(r['end_date']),"%Y-%m-%d").date() if r['end_date'] else date.today()+timedelta(30))
                    u_stat = st.selectbox("Status", MED_STATUS,
                                          index=MED_STATUS.index(r['status']) if r['status'] in MED_STATUS else 0)
                u_inst = st.text_area("Instructions", value=str(r['instructions'] or ""), height=80)
                st.markdown('</div>', unsafe_allow_html=True)
                if st.button("💾  Update Medication", type="primary", use_container_width=True):
                    sql = f"""UPDATE {TBL('medications')} SET
                        dosage='{esc(u_dos)}', frequency='{u_freq}', end_date='{u_end}',
                        status='{u_stat}', instructions='{esc(u_inst)}'
                        WHERE med_id='{esc(upd_id.strip())}'"""
                    if qrun(sql): ok("Medication updated!")
            else:
                err(f"Medication `{upd_id.strip()}` not found.")

    with tab_d:
        del_id = st.text_input("Enter Medication ID to delete")
        if del_id.strip():
            df = qdf(f"SELECT * FROM {TBL('medications')} WHERE med_id='{esc(del_id.strip())}' LIMIT 1")
            if not df.empty:
                r = df.iloc[0]
                info(f"**{r['med_name']}** {r['dosage']} &nbsp;|&nbsp; Patient: {r['patient_id']} &nbsp;|&nbsp; Status: {r['status']}")
                if st.button("🗑️  Delete Medication", type="primary", use_container_width=True):
                    if qrun(f"DELETE FROM {TBL('medications')} WHERE med_id='{esc(del_id.strip())}'"):
                        ok(f"Medication `{del_id.strip()}` deleted.")
            else:
                err(f"Medication `{del_id.strip()}` not found.")
