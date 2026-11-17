import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Read .env from the project root (one folder above database/).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_NAME = os.getenv("DB_NAME", "exam_recommender")


def setup_database():
    connection = None
    cursor = None

    try:
        # Connect to MySQL Server without selecting a database.
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = connection.cursor()

        # Create and select the project database.
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
        cursor.execute(f"USE `{DB_NAME}`")

        # 1. Students
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                date_of_birth DATE,
                qualification VARCHAR(50),
                stream VARCHAR(50),
                percentage DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # 2. Categories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INT AUTO_INCREMENT PRIMARY KEY,
                category_name VARCHAR(100) NOT NULL UNIQUE
            ) ENGINE=InnoDB
        """)

        # 3. Exams
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                exam_id INT AUTO_INCREMENT PRIMARY KEY,
                category_id INT NULL,
                exam_name VARCHAR(150) NOT NULL,
                conducting_authority VARCHAR(150),
                description TEXT,
                exam_pattern TEXT,
                application_link VARCHAR(500),
                notification_link VARCHAR(500),
                exam_date DATE,
                application_deadline DATE,
                CONSTRAINT fk_exams_category
                    FOREIGN KEY (category_id)
                    REFERENCES categories(category_id)
                    ON DELETE SET NULL
                    ON UPDATE CASCADE
            ) ENGINE=InnoDB
        """)

        # 4. Eligibility criteria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eligibility_criteria (
                criteria_id INT AUTO_INCREMENT PRIMARY KEY,
                exam_id INT NOT NULL,
                qualification VARCHAR(100),
                stream VARCHAR(100),
                min_age INT,
                max_age INT,
                min_percentage DECIMAL(5,2),
                additional_requirements TEXT,
                CONSTRAINT fk_eligibility_exam
                    FOREIGN KEY (exam_id)
                    REFERENCES exams(exam_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            ) ENGINE=InnoDB
        """)

        connection.commit()
        print(f"Database '{DB_NAME}' and all 4 tables are ready.")

    except Error as error:
        print("MySQL setup failed:", error)

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    setup_database()
