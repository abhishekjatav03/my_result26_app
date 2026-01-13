import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# ---------------- CONFIG ----------------
ADMIN_USER = "Abhishek"
ADMIN_PASS = "abhi8813"

st.set_page_config("MP Board Result System", layout="wide")

# ---------------- DB ----------------
conn = sqlite3.connect("result.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    roll INTEGER PRIMARY KEY,
    name TEXT,
    father TEXT,
    dob TEXT,
    hindi INTEGER,
    english INTEGER,
    maths INTEGER,
    science INTEGER
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def calculate_result(marks):
    if any(m < 33 for m in marks):
        return "FAIL", "—"
    percent = sum(marks) / 4
    if percent >= 60:
        return "PASS", "FIRST DIVISION"
    elif percent >= 45:
        return "PASS", "SECOND DIVISION"
    else:
        return "PASS", "THIRD DIVISION"

def generate_pdf(data):
    roll, name, father, dob, h, e, m, s = data
    marks = [h, e, m, s]
    result, division, percent, grade = calculate_result(marks)

    total = sum(marks)
    c.drawString(50, y, f"Percentage: {percent:.2f}%")
    y -= 25
    c.drawString(50, y, f"Grade: {grade}")
    y -= 25
    c.drawString(50, y, f"Result: {result}")
    c.drawString(300, y, f"Division: {division}")


    file_name = f"Marksheet_{roll}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    c.setFont("Helvetica", 12)

    c.drawCentredString(300, 800, "MP BOARD RESULT 2026")
    c.line(50, 790, 550, 790)

    y = 750
    c.drawString(50, y, f"Roll No: {roll}")
    c.drawString(300, y, f"Name: {name}")
    y -= 30
    c.drawString(50, y, f"Father Name: {father}")
    c.drawString(300, y, f"DOB: {dob}")
    y -= 40

    subjects = ["Hindi", "English", "Maths", "Science"]
    for sub, mark in zip(subjects, marks):
        c.drawString(80, y, sub)
        c.drawString(300, y, str(mark))
        y -= 25

    y -= 20
    c.drawString(50, y, f"Total Marks: {total}/400")
    y -= 25
    c.drawString(50, y, f"Result: {result}")
    c.drawString(300, y, f"Division: {division}")

    c.showPage()
    c.save()
    return file_name

# ---------------- SESSION ----------------
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ---------------- UI ----------------
st.markdown("<h2 style='text-align:center'>MP BOARD RESULT SYSTEM 2026</h2>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🔐 Admin Panel", "🎓 Student Result"])

# ================= ADMIN =================
with tab1:
    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if u == ADMIN_USER and p == ADMIN_PASS:
                st.session_state.admin_logged_in = True
                st.success("✅ Login Successful")
            else:
                st.error("❌ Invalid Credentials")
    else:
        st.subheader("Enter Student Result")

        roll = st.number_input("Roll Number", step=1)
        name = st.text_input("Student Name")
        father = st.text_input("Father Name")
        import datetime

        dob = st.date_input(
           "Date of Birth",
        min_value=datetime.date(2000, 1, 1)
               )


        col1, col2 = st.columns(2)
        with col1:
            hindi = st.number_input("Hindi", 0, 100)
            english = st.number_input("English", 0, 100)
        with col2:
            maths = st.number_input("Maths", 0, 100)
            science = st.number_input("Science", 0, 100)

        if st.button("Save Result"):
            cursor.execute("""
            INSERT OR REPLACE INTO students
            VALUES (?,?,?,?,?,?,?,?)
            """, (roll, name, father, dob, hindi, english, maths, science))
            conn.commit()
            st.success("✅ Result Saved")

        if st.button("Logout"):
            st.session_state.admin_logged_in = False

# ================= STUDENT =================
with tab2:
    st.subheader("Check Result")
    r = st.number_input("Enter Roll Number", step=1)

    if st.button("Show Result"):
        cursor.execute("SELECT * FROM students WHERE roll=?", (r,))
        data = cursor.fetchone()

        if not data:
            st.error("❌ Result Not Found")
        else:
            roll, name, father, dob, h, e, m, s = data
            marks = [h, e, m, s]
            result, division = calculate_result(marks)
            total = sum(marks)

            st.write(f"**Name:** {name}")
            st.write(f"**Father Name:** {father}")
            st.write(f"**DOB:** {dob}")

            df = pd.DataFrame({
                "Subject": ["Hindi", "English", "Maths", "Science"],
                "Marks": marks,
                "Status": ["FAIL" if x < 33 else "PASS" for x in marks]
            })

            st.dataframe(df)
            st.success(f"Total: {total}/400")

            if result == "PASS":
                st.success(f"RESULT: PASS | {division}")
            else:
                st.error("RESULT: FAIL")

            if st.button("📄 Download PDF Marksheet"):
                pdf = generate_pdf(data)
                with open(pdf, "rb") as f:
                    st.download_button("Download PDF", f, file_name=pdf)
