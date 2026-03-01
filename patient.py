import streamlit as st
from database import get_connection

def patient_dashboard():
    st.title("🙋 Patient Portal")

    conn = get_connection()

    target = st.selectbox("Send Query To",["Admin","Doctor"])
    message = st.text_area("Enter Query")

    if st.button("Submit"):
        conn.execute("INSERT INTO queries (patient_name,target,message) VALUES (?,?,?)",
                     ("Patient",target,message))
        conn.commit()
        st.success("Query Sent")

    conn.close()
