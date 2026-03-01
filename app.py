import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
import random
import string
from datetime import datetime, timedelta, time

# ======================================================
# DATABASE CONNECTION
# ======================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect("medivista.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

conn = get_connection()
c = conn.cursor()

# ======================================================
# INITIALIZE DATABASE
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
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        doctor TEXT,
        slot TEXT,
        date TEXT,
        amount REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS queries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient TEXT,
        target TEXT,
        doctor TEXT,
        message TEXT,
        status TEXT
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
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?,?,?)",
                          (email,hash_password(password),'Patient',email))
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
# MAIN APPLICATION
# ======================================================

else:

    role = st.session_state.user[2]
    username = st.session_state.user[3]

    st.sidebar.title("MediVista")
    st.sidebar.write(f"Logged in as {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# ======================================================
# ADMIN PANEL
# ======================================================

    if role == "Admin":

        page = st.sidebar.radio("Navigation",
            ["Dashboard","Add Specialist","Add Doctor",
             "Add Nurse","Register Receptionist",
             "Queries","Reports"])

        if page == "Dashboard":

            st.title("📊 Hospital Dashboard")

            df = pd.read_sql("SELECT * FROM appointments", conn)

            total_revenue = df["amount"].sum() if not df.empty else 0
            total_visits = len(df)

            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Total Revenue", f"₹ {total_revenue}")
            col2.metric("Total Doctors", len(pd.read_sql("SELECT * FROM doctors",conn)))
            col3.metric("Total Patients", len(pd.read_sql("SELECT * FROM patients",conn)))
            col4.metric("Total Visits", total_visits)

            if not df.empty:

                revenue_chart = df.groupby("date")["amount"].sum().reset_index()
                visit_chart = df.groupby("date")["patient"].count().reset_index()

                fig1 = px.bar(revenue_chart, x="date", y="amount",
                              title="Daily Revenue")
                st.plotly_chart(fig1, use_container_width=True)

                fig2 = px.line(visit_chart, x="date", y="patient",
                               title="Daily Patient Visits")
                st.plotly_chart(fig2, use_container_width=True)

        elif page == "Add Specialist":

            st.title("Add Specialist")
            spec = st.text_input("Specialist Name")

            if st.button("Add Specialist"):
                try:
                    c.execute("INSERT INTO specialists (name) VALUES (?)",(spec,))
                    conn.commit()
                    st.success("Specialist Added")
                except:
                    st.warning("Already exists")

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
                        c.execute("INSERT INTO doctors VALUES (NULL,?,?,?,?,?)",
                                  (name,email,specialist,str(start),str(end)))
                        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                                  (email,hash_password(password),'Doctor',name))
                        conn.commit()
                        st.success(f"Doctor Added. Password: {password}")
                    except:
                        st.error("Doctor already exists")

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
                        c.execute("INSERT INTO nurses VALUES (NULL,?,?,?,?,?)",
                                  (name,email,str(start),str(end),allocated))
                        c.execute("INSERT INTO users VALUES (?,?,?,?)",
                                  (email,hash_password(password),'Nurse',name))
                        conn.commit()
                        st.success(f"Nurse Added. Password: {password}")
                    except:
                        st.error("Nurse already exists")

                st.subheader("Nurse List")
                st.dataframe(pd.read_sql("SELECT * FROM nurses",conn))

        elif page == "Register Receptionist":

            st.title("Register Receptionist")
            name = st.text_input("Name")
            email = st.text_input("Email")

            if st.button("Register"):
                password = generate_password()
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?)",
                              (email,hash_password(password),'Receptionist',name))
                    conn.commit()
                    st.success(f"Receptionist Added. Password: {password}")
                except:
                    st.error("User already exists")

        elif page == "Queries":

            st.title("Patient Queries")

            qdf = pd.read_sql("SELECT * FROM queries",conn)

            if not qdf.empty:
                st.dataframe(qdf)

                query_id = st.number_input("Enter Query ID to Resolve", min_value=1, step=1)

                if st.button("Mark Resolved"):
                    c.execute("UPDATE queries SET status='Resolved' WHERE id=?",(query_id,))
                    conn.commit()
                    st.success("Marked as Resolved")
            else:
                st.info("No Queries")

        elif page == "Reports":

            st.title("Download Appointment Report")

            df = pd.read_sql("SELECT * FROM appointments",conn)

            if not df.empty:
                st.download_button("Download CSV",
                                   df.to_csv(index=False),
                                   "appointments.csv")

