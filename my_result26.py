import streamlit as st
import sqlite3
import json
import datetime
import pandas as pd

# ---------------- CONFIG ----------------
ADMIN_USER = "Abhishek"
ADMIN_PASS = "abhi8813"

st.set_page_config(page_title="Result System", layout="wide")

# ---------------- DB ----------------
conn = sqlite3.connect("result.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    title TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    roll INTEGER PRIMARY KEY,
    school TEXT,
    name TEXT,
    father TEXT,
    dob TEXT,
    subjects TEXT
)
""")
conn.commit()

# default title
cursor.execute("SELECT title FROM settings WHERE id=1")
row = cursor.fetchone()
if not row:
    cursor.execute("INSERT INTO settings VALUES (1, ?)", ("MP BOARD RESULT SYSTEM 2026",))
    conn.commit()

# ---------------- FUNCTIONS ----------------
def calculate_result(subjects):
    marks = list(subjects.values())
    total = sum(marks)
    percent = total / len(marks)

    if any(m < 33 for m in marks):
        result = "FAIL"
        division = "-"
    else:
        result = "PASS"
        if percent >= 60:
            division = "FIRST DIVISION"
        elif percent >= 45:
            division = "SECOND DIVISION"
        else:
            division = "THIRD DIVISION"

    if percent >= 75:
        grade = "A+"
    elif percent >= 60:
        grade = "A"
    elif percent >= 45:
        grade = "B"
    elif percent >= 33:
        grade = "C"
    else:
        grade = "D"

    return total, percent, result, division, grade

# ---------------- SESSION ----------------
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ---------------- TITLE ----------------
cursor.execute("SELECT title FROM settings WHERE id=1")
APP_TITLE = cursor.fetchone()[0]

st.markdown(f"<h2 style='text-align:center'>{APP_TITLE}</h2>", unsafe_allow_html=True)

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
                st.success("Login Successful")
            else:
                st.error("Invalid Credentials")
    else:
        st.subheader("Admin Settings")

        # Change heading
        new_title = st.text_input("Change Heading Title", APP_TITLE)
        if st.button("Update Title"):
            cursor.execute("UPDATE settings SET title=? WHERE id=1", (new_title,))
            conn.commit()
            st.success("Title Updated (Refresh page)")

        st.divider()
        st.subheader("Enter Student Result")

        school = st.text_input("School Name")
        roll = st.number_input("Roll Number", step=1)
        name = st.text_input("Student Name")
        father = st.text_input("Father Name")
        dob = st.date_input("Date of Birth", min_value=datetime.date(2000, 1, 1))

        st.markdown("### Enter 5 Subjects")

        subjects = {}
        for i in range(1, 6):
            col1, col2 = st.columns(2)
            with col1:
                sub = st.text_input(f"Subject {i} Name")
            with col2:
                mark = st.number_input(f"Marks {i}", 0, 100, key=f"m{i}")
            if sub:
                subjects[sub] = mark

        if st.button("Save Result"):
            if len(subjects) != 5:
                st.error("Exactly 5 subjects required")
            else:
                cursor.execute(
                    "INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?)",
                    (roll, school, name, father, str(dob), json.dumps(subjects))
                )
                conn.commit()
                st.success("Result Saved Successfully")

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
            st.error("Result Not Found")
        else:
            roll, school, name, father, dob, subjects_json = data
            subjects = json.loads(subjects_json)

            total, percent, result, division, grade = calculate_result(subjects)

            st.write(f"**School:** {school}")
            st.write(f"**Name:** {name}")
            st.write(f"**Father Name:** {father}")
            st.write(f"**DOB:** {dob}")

            df = pd.DataFrame({
                "Subject": subjects.keys(),
                "Marks": subjects.values(),
                "Status": ["PASS" if m >= 33 else "FAIL" for m in subjects.values()]
            })
            st.dataframe(df, use_container_width=True)

            st.success(f"Total Marks: {total}")
            st.info(f"Percentage: {percent:.2f}%")
            st.info(f"Grade: {grade}")

            if result == "PASS":
                st.success(f"RESULT: PASS | {division}")
            else:
                st.error("RESULT: FAIL")
