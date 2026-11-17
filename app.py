from flask import Flask, render_template
from database.db_config import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    return "Exam Recommender is running!"


@app.route("/test-db")
def test_db():
    db = get_db_connection()

    if db is None:
        return "Database connection failed!"

    db.close()
    return "Database connected successfully!"


if __name__ == "__main__":
    app.run(debug=True)