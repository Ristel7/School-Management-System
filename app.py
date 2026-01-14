from flask import Flask, render_template, request, redirect, session
from flask_bcrypt import Bcrypt
import mysql.connector

app = Flask(__name__)
app.secret_key = "super_secret_key_123"
bcrypt = Bcrypt(app)


@app.route("/")
def home():
    return render_template("index.html")

# ---------------- MYSQL CONNECTION ----------------


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="****",
        password="******",        # ✅ YOUR MYSQL PASSWORD
        database="erp"
    )

# ---------------- HASH EXISTING PASSWORDS (RUNS ONCE SAFELY) ----------------


def hash_existing_passwords():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    for user in users:
        if not user["password"].startswith("$2b$"):
            hashed = bcrypt.generate_password_hash(
                user["password"]).decode("utf-8")
            cursor.execute(
                "UPDATE users SET password=%s WHERE id=%s",
                (hashed, user["id"])
            )

    db.commit()
    cursor.close()
    db.close()


hash_existing_passwords()

# ---------------- LOGIN ROUTE ----------------


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin/dashboard")

            elif user["role"] == "teacher":
                return redirect("/teacher/dashboard")

            elif user["role"] == "student":
                return redirect("/student/dashboard")

        else:
            return "Invalid Username or Password"

    return render_template("login.html")

# ---------------- ADMIN DASHBOARD ----------------


@app.route("/admin/dashboard")
def admin_dashboard():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch students
    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()

    # Fetch teachers
    cursor.execute("SELECT * FROM teachers ORDER BY id DESC")
    teachers = cursor.fetchall()

    # Total counts
    total_students = len(students)
    total_teachers = len(teachers)

    cursor.close()
    db.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        teachers=teachers,
        total_students=total_students,
        total_teachers=total_teachers
    )

# ---------------- ADD STUDENT ----------------


@app.route("/admin/students/add", methods=["GET", "POST"])
def add_student():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        class_name = request.form["class_name"]
        roll_no = request.form["roll_no"]
        phone = request.form["phone"]

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO students (name, class_name, roll_no, phone)
            VALUES (%s, %s, %s, %s)
        """, (name, class_name, roll_no, phone))

        db.commit()
        cursor.close()
        db.close()

        return redirect("/admin/dashboard")

    return render_template("add_student.html")


# ---------------- ADD TEACHER ----------------


@app.route("/admin/teachers/add", methods=["GET", "POST"])
def add_teacher():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        subject = request.form["subject"]
        phone = request.form["phone"]

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO teachers (name, subject, phone)
            VALUES (%s, %s, %s)
        """, (name, subject, phone))

        db.commit()
        cursor.close()
        db.close()

        return redirect("/admin/dashboard")

    return render_template("add_teacher.html")


# ---------------- VIEW TEACHERS ----------------
@app.route("/admin/teachers")
def view_teachers():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM teachers ORDER BY id DESC")
    teachers = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("view_teachers.html", teachers=teachers)


# ---------------- DELETE TEACHER ----------------
@app.route("/admin/teachers/delete/<int:id>")
def delete_teacher(id):
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM teachers WHERE id=%s", (id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect("/admin/teachers")

# ---------------- VIEW STUDENTS ----------------


@app.route("/admin/students")
def view_students():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("view_students.html", students=students)


# ---------------- TEACHER DASHBOARD ----------------


@app.route("/teacher/dashboard")
def teacher_dashboard():
    if "role" not in session or session["role"] != "teacher":
        return redirect("/login")

    return render_template("teacher_dashboard.html")

# ---------------- STUDENT DASHBOARD ----------------


@app.route("/student/dashboard")
def student_dashboard():
    if "role" not in session or session["role"] != "student":
        return redirect("/login")

    return render_template("student_dashboard.html")

# ---------------- LOGOUT ----------------


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