# ======================================================
# RECEPTIONIST
# ======================================================

    elif role == "Receptionist":

        page = st.sidebar.radio("Receptionist Options",
                                ["Register Patient","Book Appointment"])

        if page == "Register Patient":

            st.title("Register Patient")
            pname = st.text_input("Name")
            pemail = st.text_input("Email")
            blood = st.selectbox("Blood Group",
                                 ["A+","A-","B+","B-","O+","O-","AB+","AB-"])

            if st.button("Register"):
                c.execute("INSERT INTO patients VALUES (NULL,?,?,?)",
                          (pname,pemail,blood))
                conn.commit()
                st.success("Patient Registered")

        elif page == "Book Appointment":

            st.title("Book Appointment")

            doctors = pd.read_sql("SELECT name FROM doctors",conn)
            patients = pd.read_sql("SELECT name FROM patients",conn)

            if not doctors.empty and not patients.empty:

                doctor = st.selectbox("Doctor", doctors["name"])
                patient = st.selectbox("Patient", patients["name"])
                date = st.date_input("Date")
                amount = st.number_input("Amount")
                slots = generate_slots(time(8,0),time(18,0))
                slot = st.selectbox("Slot", slots)

                if st.button("Book Appointment"):
                    c.execute("""
                    INSERT INTO appointments
                    (patient,doctor,slot,date,amount)
                    VALUES (?,?,?,?,?)
                    """,(patient,doctor,slot,str(date),amount))
                    conn.commit()
                    st.success("Appointment Booked")

# ======================================================
# DOCTOR
# ======================================================

    elif role == "Doctor":

        st.title("Doctor Panel")

        st.subheader("My Appointments")
        df = pd.read_sql(f"SELECT * FROM appointments WHERE doctor='{username}'",conn)
        st.dataframe(df)

        st.subheader("Queries")
        qdf = pd.read_sql(f"""
        SELECT * FROM queries
        WHERE doctor='{username}' OR target='Doctor'
        """,conn)
        st.dataframe(qdf)

# ======================================================
# NURSE
# ======================================================

    elif role == "Nurse":

        st.title("Nurse Panel")
        df = pd.read_sql(f"SELECT * FROM nurses WHERE name='{username}'",conn)
        st.dataframe(df)

# ======================================================
# PATIENT
# ======================================================

    elif role == "Patient":

        page = st.sidebar.radio("Patient Options",
                                ["View Appointments","Send Query"])

        if page == "View Appointments":
            df = pd.read_sql(f"SELECT * FROM appointments WHERE patient='{username}'",conn)
            st.dataframe(df)

        elif page == "Send Query":

            st.title("Send Query")

            target = st.selectbox("Query To", ["Doctor","Management"])
            message = st.text_area("Enter your query")
            doctor_name = None

            if target == "Doctor":
                doctors = pd.read_sql("SELECT name FROM doctors",conn)
                doctor_name = st.selectbox("Select Doctor", doctors["name"])

            if st.button("Submit Query"):
                c.execute("""
                INSERT INTO queries
                (patient,target,doctor,message,status)
                VALUES (?,?,?,?,?)
                """,(username,target,doctor_name,message,"Pending"))
                conn.commit()
                st.success("Query Submitted")

            st.subheader("My Queries")
            my_queries = pd.read_sql(f"SELECT * FROM queries WHERE patient='{username}'",conn)
            st.dataframe(my_queries)
