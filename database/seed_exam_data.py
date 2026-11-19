"""
Seed data for Exam Recommender.

Run from the project root:
    python seed_exam_data.py

Requirements:
    pip install mysql-connector-python python-dotenv

This script:
- Connects using the same .env settings as database/db_config.py.
- Inserts categories, exams and eligibility criteria into the existing 4-table schema.
- Avoids duplicate categories/exams/criteria when run more than once.
- Does NOT create or alter tables. Run database/setup_db.py first.

Important:
Eligibility is a starter-level mapping by minimum qualification. Actual exam
eligibility can also depend on age, subjects, category, nationality, degree
branch, passing year and the latest official notification. Check official
notifications before applying.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "exam_recommender"),
}

# Keep category names consistent with the existing categories table.
CATEGORIES = [
    "Government Jobs",
    "Engineering & Technical",
    "Medical",
    "University Admissions",
    "Defence",
    "Postgraduate & Research",
]

# Each exam has one minimum-qualification rule because the current Flask app
# reads only the first criteria row for an exam.
# Qualification and stream must match the values used in the registration form.
EXAMS = [
    {
        "category": "Government Jobs",
        "name": "SSC MTS and Havaldar",
        "authority": "Staff Selection Commission (SSC)",
        "description": "Recruitment examination for Multi-Tasking Staff and Havaldar posts in central government departments.",
        "pattern": "Computer Based Examination; additional PET/PST for Havaldar as notified.",
        "application": "https://ssc.gov.in/",
        "notification": "https://ssc.gov.in/",
        "qualification": "10th",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Matriculation is the basic educational qualification. Age limits differ by post and category; verify the current SSC notice.",
    },
    {
        "category": "Government Jobs",
        "name": "RRB Group D (Level 1)",
        "authority": "Railway Recruitment Boards (RRB)",
        "description": "Railway Level-1 recruitment for various posts. The Railway Board has specified 10th pass, ITI or equivalent/NAC for Level-1 recruitment.",
        "pattern": "Computer Based Test, Physical Efficiency Test and document/medical verification as notified.",
        "application": "https://www.rrbapply.gov.in/",
        "notification": "https://www.rrbcdg.gov.in/",
        "qualification": "10th",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "10th/ITI/NAC routes and age conditions must be checked in the relevant CEN notification.",
    },
    {
        "category": "Government Jobs",
        "name": "SSC CHSL",
        "authority": "Staff Selection Commission (SSC)",
        "description": "Combined Higher Secondary Level examination for posts such as LDC, JSA and DEO.",
        "pattern": "Tier-I Computer Based Examination and Tier-II as per the current notification.",
        "application": "https://ssc.gov.in/",
        "notification": "https://ssc.gov.in/",
        "qualification": "12th",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Some DEO posts require Science with Mathematics. Post-wise requirements and age limits vary.",
    },
    {
        "category": "Engineering & Technical",
        "name": "JEE Main",
        "authority": "National Testing Agency (NTA)",
        "description": "Entrance examination for undergraduate engineering, architecture and planning programmes, including NITs, IIITs and other participating institutes.",
        "pattern": "Computer Based Test; papers and subject combinations depend on the chosen programme.",
        "application": "https://jeemain.nta.nic.in/",
        "notification": "https://jeemain.nta.nic.in/",
        "qualification": "12th",
        "stream": "PCM",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "For B.E./B.Tech, required Class 12 subjects include Physics and Mathematics plus an approved third subject. Passing-year window and institute admission marks are notification-specific.",
    },
    {
        "category": "Medical",
        "name": "NEET UG",
        "authority": "National Testing Agency (NTA)",
        "description": "National entrance examination for undergraduate medical courses including MBBS and other programmes covered by the applicable regulations.",
        "pattern": "Pen-and-paper/OMR examination; subjects include Physics, Chemistry and Biology.",
        "application": "https://neet.nta.nic.in/",
        "notification": "https://neet.nta.nic.in/",
        "qualification": "12th",
        "stream": "PCB",
        "min_age": 17,
        "max_age": None,
        "min_percentage": None,
        "notes": "Physics, Chemistry, Biology/Biotechnology and English requirements apply. Minimum qualifying marks depend on category; verify the current bulletin.",
    },
    {
        "category": "University Admissions",
        "name": "CUET UG",
        "authority": "National Testing Agency (NTA)",
        "description": "Common entrance test used by central and participating universities for undergraduate admissions.",
        "pattern": "Computer Based Test; language, domain subjects and general test depend on university/course requirements.",
        "application": "https://cuet.nta.nic.in/",
        "notification": "https://cuet.nta.nic.in/",
        "qualification": "12th",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Programme and university-specific subject/marks conditions apply even when a candidate can appear for CUET UG.",
    },
    {
        "category": "Defence",
        "name": "NDA and NA Examination",
        "authority": "Union Public Service Commission (UPSC)",
        "description": "UPSC examination for admission to the National Defence Academy and Naval Academy.",
        "pattern": "Written examination followed by SSB interview and medical examination.",
        "application": "https://upsconline.nic.in/",
        "notification": "https://upsc.gov.in/examinations/active-examinations",
        "qualification": "12th",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Army Wing has a different subject requirement from Air Force/Naval Wings and the 10+2 Cadet Entry Scheme. Strict date-of-birth window applies.",
    },
    {
        "category": "Engineering & Technical",
        "name": "JEECUP (UP Polytechnic Entrance)",
        "authority": "Joint Entrance Examination Council, Uttar Pradesh",
        "description": "Uttar Pradesh entrance examination for admission to diploma-level polytechnic programmes.",
        "pattern": "Computer Based Test; group and subject pattern depend on the diploma programme.",
        "application": "https://jeecup.admissions.nic.in/",
        "notification": "https://jeecup.admissions.nic.in/",
        "qualification": "10th",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Eligibility differs by JEECUP group. Some groups require 10th, 12th or other specific qualifications; verify the selected group.",
    },
    {
        "category": "Engineering & Technical",
        "name": "RRB Assistant Loco Pilot (ALP)",
        "authority": "Railway Recruitment Boards (RRB)",
        "description": "Railway recruitment for Assistant Loco Pilot posts requiring specified technical qualifications.",
        "pattern": "CBT-1, CBT-2, Computer Based Aptitude Test where applicable, document verification and medical examination.",
        "application": "https://www.rrbapply.gov.in/",
        "notification": "https://www.rrbcdg.gov.in/",
        "qualification": "Diploma/ITI",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Only specified ITI trades or relevant engineering diplomas/degrees are accepted. The exact trade/branch list is notification-specific.",
    },
    {
        "category": "Engineering & Technical",
        "name": "SSC Junior Engineer (JE)",
        "authority": "Staff Selection Commission (SSC)",
        "description": "Recruitment examination for Junior Engineer posts in Civil, Mechanical and Electrical disciplines in specified departments.",
        "pattern": "Paper-I and Paper-II Computer Based Examinations, followed by document verification.",
        "application": "https://ssc.gov.in/",
        "notification": "https://ssc.gov.in/",
        "qualification": "Diploma/ITI",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "This is a simplified diploma route. Accepted diploma/degree branches and required experience differ by post; some posts accept degrees as well.",
    },
    {
        "category": "Government Jobs",
        "name": "UPSC Civil Services Examination",
        "authority": "Union Public Service Commission (UPSC)",
        "description": "Examination for recruitment to services such as IAS, IPS and IFS, subject to service-specific conditions.",
        "pattern": "Civil Services Preliminary Examination, Main Examination and Personality Test.",
        "application": "https://upsconline.nic.in/",
        "notification": "https://upsc.gov.in/examinations/active-examinations",
        "qualification": "Graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "A recognised bachelor's degree or equivalent is required. Age and attempt limits vary by category.",
    },
    {
        "category": "Government Jobs",
        "name": "SSC CGL",
        "authority": "Staff Selection Commission (SSC)",
        "description": "Combined Graduate Level recruitment for various Group B and Group C posts in central government departments.",
        "pattern": "Tier-I and Tier-II Computer Based Examinations; post-specific requirements may apply.",
        "application": "https://ssc.gov.in/",
        "notification": "https://ssc.gov.in/",
        "qualification": "Graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Bachelor's degree is the general requirement. Certain posts require specific subjects or additional qualifications.",
    },
    {
        "category": "Government Jobs",
        "name": "IBPS PO",
        "authority": "Institute of Banking Personnel Selection (IBPS)",
        "description": "Common recruitment process for Probationary Officer/Management Trainee posts in participating banks.",
        "pattern": "Preliminary Examination, Main Examination and interview.",
        "application": "https://www.ibps.in/",
        "notification": "https://www.ibps.in/",
        "qualification": "Graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "A graduation degree in any discipline is the general educational requirement; age and cut-off dates are notification-specific.",
    },
    {
        "category": "University Admissions",
        "name": "CAT",
        "authority": "IIMs (coordinated by a designated IIM)",
        "description": "Common Admission Test used by IIMs and other participating institutions for postgraduate management programmes.",
        "pattern": "Computer Based Test with VARC, DILR and Quantitative Ability sections.",
        "application": "https://iimcat.ac.in/",
        "notification": "https://iimcat.ac.in/",
        "qualification": "Graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": 50,
        "notes": "General/EWS/NC-OBC minimum marks and SC/ST/PwD relaxations differ. This seed uses 50% as a general-category baseline; reserved-category rules must be checked.",
    },
    {
        "category": "Engineering & Technical",
        "name": "GATE",
        "authority": "IISc and participating IITs (organising institute changes by year)",
        "description": "Graduate Aptitude Test in Engineering used for postgraduate admissions and, by some organisations, recruitment.",
        "pattern": "Computer Based Test; paper and syllabus depend on the chosen discipline.",
        "application": "https://gate2026.iitg.ac.in/",
        "notification": "https://gate2026.iitg.ac.in/",
        "qualification": "Graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Eligibility includes candidates in the third year or higher of specified undergraduate programmes and candidates with higher degrees. This profile field alone cannot verify year/branch.",
    },
    {
        "category": "Postgraduate & Research",
        "name": "CUET PG",
        "authority": "National Testing Agency (NTA)",
        "description": "Common entrance test for admission to postgraduate programmes at participating universities.",
        "pattern": "Computer Based Test; paper selection and eligibility depend on the programme/university.",
        "application": "https://exams.nta.ac.in/CUET-PG/",
        "notification": "https://exams.nta.ac.in/CUET-PG/",
        "qualification": "Graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Specific bachelor's subject, marks and degree conditions are set by the participating university and programme.",
    },
    {
        "category": "Postgraduate & Research",
        "name": "UGC NET",
        "authority": "National Testing Agency (NTA)",
        "description": "Eligibility test for Assistant Professor and/or Junior Research Fellowship in subjects covered by UGC NET.",
        "pattern": "Computer Based Test with two papers.",
        "application": "https://ugcnet.nta.nic.in/",
        "notification": "https://ugcnet.nta.nic.in/",
        "qualification": "Post-graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "General/EWS usually require 55% in master's; specified reserved categories require 50%. Subject of the postgraduate degree and JRF age rules matter. Percentage left blank because the current profile has no category field.",
    },
    {
        "category": "Postgraduate & Research",
        "name": "CSIR UGC NET",
        "authority": "National Testing Agency (NTA) / CSIR",
        "description": "National eligibility test for Junior Research Fellowship and Lectureship/Assistant Professor in specified science subjects.",
        "pattern": "Computer Based Test; subject-specific paper.",
        "application": "https://csirnet.nta.ac.in/",
        "notification": "https://csirnet.nta.ac.in/",
        "qualification": "Post-graduation",
        "stream": "Any",
        "min_age": None,
        "max_age": None,
        "min_percentage": None,
        "notes": "Subject/degree requirements and category-wise marks rules apply. Check the latest CSIR NET information bulletin.",
    },
]

def get_or_create_category(cursor, category_name):
    cursor.execute(
        "SELECT category_id FROM categories WHERE category_name = %s",
        (category_name,),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO categories (category_name) VALUES (%s)",
        (category_name,),
    )
    return cursor.lastrowid


def seed_database():
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        category_ids = {
            name: get_or_create_category(cursor, name)
            for name in CATEGORIES
        }

        inserted_exams = 0
        skipped_exams = 0
        inserted_criteria = 0

        for item in EXAMS:
            cursor.execute(
                "SELECT exam_id FROM exams WHERE exam_name = %s",
                (item["name"],),
            )
            existing = cursor.fetchone()

            if existing:
                exam_id = existing[0]
                skipped_exams += 1
            else:
                cursor.execute(
                    """
                    INSERT INTO exams
                    (category_id, exam_name, conducting_authority, description,
                     exam_pattern, application_link, notification_link,
                     exam_date, application_deadline)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, NULL)
                    """,
                    (
                        category_ids[item["category"]],
                        item["name"],
                        item["authority"],
                        item["description"],
                        item["pattern"],
                        item["application"],
                        item["notification"],
                    ),
                )
                exam_id = cursor.lastrowid
                inserted_exams += 1

            # Keep one criteria row per exam for compatibility with the
            # current get_exam() implementation in app.py.
            cursor.execute(
                """
                SELECT criteria_id
                FROM eligibility_criteria
                WHERE exam_id = %s
                ORDER BY criteria_id
                LIMIT 1
                """,
                (exam_id,),
            )
            criteria_exists = cursor.fetchone()

            if not criteria_exists:
                cursor.execute(
                    """
                    INSERT INTO eligibility_criteria
                    (exam_id, qualification, stream, min_age, max_age,
                     min_percentage, additional_requirements)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        exam_id,
                        item["qualification"],
                        item["stream"],
                        item["min_age"],
                        item["max_age"],
                        item["min_percentage"],
                        item["notes"],
                    ),
                )
                inserted_criteria += 1

        connection.commit()
        print("\nExam data seeding completed successfully.")
        print(f"New exams inserted: {inserted_exams}")
        print(f"Existing exams skipped: {skipped_exams}")
        print(f"New eligibility rows inserted: {inserted_criteria}")
        print(f"Categories available: {len(CATEGORIES)}")
        print("No tables were created or altered by this script.")

    except Error as error:
        if connection:
            connection.rollback()
        print("\nDatabase seeding failed:", error)
        print("Check MySQL Server, .env credentials, and run setup_db.py first.")
        sys.exit(1)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    seed_database()
