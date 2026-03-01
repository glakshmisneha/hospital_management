import streamlit as st
import pandas as pd
from database import get_connection

def doctor_dashboard():
    st.title("👨‍⚕ Doctor Portal")

    conn = get_connection()

    df = pd.read_sql("SELECT * FROM appointments",conn)
    st.subheader("My Appointments")
    st.dataframe(df)

    queries = pd.read_sql("SELECT * FROM queries WHERE target='Doctor'",conn)
    st.subheader("Patient Queries")
    st.dataframe(queries)

    conn.close()
