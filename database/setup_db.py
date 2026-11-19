import os
import re
import sys

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DB_NAME = os.getenv("DB_NAME", "exam_recommender")


def setup_database():
    if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
        raise ValueError("DB_NAME may contain only letters, numbers and underscores.")
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{DB_NAME}`")
        cursor.execute("""CREATE TABLE IF NOT EXISTS students (
            student_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            date_of_birth DATE NOT NULL,
            qualification VARCHAR(50) NOT NULL,
            stream VARCHAR(60) NOT NULL,
            percentage DECIMAL(5,2) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL UNIQUE
        ) ENGINE=InnoDB""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS exams (
            exam_id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT NULL,
            exam_name VARCHAR(150) NOT NULL UNIQUE,
            conducting_authority VARCHAR(150) NULL,
            description TEXT NULL,
            exam_pattern TEXT NULL,
            application_link VARCHAR(500) NULL,
            notification_link VARCHAR(500) NULL,
            exam_date DATE NULL,
            application_deadline DATE NULL,
            CONSTRAINT fk_exams_category FOREIGN KEY (category_id)
                REFERENCES categories(category_id) ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS eligibility_criteria (
            criteria_id INT AUTO_INCREMENT PRIMARY KEY,
            exam_id INT NOT NULL,
            qualification VARCHAR(100) NULL,
            stream VARCHAR(100) NULL,
            min_age INT NULL,
            max_age INT NULL,
            min_percentage DECIMAL(5,2) NULL,
            additional_requirements TEXT NULL,
            CONSTRAINT fk_eligibility_exam FOREIGN KEY (exam_id)
                REFERENCES exams(exam_id) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB""")
        connection.commit()
        print(f"Database '{DB_NAME}' and all 4 tables are ready.")
    except (Error, ValueError) as error:
        if connection:
            connection.rollback()
        print("MySQL setup failed:", error)
        sys.exit(1)
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    setup_database()
