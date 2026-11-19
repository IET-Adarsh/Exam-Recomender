# Exam Recommender

A simple Flask + MySQL college mini-project. It lists examinations, lets students register/login, and applies basic rule-based eligibility checks using the four existing tables: `students`, `categories`, `exams`, and `eligibility_criteria`.

## Requirements
- Python 3.10 or newer
- MySQL Server running locally

## Setup (Windows)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set the MySQL username/password and a long random `SECRET_KEY`.

Create tables:

```bat
python database\setup_db.py
```

Insert the included sample catalogue:

```bat
python seed_exam_data.py
```

Start the Flask app:

```bat
python app.py
```

Open http://127.0.0.1:5000. Use `/test-db` to check the database connection.

## Notes
- The seed data is an initial sample catalogue, not a complete or permanently current list of examinations.
- Eligibility uses the first criteria row stored for an exam and simplified qualification-level/stream rules. Real exam rules can depend on age cut-offs, category, subject combinations, degree branch, passing year, nationality and the current notification. Always verify official notices before applying.
- `match_score` is a criteria-match percentage, not a probability of selection or admission.
- No AI/ML is used. The project uses ordinary rule-based comparisons.
