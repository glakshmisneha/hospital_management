import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
import random
import string
from datetime import datetime, timedelta, time

# ================= DATABASE =================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

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
    CREATE TABLE IF NOT EXISTS specialists(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS doctors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        specialist TEXT,
        shift_start TEXT,
        shift_end TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS nurses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
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
        amount REAL
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

# ================= UTILITIES =================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def generate_slots(start, end):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while current < end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=20)
    return slots

# ================= UI =================

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

if "user" not in st.session_state:
    st.session_state.user = None

# ================= LOGIN =================

if st.session_state.user is None:

    st.title("🏥 MediVista Hospital Portal")

    mode = st.radio("Login / Register", ["Login","Register"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Register":
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?,?)",
                          (email,hash_password(password),'Patient',email))
                conn.commit()
                st.success("Registered Successfully")
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

# ================= MAIN =================

else:

    role = st.session_state.user[2]
    username = st.session_state.user[3]

    st.sidebar.title("MediVista")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ================= ADMIN =================

    if role == "Admin":

        page = st.sidebar.radio("Navigation",
            ["Dashboard","Add Specialist","Add Doctor",
             "Add Nurse","Register Staff",
             "Reports"])

        if page == "Dashboard":

            st.title("📊 Hospital Dashboard")

            df = pd.read_sql("SELECT * FROM appointments", conn)
            revenue = df["amount"].sum() if not df.empty else 0

            col1,col2,col3 = st.columns(3)
            col1.metric("Total Revenue", f"₹ {revenue}")
            col2.metric("Total Doctors", len(pd.read_sql("SELECT * FROM doctors",conn)))
            col3.metric("Total Patients", len(pd.read_sql("SELECT * FROM patients",conn)))

            if not df.empty:
                fig = px.bar(df.groupby("date")["amount"].sum().reset_index(),
                             x="date", y="amount",
                             title="Daily Revenue")
                st.plotly_chart(fig, use_container_width=True)

        elif page == "Add Specialist":

            st.title("Add Specialist")
            spec = st.text_input("Specialist Name")

            if st.button("Add"):
                try:
                    c.execute("INSERT INTO specialists (name) VALUES (?)",(spec,))
                    conn.commit()
                    st.success("Added")
                except:
                    st.warning("Exists")

            st.dataframe(pd.read_sql("SELECT * FROM specialists",conn))

        elif page == "Add Doctor":

            st.title("Add Doctor")

            specs = pd.read_sql("SELECT name FROM specialists",conn)

            if specs.empty:
                st.warning("Add specialist first")
            else:
                name = st.text_input("Doctor Name")
                email = st.text_input("Doctor Email")
                specialist = st.selectbox("Specialist", specs["name"])
                start = st.time_input("Shift Start",time(8,0))
                end = st.time_input("Shift End",time(18,0))

                if st.button("Add Doctor"):
                    password = generate_password()
                    try:
                        c.execute("INSERT INTO doctors (name,email,specialist,shift_start,shift_end) VALUES (?,?,?,?,?)",
                                  (name,email,specialist,str(start),str(end)))
                        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                                  (email,hash_password(password),'Doctor',name))
                        conn.commit()
                        st.success(f"Doctor Added. Login Password: {password}")
                    except:
                        st.error("Doctor exists")

                st.subheader("Doctors List")
                st.dataframe(pd.read_sql("SELECT * FROM doctors",conn))

        elif page == "Add Nurse":

            st.title("Add Nurse")

            doctors = pd.read_sql("SELECT name FROM doctors",conn)

            if doctors.empty:
                st.warning("Add doctor first")
            else:
                name = st.text_input("Nurse Name")
                email = st.text_input("Nurse Email")
                allocated = st.selectbox("Allocated Doctor", doctors["name"])
                start = st.time_input("Shift Start",time(8,0))
                end = st.time_input("Shift End",time(18,0))

                if st.button("Add Nurse"):
                    password = generate_password()
                    try:
                        c.execute("INSERT INTO nurses (name,email,shift_start,shift_end,allocated_doctor) VALUES (?,?,?,?,?)",
                                  (name,email,str(start),str(end),allocated))
                        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                                  (email,hash_password(password),'Nurse',name))
                        conn.commit()
                        st.success(f"Nurse Added. Login Password: {password}")
                    except:
                        st.error("Exists")

                st.subheader("Nurse List")
                st.dataframe(pd.read_sql("SELECT * FROM nurses",conn))

        elif page == "Register Staff":

            st.title("Register Receptionist")
            name = st.text_input("Name")
            email = st.text_input("Email")

            if st.button("Register"):
                password = generate_password()
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (email,hash_password(password),'Receptionist',name))
                    conn.commit()
                    st.success(f"Receptionist Added. Login Password: {password}")
                except:
                    st.error("Exists")

        elif page == "Reports":

            st.title("Download Reports")

            df = pd.read_sql("SELECT * FROM appointments",conn)

            if not df.empty:
                st.download_button("Download Appointments CSV",
                                   df.to_csv(index=False),
                                   "appointments.csv")

    # ================= DOCTOR =================

    elif role == "Doctor":

        st.title("Doctor Panel")

        df = pd.read_sql(f"SELECT * FROM appointments WHERE doctor='{username}'",conn)
        st.dataframe(df)

    # ================= NURSE =================

    elif role == "Nurse":

        st.title("Nurse Panel")

        df = pd.read_sql(f"SELECT * FROM nurses WHERE name='{username}'",conn)
        st.dataframe(df)

    # ================= RECEPTIONIST =================

    elif role == "Receptionist":

        st.title("Receptionist Panel")

        option = st.radio("Options",["Register Patient","Book Appointment"])

        if option == "Register Patient":
            pname = st.text_input("Name")
            pemail = st.text_input("Email")
            blood = st.selectbox("Blood Group",
                                 ["A+","A-","B+","B-","O+","O-","AB+","AB-"])
            if st.button("Register"):
                c.execute("INSERT INTO patients VALUES (NULL,?,?,?)",
                          (pname,pemail,blood))
                conn.commit()
                st.success("Patient Registered")

        elif option == "Book Appointment":

            doctors = pd.read_sql("SELECT name FROM doctors",conn)
            patients = pd.read_sql("SELECT name FROM patients",conn)

            if not doctors.empty and not patients.empty:
                doctor = st.selectbox("Doctor", doctors["name"])
                patient = st.selectbox("Patient", patients["name"])
                date = st.date_input("Date")
                amount = st.number_input("Amount")
                slots = generate_slots(time(8,0),time(18,0))
                slot = st.selectbox("Slot", slots)

                if st.button("Book"):
                    c.execute("""
                    INSERT INTO appointments
                    (patient,doctor,slot,date,amount)
                    VALUES (?,?,?,?,?)
                    """,(patient,doctor,slot,str(date),amount))
                    conn.commit()
                    st.success("Booked")
