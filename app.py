import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from database.db_config import get_db_connection  # noqa: E402

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "development-key-change-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@app.context_processor
def inject_user():
    """Expose the signed-in student's name to every template."""
    return {"current_user": session.get("student_name"), "calculate_age": calculate_age}


def fetch_one(query, params=()):
    db = get_db_connection()
    if db is None:
        return None
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchone()
    except Error:
        app.logger.exception("Database fetch_one failed")
        raise
    finally:
        if cursor:
            cursor.close()
        db.close()


def fetch_all(query, params=()):
    db = get_db_connection()
    if db is None:
        return []
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    except Error:
        app.logger.exception("Database fetch_all failed")
        raise
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
        app.logger.exception("Database write failed")
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


QUALIFICATION_LEVELS = {
    "10th": 1,
    "12th": 2,
    "diploma/iti": 3,
    "graduation": 4,
    "post-graduation": 5,
}


def _stream_matches(required, actual):
    required = (required or "Any").strip().lower()
    actual = (actual or "").strip().lower()
    if required in ("", "any", "all"):
        return True
    if not actual:
        return False
    if required == actual:
        return True
    if required == "science":
        return actual in {"science", "pcm", "pcb", "pcmb"}
    if required == "technical":
        return actual in {"technical", "computer science", "civil", "mechanical", "electrical", "electronics", "iti"}
    return False


def check_eligibility(student, criteria):
    """Rule-based comparison; match_score is not a probability."""
    if not criteria:
        return {"eligible": False, "status": "Criteria not available", "match_score": 0}

    checks = []
    required_qualification = (criteria.get("qualification") or "Any").strip().lower()
    actual_qualification = (student.get("qualification") or "").strip().lower()

    if required_qualification not in ("", "any", "all"):
        required_level = QUALIFICATION_LEVELS.get(required_qualification)
        actual_level = QUALIFICATION_LEVELS.get(actual_qualification)
        checks.append(
            required_level is not None
            and actual_level is not None
            and actual_level >= required_level
        )

    required_stream = criteria.get("stream")
    if required_stream and required_stream.strip().lower() not in ("any", "all"):
        checks.append(_stream_matches(required_stream, student.get("stream")))

    age = calculate_age(student.get("date_of_birth"))
    min_age = criteria.get("min_age")
    max_age = criteria.get("max_age")
    if min_age is not None or max_age is not None:
        checks.append(
            age is not None
            and (min_age is None or age >= int(min_age))
            and (max_age is None or age <= int(max_age))
        )

    min_percentage = criteria.get("min_percentage")
    if min_percentage is not None:
        percentage = student.get("percentage")
        checks.append(percentage is not None and float(percentage) >= float(min_percentage))

    if not checks:
        return {"eligible": False, "status": "Criteria incomplete", "match_score": 0}

    score = round(sum(bool(check) for check in checks) / len(checks) * 100)
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
            """SELECT * FROM eligibility_criteria
               WHERE exam_id = %s ORDER BY criteria_id LIMIT 1""",
            (exam_id,),
        )
    return exam


@app.route("/")
def home():
    categories = fetch_all(
        "SELECT category_id, category_name FROM categories ORDER BY category_name"
    )
    featured_exams = fetch_all(
        """SELECT exam_id, exam_name, conducting_authority
           FROM exams ORDER BY exam_name LIMIT 6"""
    )
    total_row = fetch_one("SELECT COUNT(*) AS total FROM exams") or {"total": 0}
    return render_template(
        "index.html",
        categories=categories,
        featured_exams=featured_exams,
        total_exams=total_row["total"],
    )


