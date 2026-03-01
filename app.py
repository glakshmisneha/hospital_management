import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, timedelta, time

# =====================================================
# DATABASE CONNECTION (SAFE)
# =====================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# =====================================================
# INITIALIZE DATABASE + DEMO DATA
# =====================================================

def init_db():

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        email TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        specialist TEXT,
        nurse TEXT,
        start_time TEXT,
        end_time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS nurses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        shift_start TEXT,
        shift_end TEXT,
        allocated_doctor TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS patients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        blood_group TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS rooms(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_name TEXT UNIQUE,
        room_type TEXT,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        doctor TEXT,
        slot TEXT,
        date TEXT,
        amount REAL DEFAULT 0,
        room TEXT DEFAULT '',
        room_amount REAL DEFAULT 0
    )
    """)

    # Default Admin
    c.execute("""
    INSERT OR IGNORE INTO users
    VALUES ('admin@admin.com',
            ?,
            'Admin',
            'Super Admin')
    """, (hashlib.sha256("Admin@123".encode()).hexdigest(),))

    # DEMO DATA (Only if empty)
    if not pd.read_sql("SELECT * FROM doctors", conn).shape[0]:
        c.execute("""
        INSERT INTO doctors (name,email,specialist,nurse,start_time,end_time)
        VALUES ('Dr. Smith','drsmith@hospital.com','Cardiology','Nurse Mary','08:00:00','18:00:00')
        """)
        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                  ('drsmith@hospital.com',
                   hashlib.sha256("Doctor@123".encode()).hexdigest(),
                   'Doctor',
                   'Dr. Smith'))

    if not pd.read_sql("SELECT * FROM rooms", conn).shape[0]:
        c.execute("INSERT INTO rooms VALUES (NULL,'Room101','General','Available')")
        c.execute("INSERT INTO rooms VALUES (NULL,'Room102','Private','Available')")

    conn.commit()

init_db()

# =====================================================
# UTILITIES
# =====================================================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_slots(start, end):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while current < end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=20)
    return slots

# =====================================================
# UI STYLE
# =====================================================

st.set_page_config(layout="wide")

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);}
section[data-testid="stSidebar"]{background-color:#0d1117;}
div.stButton>button{
background:linear-gradient(90deg,#00c6ff,#0072ff);
border-radius:20px;color:white;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# =====================================================
# SESSION
# =====================================================

if "user" not in st.session_state:
    st.session_state.user = None

# =====================================================
# LOGIN / REGISTER
# =====================================================

if st.session_state.user is None:

    st.title("🏥 MediVista Hospital Portal")

    mode = st.radio("Login / Register", ["Login","Register"], horizontal=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Register":
        role = st.selectbox("Role", ["Patient"])
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?,?)",
                          (email,hash_password(password),role,email))
                conn.commit()
                st.success("Registered")
            except:
                st.warning("User exists")

    if mode == "Login":
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE email=? AND password=?",
                      (email,hash_password(password)))
            user = c.fetchone()
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

# =====================================================
# MAIN SYSTEM
# =====================================================

else:

    role = st.session_state.user[2]
    name = st.session_state.user[3]

    st.sidebar.title("MediVista")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ==================================================
    # ADMIN DASHBOARD
    # ==================================================

    if role == "Admin":

        st.title("📊 Hospital Dashboard")

        df = pd.read_sql("SELECT * FROM appointments", conn)
        revenue = df["amount"].sum() + df["room_amount"].sum() if not df.empty else 0

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Total Revenue", f"₹ {revenue}")
        col2.metric("Total Patients", len(pd.read_sql("SELECT * FROM patients", conn)))
        col3.metric("Total Doctors", len(pd.read_sql("SELECT * FROM doctors", conn)))
        col4.metric("Total Visits", len(df))

        if not df.empty:
            chart = df.groupby("date")[["amount","room_amount"]].sum().reset_index()
            chart["total"] = chart["amount"] + chart["room_amount"]
            fig = px.bar(chart, x="date", y="total", title="Daily Revenue")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointments yet. Book some to see analytics.")

    # ==================================================
    # RECEPTIONIST
    # ==================================================

    elif role == "Receptionist":

        st.title("Receptionist Panel")

        doctors = pd.read_sql("SELECT * FROM doctors", conn)

        if not doctors.empty:
            doctor = st.selectbox("Doctor", doctors["name"])
            patient = st.text_input("Patient Name")
            amount = st.number_input("Appointment Payment")
            slots = generate_slots(time(8,0), time(18,0))
            slot = st.selectbox("Slot", slots)

            if st.button("Book Appointment"):
                c.execute("""
                INSERT INTO appointments
                (patient,doctor,slot,date,amount,room,room_amount)
                VALUES (?,?,?,?,?,?,?)
                """,(patient,doctor,slot,str(datetime.now().date()),amount,"",0))
                conn.commit()
                st.success("Booked Successfully")
