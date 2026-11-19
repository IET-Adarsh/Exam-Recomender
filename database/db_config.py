import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_db_connection():
    """Create and return a connection to the configured MySQL database."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "exam_recommender"),
            charset="utf8mb4",
        )
    except Error as error:
        print("MySQL connection failed:", error)
        return None
