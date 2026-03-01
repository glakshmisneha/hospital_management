import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database import get_connection

def admin_dashboard():
    st.title("📊 Admin Dashboard")

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

    # Revenue Graph
    if not df_appointments.empty:
        st.subheader("Revenue by Date")
        revenue_data = df_appointments.groupby("date")["amount"].sum()
        fig, ax = plt.subplots()
        revenue_data.plot(kind="bar", ax=ax)
        st.pyplot(fig)

    st.divider()
    st.subheader("Add Doctor")

    name = st.text_input("Doctor Name")
    email = st.text_input("Doctor Email")
    specialist = st.text_input("Specialist")
    nurse = st.text_input("Allotted Nurse")
    start = st.time_input("Start Time")
    end = st.time_input("End Time")

    if st.button("Add Doctor"):
        conn.execute("INSERT INTO doctors (name,email,specialist,nurse,start_time,end_time) VALUES (?,?,?,?,?,?)",
                     (name,email,specialist,nurse,str(start),str(end)))
        conn.commit()
        st.success("Doctor Added")

    st.divider()
    st.subheader("Room Management")

    room_name = st.text_input("Room Name")
    room_type = st.selectbox("Room Type",["ICU","General","Private"])
    status = st.selectbox("Status",["Available","Occupied"])

    if st.button("Add Room"):
        conn.execute("INSERT INTO rooms (room_name,room_type,status) VALUES (?,?,?)",
                     (room_name,room_type,status))
        conn.commit()
        st.success("Room Added")

    conn.close()
