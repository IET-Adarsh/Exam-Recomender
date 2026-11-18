import os
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_config import get_db_connection

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-this-key")

def fetch_one(query, params=()):
    db = get_db_connection()
    if db is None:
        return None
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        db.close()


def fetch_all(query, params=()):
    db = get_db_connection()
    if db is None:
        return None
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        db.close()


def execute_query(query, params=()):
    db = get_db_connection()
    if db is None:
        return None
    cursor = None
    try:
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()
        return cursor.lastrowid
    except Exception:
        db.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        db.close()


def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def check_eligibility(student, criteria):
    if not criteria:
        return {"eligible": False, "status": "Criteria not available", "match_score": 0}

    checks = []

    required = (criteria.get("qualification") or "").strip().lower()
    actual = (student.get("qualification") or "").strip().lower()
    if required and required not in ("any", "all"):
        checks.append(required == actual)

    required = (criteria.get("stream") or "").strip().lower()
    actual = (student.get("stream") or "").strip().lower()
    if required and required not in ("any", "all"):
        checks.append(required == actual)

    age = calculate_age(student.get("date_of_birth"))
    min_age, max_age = criteria.get("min_age"), criteria.get("max_age")
    if min_age is not None or max_age is not None:
        checks.append(
            age is not None
            and (min_age is None or age >= min_age)
            and (max_age is None or age <= max_age)
        )

    min_percentage = criteria.get("min_percentage")
    if min_percentage is not None:
        percentage = student.get("percentage")
        checks.append(
            percentage is not None and float(percentage) >= float(min_percentage)
        )

    if not checks:
        return {"eligible": False, "status": "Criteria incomplete", "match_score": 0}

    score = round(sum(checks) / len(checks) * 100)
    eligible = all(checks)
    return {
        "eligible": eligible,
        "status": "Eligible" if eligible else "Not eligible",
        "match_score": score,
    }


def get_exam(exam_id):
    exam = fetch_one(
        """
        SELECT e.*, c.category_name
        FROM exams e
        LEFT JOIN categories c ON c.category_id = e.category_id
        WHERE e.exam_id = %s
        """,
        (exam_id,),
    )
    if exam:
        exam["criteria"] = fetch_one(
            """
            SELECT * FROM eligibility_criteria
            WHERE exam_id = %s
            ORDER BY criteria_id LIMIT 1
            """,
            (exam_id,),
        )
    return exam


@app.route("/")
def home():
    categories = fetch_all(
        "SELECT category_id, category_name FROM categories ORDER BY category_name"
    )
    featured_exams = fetch_all(
        "SELECT exam_id, exam_name, conducting_authority FROM exams ORDER BY exam_name LIMIT 6"
    )
    return render_template(
        "index.html",
        categories=categories or [],
        featured_exams=featured_exams or [],
    )


