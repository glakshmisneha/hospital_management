import streamlit as st
import pandas as pd
from database import get_connection

def staff_dashboard():
    st.title("🏥 Hospital Staff Panel")

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM doctors",conn)
    st.dataframe(df[["name","nurse","start_time","end_time"]])
    conn.close()