@app.route("/auth")
def auth():
    if session.get("student_id"):
        return redirect(url_for("dashboard"))
    categories = fetch_all(
        "SELECT category_id, category_name FROM categories ORDER BY category_name"
    )
    return render_template("auth.html", categories=categories, active_tab=request.args.get("tab", "login"), today=date.today().isoformat())


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
        return redirect(url_for("auth", tab="register"))
    if len(password) < 8:
        flash("Password must contain at least 8 characters.", "error")
        return redirect(url_for("auth", tab="register"))

    try:
        dob = date.fromisoformat(dob_text)
        if dob >= date.today():
            raise ValueError
        percentage = float(percentage_text) if percentage_text else None
        if percentage is not None and not 0 <= percentage <= 100:
            raise ValueError
    except ValueError:
        flash("Enter a valid past date of birth and percentage between 0 and 100.", "error")
        return redirect(url_for("auth", tab="register"))

    try:
        if fetch_one("SELECT student_id FROM students WHERE email = %s", (email,)):
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("auth"))

        student_id = execute_query(
            """INSERT INTO students
               (name, email, password, date_of_birth, qualification, stream, percentage)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, email, generate_password_hash(password), dob,
             qualification, stream, percentage),
        )
        if student_id is None:
            flash("Could not connect to the database. Check MySQL settings.", "error")
            return redirect(url_for("auth", tab="register"))
        session.clear()
        session["student_id"] = student_id
        session["student_name"] = name
        flash("Registration successful.", "success")
        return redirect(url_for("dashboard"))
    except Error as error:
        app.logger.exception("Registration failed")
        if getattr(error, "errno", None) == 1062:
            flash("This email is already registered.", "error")
        else:
            flash("Registration failed. Check the database and try again.", "error")
        return redirect(url_for("auth", tab="register"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        flash("Enter email and password.", "error")
        return redirect(url_for("auth"))
    try:
        student = fetch_one(
            "SELECT student_id, name, password FROM students WHERE email = %s", (email,)
        )
    except Error:
        flash("Database is unavailable. Please try again.", "error")
        return redirect(url_for("auth"))
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
    query = """SELECT e.exam_id, e.category_id, e.exam_name,
                      e.conducting_authority, e.description, e.exam_date,
                      e.application_deadline, c.category_name
               FROM exams e
               LEFT JOIN categories c ON c.category_id = e.category_id
               WHERE 1=1"""
    params = []
    if category_id:
        query += " AND e.category_id = %s"
        params.append(category_id)
    if search:
        query += " AND (e.exam_name LIKE %s OR e.conducting_authority LIKE %s OR e.description LIKE %s)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY e.exam_name"
    exam_rows = fetch_all(query, tuple(params))
    categories = fetch_all(
        "SELECT category_id, category_name FROM categories ORDER BY category_name"
    )
    return render_template(
        "exams.html", exams=exam_rows, categories=categories,
        selected_category=category_id, search_query=search,
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
            """SELECT date_of_birth, qualification, stream, percentage
               FROM students WHERE student_id = %s""",
            (session["student_id"],),
        )
        if student:
            eligibility = check_eligibility(student, exam.get("criteria"))
    return render_template("exam_details.html", exam=exam, eligibility=eligibility)


@app.route("/dashboard")
def dashboard():
    if not session.get("student_id"):
        flash("Please log in to view your dashboard.", "error")
        return redirect(url_for("auth"))
    student = fetch_one(
        """SELECT student_id, name, email, date_of_birth,
                  qualification, stream, percentage
           FROM students WHERE student_id = %s""",
        (session["student_id"],),
    )
    if not student:
        session.clear()
        flash("Student account not found. Please log in again.", "error")
        return redirect(url_for("auth"))

    all_exams = fetch_all(
        """SELECT e.exam_id, e.category_id, e.exam_name, e.conducting_authority,
                  e.description, e.exam_date, e.application_deadline,
                  c.category_name
           FROM exams e LEFT JOIN categories c ON c.category_id = e.category_id
           ORDER BY e.exam_name"""
    )
    criteria_rows = fetch_all(
        """SELECT ec.* FROM eligibility_criteria ec
           INNER JOIN (SELECT exam_id, MIN(criteria_id) AS criteria_id
                       FROM eligibility_criteria GROUP BY exam_id) first_row
           ON first_row.criteria_id = ec.criteria_id"""
    )
    criteria_by_exam = {row["exam_id"]: row for row in criteria_rows}
    recommendations = []
    for exam in all_exams:
        result = check_eligibility(student, criteria_by_exam.get(exam["exam_id"]))
        exam.update(result)
        if result["eligible"]:
            recommendations.append(exam)

    return render_template(
        "dashboard.html", student=student, recommendations=recommendations,
        eligible_count=len(recommendations),
    )


@app.route("/test-db")
def test_db():
    db = get_db_connection()
    if db is None:
        return "Database connection failed. Check .env and MySQL Server.", 500
    cursor = None
    try:
        cursor = db.cursor()
        for table in ("students", "categories", "exams", "eligibility_criteria"):
            cursor.execute(f"DESCRIBE `{table}`")
            cursor.fetchall()
        return "Database connected and all 4 tables verified!"
    except Error:
        app.logger.exception("Database test failed")
        return "Database test failed. Run database/setup_db.py and check MySQL settings.", 500
    finally:
        if cursor:
            cursor.close()
        db.close()


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(_error):
    app.logger.exception("Unhandled server error")
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