@app.route("/auth")
def auth():
    if session.get("student_id"):
        return redirect(url_for("dashboard"))
    return render_template("auth.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    dob_text = request.form.get("date_of_birth", "").strip()
    qualification = request.form.get("qualification", "").strip()
    stream = request.form.get("stream", "").strip()
    percentage_text = request.form.get("percentage", "").strip()

    if not all([name, email, password, dob_text, qualification, stream]):
        flash("Please fill all required registration fields.", "error")
        return redirect(url_for("auth"))

    if len(password) < 8:
        flash("Password must contain at least 8 characters.", "error")
        return redirect(url_for("auth"))

    try:
        dob = date.fromisoformat(dob_text)
        percentage = float(percentage_text) if percentage_text else None
        if percentage is not None and not 0 <= percentage <= 100:
            raise ValueError
    except ValueError:
        flash("Enter a valid date of birth and percentage (0–100).", "error")
        return redirect(url_for("auth"))

    existing = fetch_one("SELECT student_id FROM students WHERE email = %s", (email,))
    if existing:
        flash("Email already registered. Please log in.", "error")
        return redirect(url_for("auth"))

    try:
        student_id = execute_query(
            """
            INSERT INTO students
            (name, email, password, date_of_birth, qualification, stream, percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name, email, generate_password_hash(password), dob,
             qualification, stream, percentage),
        )
        if student_id is None:
            flash("Could not connect to the database.", "error")
            return redirect(url_for("auth"))

        session.clear()
        session["student_id"] = student_id
        session["student_name"] = name
        flash("Registration successful.", "success")
        return redirect(url_for("dashboard"))
    except Exception:
        app.logger.exception("Registration failed")
        flash("Registration failed. Please try again.", "error")
        return redirect(url_for("auth"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        flash("Enter email and password.", "error")
        return redirect(url_for("auth"))

    student = fetch_one(
        "SELECT student_id, name, password FROM students WHERE email = %s",
        (email,),
    )
    if not student or not check_password_hash(student["password"], password):
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth"))

    session.clear()
    session["student_id"] = student["student_id"]
    session["student_name"] = student["name"]
    flash("Login successful.", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/exams")
def exams():
    category_id = request.args.get("category", type=int)
    search = request.args.get("q", "").strip()

    query = """
        SELECT e.exam_id, e.exam_name, e.conducting_authority,
               e.description, e.exam_date, e.application_deadline,
               c.category_name
        FROM exams e
        LEFT JOIN categories c ON c.category_id = e.category_id
        WHERE 1=1
    """
    params = []
    if category_id:
        query += " AND e.category_id = %s"
        params.append(category_id)
    if search:
        query += " AND (e.exam_name LIKE %s OR e.conducting_authority LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY e.exam_name"

    exams_list = fetch_all(query, tuple(params))
    categories = fetch_all(
        "SELECT category_id, category_name FROM categories ORDER BY category_name"
    )
    return render_template(
        "exams.html",
        exams=exams_list or [],
        categories=categories or [],
        selected_category=category_id,
        search_query=search,
    )


@app.route("/exam/<int:exam_id>")
def exam_details(exam_id):
    exam = get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "error")
        return redirect(url_for("exams"))

    eligibility = None
    if session.get("student_id"):
        student = fetch_one(
            """
            SELECT date_of_birth, qualification, stream, percentage
            FROM students WHERE student_id = %s
            """,
            (session["student_id"],),
        )
        if student:
            eligibility = check_eligibility(student, exam.get("criteria"))

    return render_template(
        "exam_details.html", exam=exam, eligibility=eligibility
    )


@app.route("/dashboard")
def dashboard():
    if not session.get("student_id"):
        flash("Please log in to view your dashboard.", "error")
        return redirect(url_for("auth"))

    student = fetch_one(
        """
        SELECT student_id, name, email, date_of_birth,
               qualification, stream, percentage
        FROM students WHERE student_id = %s
        """,
        (session["student_id"],),
    )
    if not student:
        session.clear()
        flash("Student account not found. Please log in again.", "error")
        return redirect(url_for("auth"))

    all_exams = fetch_all(
        """
        SELECT e.exam_id, e.exam_name, e.conducting_authority,
               e.description, e.exam_date, e.application_deadline,
               c.category_name
        FROM exams e
        LEFT JOIN categories c ON c.category_id = e.category_id
        ORDER BY e.exam_name
        """
    )

    recommendations = []
    for exam in all_exams or []:
        criteria = fetch_one(
            """
            SELECT qualification, stream, min_age, max_age, min_percentage,
                   additional_requirements
            FROM eligibility_criteria
            WHERE exam_id = %s
            ORDER BY criteria_id LIMIT 1
            """,
            (exam["exam_id"],),
        )
        result = check_eligibility(student, criteria)
        exam.update(result)
        if result["eligible"]:
            recommendations.append(exam)

    categories = fetch_all(
        "SELECT category_id, category_name FROM categories ORDER BY category_name"
    )
    return render_template(
        "dashboard.html",
        student=student,
        recommendations=recommendations,
        eligible_count=len(recommendations),
        categories=categories or [],
    )


@app.route("/test-db")
def test_db():
    db = get_db_connection()
    if db is None:
        return "Database connection failed!", 500

    cursor = None
    try:
        cursor = db.cursor()
        for table in ("students", "categories", "exams", "eligibility_criteria"):
            cursor.execute(f"DESCRIBE `{table}`")
            cursor.fetchall()
        return "Database connected and all 4 tables verified!"
    except Exception as error:
        app.logger.exception("Database test failed")
        return f"Database test failed: {error}", 500
    finally:
        if cursor:
            cursor.close()
        db.close()


@app.errorhandler(404)
def page_not_found(error):
    return "Page not found.", 404


if __name__ == "__main__":
    app.run(debug=True)