import streamlit as st
from database import create_tables
from auth import register_user, login_user
import admin, doctor, receptionist, staff, patient

create_tables()

st.set_page_config(page_title="Hospital Analytics Dashboard", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- LOGIN / REGISTER ---------------- #

def login_page():
    st.title("🏥 Hospital Management System")

    menu = st.radio("Select Option", ["Login", "Register"])

    if menu == "Register":
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Patient"])

        if st.button("Register"):
            if email.endswith("@gmail.com"):
                register_user(name,email,password,role)
            else:
                st.error("Patients must use gmail")

    if menu == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(email,password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid Credentials")

# ---------------- ROUTING ---------------- #

if st.session_state.user is None:
    login_page()
else:
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
