import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database import get_connection

def admin_dashboard():
    st.title("Appointment Booking")

    conn = get_connection()

    df_appointments = pd.read_sql("SELECT * FROM appointments", conn)
    df_doctors = pd.read_sql("SELECT * FROM doctors", conn)
    df_patients = pd.read_sql("SELECT * FROM patients", conn)

    total_revenue = df_appointments["amount"].sum() if not df_appointments.empty else 0

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total Revenue", f"₹{total_revenue}")
    col2.metric("Total Patients", len(df_patients))
    col3.metric("Total Doctors", len(df_doctors))
    col4.metric("Total Visits", len(df_appointments))

    st.markdown("---")

    # Booking UI Like Screenshot
    st.subheader("Book Appointment")

    if not df_patients.empty and not df_doctors.empty:
        patient = st.selectbox("Select Patient", df_patients["name"])
        doctor = st.selectbox("Select Doctor", df_doctors["name"])
        date = st.date_input("Select Date")
        amount = st.number_input("Amount")

        if st.button("Book Appointment"):
            conn.execute("INSERT INTO appointments (patient_name,doctor_name,slot,date,amount) VALUES (?,?,?,?,?)",
                         (patient,doctor,"Manual Slot",str(date),amount))
            conn.commit()
            st.success("Appointment Booked Successfully")

    st.markdown("---")
    st.subheader("Appointments Table")
    st.dataframe(df_appointments)

    # Revenue Chart
    if not df_appointments.empty:
        st.subheader("Revenue Analytics")
        revenue_data = df_appointments.groupby("date")["amount"].sum()
        fig, ax = plt.subplots()
        revenue_data.plot(kind="bar", ax=ax)
        st.pyplot(fig)

    conn.close()
