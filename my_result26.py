import streamlit as st
import mysql.connector

# ------------------ SESSION INIT ------------------
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

# ------------------ ADMIN CREDENTIALS ------------------
ADMIN_USER = "Abhishek"
ADMIN_PASS = "12345"  # Change your password here

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="MP Board Result System",
    layout="centered",
    page_icon="🎓"
)

st.title("🎓 MP Board Result System")
st.markdown("---")

# ------------------ DATABASE CONNECTION ------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="abhi123",      # Set your MySQL password
        database="result_system"
    )

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["🔐 Admin Login", "📄 Student Result"])

# ================= ADMIN LOGIN =================
with tab1:
    st.header("🔐 Admin Login")

    if not st.session_state["admin_logged_in"]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == ADMIN_USER and password == ADMIN_PASS:
                st.session_state["admin_logged_in"] = True
                st.success("✅ Login Successful")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid Username or Password")

    else:
        st.success("🟢 Admin Logged In")

        if st.button("Logout"):
            st.session_state["admin_logged_in"] = False
            st.experimental_rerun()

        st.markdown("---")
        st.header("🛠️ Admin Panel – Add / Update Result")

        # --------- STUDENT DETAILS INPUT ----------
        roll_no = st.text_input("Roll Number")
        student_name = st.text_input("Student Name")
        father_name = st.text_input("Father Name")
        school_name = st.text_input("School Name")
        dob = st.date_input("Date of Birth")

        st.subheader("📊 Subject Marks")
        hindi = st.number_input("Hindi", 0, 100)
        english = st.number_input("English", 0, 100)
        maths = st.number_input("Maths", 0, 100)
        science = st.number_input("Science", 0, 100)
        social = st.number_input("Social Science", 0, 100)

        if st.button("💾 Save Result"):
            if not roll_no.isdigit():
                st.error("Roll Number must be numeric")
                st.stop()
            
            roll_no = int(roll_no)
            subjects = ["Hindi", "English", "Maths", "Science", "Social Science"]
            marks_list = [hindi, english, maths, science, social]

            total = sum(marks_list)
            percentage = total / 5

            failed = [subjects[i] for i, m in enumerate(marks_list) if m < 33]

            if failed:
                result_status = "FAIL"
                division = "No Division"
            else:
                result_status = "PASS"
                if percentage >= 60:
                    division = "First Division"
                elif percentage >= 45:
                    division = "Second Division"
                else:
                    division = "Third Division"

            if percentage >= 90:
                grade = "A+"
            elif percentage >= 75:
                grade = "A"
            elif percentage >= 60:
                grade = "B"
            elif percentage >= 45:
                grade = "C"
            elif percentage >= 33:
                grade = "D"
            else:
                grade = "F"

            conn = get_connection()
            cursor = conn.cursor()

            # INSERT / UPDATE STUDENT DETAILS
            cursor.execute(
                "REPLACE INTO students VALUES (%s,%s,%s,%s,%s)",
                (roll_no, student_name, father_name, school_name, dob)
            )

            # INSERT / UPDATE MARKS
            cursor.execute("DELETE FROM marks WHERE roll_no=%s", (roll_no,))
            for sub, mark in zip(subjects, marks_list):
                cursor.execute(
                    "INSERT INTO marks VALUES (%s,%s,%s)",
                    (roll_no, sub, mark)
                )

            # INSERT / UPDATE RESULT SUMMARY
            cursor.execute(
                "REPLACE INTO result_summary VALUES (%s,%s,%s,%s,%s,%s)",
                (roll_no, total, percentage, result_status, division, grade)
            )

            conn.commit()
            cursor.close()
            conn.close()

            st.success("✅ Result Saved Successfully")

# ================= STUDENT RESULT =================
with tab2:
    st.header("📄 Student Result (Roll No Wise)")

    roll_search = st.text_input("Enter Roll Number")

    if st.button("🔍 View Result"):
        if not roll_search.isdigit():
            st.error("Roll Number must be numeric")
            st.stop()

        roll_search = int(roll_search)

        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT s.roll_no, s.student_name, s.father_name, s.school_name, s.dob,
               m.subject, m.marks,
               r.total, r.percentage, r.result_status, r.division, r.grade
        FROM students s
        JOIN marks m ON s.roll_no = m.roll_no
        JOIN result_summary r ON s.roll_no = r.roll_no
        WHERE s.roll_no = %s
        """

        cursor.execute(query, (roll_search,))
        data = cursor.fetchall()

        if not data:
            st.error("❌ Result Not Found")
        else:
            first = data[0]

            st.subheader("🧾 Student Details")
            st.write(f"Roll No : {first[0]}")
            st.write(f"Name : {first[1]}")
            st.write(f"Father Name : {first[2]}")
            st.write(f"School : {first[3]}")
            st.write(f"DOB : {first[4]}")

            st.markdown("---")

            table = []
            failed = []

            for row in data:
                status = "FAIL" if row[6] < 33 else "PASS"
                if status == "FAIL":
                    failed.append(row[5])
                table.append({
                    "Subject": row[5],
                    "Marks": row[6],
                    "Status": status
                })

            st.table(table)

            st.markdown("---")
            st.subheader("🏆 Result Summary")
            st.write(f"Total : {first[7]}")
            st.write(f"Percentage : {first[8]}%")
            st.write(f"Result : {first[9]}")
            st.write(f"Division : {first[10]}")
            st.write(f"Grade : {first[11]}")

            if failed:
                st.error("❌ Failed In: " + ", ".join(failed))
            else:
                st.success("✅ Passed All Subjects")

        cursor.close()
        conn.close()
