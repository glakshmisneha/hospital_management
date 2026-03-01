import streamlit as st
import pandas as pd
from database import get_connection

def reception_dashboard():
    st.title("🧾 Receptionist Panel")

    conn = get_connection()

    st.subheader("Register Patient")

    name = st.text_input("Patient Name")
    email = st.text_input("Patient Email")
    blood = st.selectbox("Blood Group",
                         ["A+","A-","B+","B-","O+","O-","AB+","AB-"])

    if st.button("Register"):
        conn.execute("INSERT INTO patients (name,email,blood_group) VALUES (?,?,?)",
                     (name,email,blood))
        conn.commit()
        st.success("Patient Registered")

    st.divider()
    st.subheader("Book Appointment")

    doctors = pd.read_sql("SELECT * FROM doctors",conn)
    if not doctors.empty:
        doctor = st.selectbox("Select Doctor",doctors["name"])
        date = st.date_input("Select Date")
        slot = st.time_input("Select Slot")
        amount = st.number_input("Amount Paid")

        if st.button("Book"):
            conn.execute("INSERT INTO appointments (patient_name,doctor_name,slot,date,amount) VALUES (?,?,?,?,?)",
                         (name,doctor,str(slot),str(date),amount))
            conn.commit()
            st.success("Appointment Booked")

    conn.close()
