import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, timedelta, time

# ======================================================
# DATABASE CONNECTION (SAFE)
# ======================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# ======================================================
# INITIALIZE DATABASE (SCHEMA SAFE)
# ======================================================

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS queries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        target TEXT,
        message TEXT
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

    conn.commit()

init_db()

# ======================================================
# UTILITIES
# ======================================================

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

# ======================================================
# UI STYLE
# ======================================================

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

# ======================================================
# SESSION
# ======================================================

if "user" not in st.session_state:
    st.session_state.user = None

# ======================================================
# LOGIN / REGISTER
# ======================================================

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
                st.success("Registered Successfully")
            except:
                st.warning("User already exists")

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

# ======================================================
# MAIN SYSTEM
# ======================================================

else:

    role = st.session_state.user[2]
    name = st.session_state.user[3]

    st.sidebar.title("MediVista")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ==================================================
    # ADMIN PANEL
    # ==================================================

    if role == "Admin":

        page = st.sidebar.radio("Navigation",
            ["Dashboard","Doctors","Nurses","Rooms","Staff Registration","Queries"])

        # ---------------- DASHBOARD ----------------
        if page == "Dashboard":

            st.title("📊 Hospital Analytics Dashboard")

            df_app = pd.read_sql("SELECT * FROM appointments", conn)
            df_doc = pd.read_sql("SELECT * FROM doctors", conn)
            df_pat = pd.read_sql("SELECT * FROM patients", conn)

            revenue = df_app["amount"].sum() + df_app["room_amount"].sum() if not df_app.empty else 0

            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Total Revenue", f"₹ {revenue}")
            col2.metric("Total Patients", len(df_pat))
            col3.metric("Total Doctors", len(df_doc))
            col4.metric("Total Visits", len(df_app))

            if not df_app.empty:

                rev_chart = df_app.groupby("date")[["amount","room_amount"]].sum().reset_index()
                rev_chart["total"] = rev_chart["amount"] + rev_chart["room_amount"]

                fig1 = px.bar(rev_chart, x="date", y="total",
                              title="Daily Revenue")
                st.plotly_chart(fig1, use_container_width=True)

                workload = df_app["doctor"].value_counts().reset_index()
                workload.columns = ["Doctor","Appointments"]

                fig2 = px.pie(workload, names="Doctor",
                              values="Appointments",
                              title="Doctor Workload Distribution")
                st.plotly_chart(fig2, use_container_width=True)

        # ---------------- DOCTORS ----------------
        elif page == "Doctors":

            st.title("Add Doctor Shift")

            dname = st.text_input("Doctor Name")
            demail = st.text_input("Doctor Email")
            specialist = st.text_input("Specialist")
            nurse = st.text_input("Allocated Nurse")
            start = st.time_input("Shift Start", time(8,0))
            end = st.time_input("Shift End", time(18,0))

            if st.button("Add Doctor"):
                try:
                    c.execute("""
                    INSERT INTO doctors
                    (name,email,specialist,nurse,start_time,end_time)
                    VALUES (?,?,?,?,?,?)
                    """,(dname,demail,specialist,nurse,str(start),str(end)))

                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (demail,hash_password("Doctor@123"),"Doctor",dname))
                    conn.commit()
                    st.success("Doctor Added")
                except:
                    st.warning("Doctor already exists")

            st.dataframe(pd.read_sql("SELECT * FROM doctors",conn))

        # ---------------- ROOMS ----------------
        elif page == "Rooms":

            st.title("Room Management")

            room = st.text_input("Room Name")
            rtype = st.selectbox("Room Type",["ICU","General","Private"])
            status = st.selectbox("Status",["Available","Occupied"])

            if st.button("Add Room"):
                try:
                    c.execute("INSERT INTO rooms VALUES (NULL,?,?,?)",
                              (room,rtype,status))
                    conn.commit()
                    st.success("Room Added")
                except:
                    st.warning("Room already exists")

            rooms = pd.read_sql("SELECT * FROM rooms",conn)

            if not rooms.empty:
                selected = st.selectbox("Select Room", rooms["room_name"])
                new_status = st.selectbox("Change Status",["Available","Occupied"])

                if st.button("Update Status"):
                    c.execute("UPDATE rooms SET status=? WHERE room_name=?",
                              (new_status,selected))
                    conn.commit()
                    st.success("Updated")

            st.dataframe(rooms)
