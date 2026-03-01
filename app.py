import streamlit as st
from database import create_tables
from auth import login_user, register_user
import admin, doctor, receptionist, staff, patient

create_tables()

st.set_page_config(page_title="MediVista Admin", layout="wide")

# ---------------- CUSTOM CSS ---------------- #

def load_css():
    st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #1f3b4d, #2c5364);
        color: white;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        border-radius: 25px;
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border: none;
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #0072ff, #00c6ff);
        transform: scale(1.05);
        transition: 0.3s;
    }

    /* Input fields */
    .stTextInput>div>div>input {
        background-color: #1e293b;
        color: white;
        border-radius: 10px;
    }

    /* Select box */
    .stSelectbox>div>div {
        background-color: #1e293b;
        color: white;
        border-radius: 10px;
    }

    /* Tables */
    .stDataFrame {
        background-color: #0f172a;
        border-radius: 10px;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# ---------------- SESSION ---------------- #

if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.rerun()

# ---------------- LOGIN PAGE ---------------- #

def login_page():
    st.markdown("<h1 style='text-align:center;'>🏥 MediVista Hospital</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.markdown("### Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid Credentials")

        st.markdown("---")
        st.markdown("### Register (Patients Only)")
        name = st.text_input("Full Name")
        reg_email = st.text_input("Gmail")
        reg_pass = st.text_input("New Password", type="password")

        if st.button("Register"):
            if reg_email.endswith("@gmail.com"):
                success = register_user(name, reg_email, reg_pass, "Patient")
                if success:
                    st.success("Registered Successfully")
                else:
                    st.error("User already exists")
            else:
                st.error("Only gmail allowed")

# ---------------- ROUTING ---------------- #

if st.session_state.user is None:
    login_page()
else:
    st.sidebar.title("MediVista Admin")
    st.sidebar.write(f"Welcome {st.session_state.user[1]}")
    st.sidebar.button("Logout", on_click=logout)

    role = st.session_state.user[4]

    if role == "Admin":
        admin.admin_dashboard()

    elif role == "Doctor":
        doctor.doctor_dashboard()

    elif role == "Receptionist":
        receptionist.reception_dashboard()

    elif role == "Staff":
        staff.staff_dashboard()

    elif role == "Patient":
        patient.patient_dashboard()
