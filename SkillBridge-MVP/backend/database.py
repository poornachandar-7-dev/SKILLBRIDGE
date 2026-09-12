# backend/database.py
#
# WHAT THIS FILE DOES:
# This file is responsible for:
#   1. Creating the data folder and SQLite database file safely
#   2. Creating all the tables SkillBridge needs (if they don't exist yet)
#   3. Opening safe connections with foreign-key enforcement enabled
#   4. Providing safe, parameterized CRUD functions for users, skills, and student assessments
#   5. Providing database health and relationship diagnostic checks
#
# WHY WE NEED THIS FILE:
# Every other part of the backend (auth, assessment, matching, etc.) will
# need to save or read data. Instead of every file writing its own database
# connection code, they all come here and use standard functions.
# This keeps all database logic in ONE place.

import sqlite3
import os
import json
from datetime import datetime, date, timedelta

# ---------------------------------------------------------
# WHAT IS "sqlite3"?
# sqlite3 is a built-in Python module (no installation needed) that lets
# Python talk to a SQLite database. SQLite stores the entire database as
# a single file on your computer (data/skillbridge.db) — no separate
# database server needed. Perfect for an MVP.
# ---------------------------------------------------------

# ---------------------------------------------------------
# BUILDING THE FILE PATH TO OUR DATABASE
# ---------------------------------------------------------
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DB_DIR, "skillbridge.db")

# Safety check: make sure the directory exists before any connection attempt
os.makedirs(DB_DIR, exist_ok=True)

# The 4 MVP skills required for Stage 4
DEFAULT_SKILLS = ["Python", "Java", "Web Development", "Data Structures"]

# Default achievement badges catalog for gamification
DEFAULT_BADGES = [
    {
        "id": "first_step",
        "name": "First Step",
        "description": "Completed your first skill assessment",
        "icon": "🎯",
        "category": "Assessment",
        "xp_bonus": 50,
    },
    {
        "id": "python_pro",
        "name": "Python Prodigy",
        "description": "Scored 80% or higher on Python assessment",
        "icon": "🐍",
        "category": "Skill Mastery",
        "xp_bonus": 75,
    },
    {
        "id": "java_champ",
        "name": "Java Champion",
        "description": "Scored 80% or higher on Java assessment",
        "icon": "☕",
        "category": "Skill Mastery",
        "xp_bonus": 75,
    },
    {
        "id": "web_architect",
        "name": "Web Architect",
        "description": "Scored 80% or higher on Web Development",
        "icon": "🌐",
        "category": "Skill Mastery",
        "xp_bonus": 75,
    },
    {
        "id": "algo_ace",
        "name": "Algorithm Ace",
        "description": "Scored 80% or higher on Data Structures",
        "icon": "⚡",
        "category": "Skill Mastery",
        "xp_bonus": 75,
    },
    {
        "id": "skill_master",
        "name": "Skill All-Rounder",
        "description": "Assessed across all core MVP skill domains",
        "icon": "🏆",
        "category": "Mastery",
        "xp_bonus": 150,
    },
    {
        "id": "first_app",
        "name": "Opportunity Hunter",
        "description": "Applied to your first internship or job",
        "icon": "🚀",
        "category": "Career",
        "xp_bonus": 50,
    },
    {
        "id": "streak_3",
        "name": "Streak Starter",
        "description": "Maintained a 3-day continuous learning streak",
        "icon": "🔥",
        "category": "Consistency",
        "xp_bonus": 50,
    },
    {
        "id": "streak_7",
        "name": "Consistency Master",
        "description": "Maintained a 7-day continuous learning streak",
        "icon": "⭐",
        "category": "Consistency",
        "xp_bonus": 100,
    },
    {
        "id": "top_tier",
        "name": "Leaderboard Elite",
        "description": "Ranked in the Student Top 3 leaderboard",
        "icon": "🥇",
        "category": "Excellence",
        "xp_bonus": 150,
    },
    {
        "id": "screening_star",
        "name": "Screening Star",
        "description": "Passed a company screening test with flying colors",
        "icon": "⭐",
        "category": "Industry Readiness",
        "xp_bonus": 75,
    },
]

LEVEL_THRESHOLDS = [
    (1, 0, "Novice Explorer"),
    (2, 100, "Skill Apprentice"),
    (3, 250, "Proficient Builder"),
    (4, 500, "Advanced Specialist"),
    (5, 850, "Career Ready"),
    (6, 1300, "Industry Master"),
    (7, 1900, "Grandmaster Innovator"),
]


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Opens a connection to the SQLite database and returns it.

    Parameters:
        db_path (str, optional): Custom path to a database file (used for isolated tests).
                                 Defaults to DB_PATH (data/skillbridge.db).
    """
    target_path = db_path or DB_PATH
    # Ensure the parent directory exists for whatever path was requested
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    # Autocommit keeps a failed constraint statement from holding a write
    # lock after a caller closes its connection without an explicit rollback.
    # Each write helper still calls commit() for clarity and compatibility
    # with the original Stage 2–4 implementation.
    connection = sqlite3.connect(target_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    # Explicitly enable foreign-key constraint enforcement
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db(db_path: str = None):
    """
    Creates all the tables SkillBridge needs, if they don't already exist.
    Safe to call multiple times (idempotent) — will never delete existing data.
    """
    connection = get_connection(db_path)
    cursor = connection.cursor()

    # -----------------------------------------------------
    # TABLE 1: users
    # Stores accounts for all 4 roles: student, industry, academician, institution
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'industry', 'academician', 'institution')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # TABLE 2: skills
    # A master catalog of skills (e.g. Python, Java, Web Development, Data Structures)
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # -----------------------------------------------------
    # TABLE 3: student_skills
    # Stores a student's assessed skill scores (0 to 100)
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)

    # -----------------------------------------------------
    # TABLE 4: opportunities
    # Jobs/internships posted by industry users
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            opportunity_type TEXT CHECK(opportunity_type IN ('internship', 'job')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (industry_id) REFERENCES users(id)
        )
    """)

    # -----------------------------------------------------
    # TABLE 5: opportunity_skills
    # Skills and minimum scores required by an opportunity
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunity_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            required_score INTEGER NOT NULL CHECK(required_score >= 0 AND required_score <= 100),
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        )
    """)

    # -----------------------------------------------------
    # TABLE 6: applications
    # Tracks student applications to opportunities
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            opportunity_id INTEGER NOT NULL,
            status TEXT DEFAULT 'applied' CHECK(status IN ('applied', 'shortlisted', 'rejected', 'accepted')),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        )
    """)

    # -----------------------------------------------------
    # SAFE MVP EXTENSIONS
    # These migrations keep databases created by Stages 1-4 usable.
    # -----------------------------------------------------
    user_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(users);").fetchall()
    }
    if "age" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER;")
    if "gender" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT;")

    opportunity_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(opportunities);").fetchall()
    }
    if "company_name" not in opportunity_columns:
        cursor.execute(
            "ALTER TABLE opportunities ADD COLUMN company_name TEXT NOT NULL DEFAULT 'Unnamed organization';"
        )

    # The API also checks for duplicates, while this index protects the
    # invariant when two requests arrive at nearly the same time.
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_applications_student_opportunity
            ON applications(student_id, opportunity_id);
        """)
    except sqlite3.IntegrityError:
        # Do not delete or rewrite historical rows during startup. The API
        # duplicate check still protects new writes; a later maintenance
        # migration can consolidate legacy duplicates explicitly.
        pass
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_opportunities_industry
        ON opportunities(industry_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_opportunity_skills_opportunity
        ON opportunity_skills(opportunity_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_applications_opportunity
        ON applications(opportunity_id);
    """)

    # -----------------------------------------------------
    # TABLE 7: student_gamification
    # Tracks XP, active streaks, level, and last activity date
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_gamification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER UNIQUE NOT NULL,
            xp INTEGER NOT NULL DEFAULT 0,
            streak INTEGER NOT NULL DEFAULT 1,
            last_active_date TEXT,
            level INTEGER NOT NULL DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    """)

    # -----------------------------------------------------
    # TABLE 8: badges
    # Catalog of milestone badges that students can unlock
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            category TEXT NOT NULL,
            xp_bonus INTEGER NOT NULL DEFAULT 25
        )
    """)

    # -----------------------------------------------------
    # TABLE 9: user_badges
    # Badges awarded to users with timestamps
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id TEXT NOT NULL,
            awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (badge_id) REFERENCES badges(id)
        )
    """)

    # -----------------------------------------------------
    # TABLE 10: xp_activities
    # Complete activity log of XP earned by each student
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            xp_earned INTEGER NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_student_gamification_student
        ON student_gamification(student_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_badges_user
        ON user_badges(user_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_xp_activities_user
        ON xp_activities(user_id);
    """)

    # -----------------------------------------------------
    # TABLE 11: screening_tests
    # Custom tests created by industry recruiters for opportunities
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            passing_score INTEGER NOT NULL DEFAULT 60,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        );
    """)

    # -----------------------------------------------------
    # TABLE 12: screening_questions
    # Questions attached to a company screening test
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_option INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES screening_tests(id)
        );
    """)

    # -----------------------------------------------------
    # TABLE 13: screening_attempts
    # Student attempts and scores for screening tests
    # -----------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            opportunity_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            passed BOOLEAN NOT NULL,
            answers_json TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, test_id),
            FOREIGN KEY (test_id) REFERENCES screening_tests(id),
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_tests_opp ON screening_tests(opportunity_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_questions_test ON screening_questions(test_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_attempts_student ON screening_attempts(student_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_attempts_opp ON screening_attempts(opportunity_id);")

    # Seed default badges catalog
    for badge in DEFAULT_BADGES:
        cursor.execute("""
            INSERT OR REPLACE INTO badges (id, name, description, icon, category, xp_bonus)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (badge["id"], badge["name"], badge["description"], badge["icon"], badge["category"], badge["xp_bonus"]))

    # Commit the changes and close the connection
    connection.commit()
    connection.close()
    try:
        seed_demo_screening_test(db_path)
    except Exception:
        pass

    print("Database initialized - tables are ready.")


# =========================================================
# SKILLS SEEDING FUNCTION (Stage 4)
# =========================================================

def seed_default_skills(db_path: str = None):
    """
    Safely ensures the 4 MVP skills exist in the skills table:
      1. Python
      2. Java
      3. Web Development
      4. Data Structures
      
    Uses INSERT OR IGNORE to prevent duplicates if skills already exist.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        for skill_name in DEFAULT_SKILLS:
            cursor.execute("INSERT OR IGNORE INTO skills (name) VALUES (?);", (skill_name,))
        connection.commit()
    finally:
        connection.close()


# =========================================================
# USER CRUD FUNCTIONS (Stage 3 Authentication Foundation)
# =========================================================

def create_user(
    name: str,
    email: str,
    password_hash: str,
    role: str,
    age: int = None,
    gender: str = None,
    db_path: str = None
) -> dict:
    """
    CREATE: Adds a new user account into the users table with age and gender.
    """
    clean_name = name.strip()
    clean_email = email.strip().lower()
    clean_role = role.strip().lower()
    clean_gender = gender.strip().title() if gender and gender.strip() else None
    clean_age = int(age) if age is not None else None

    allowed_roles = ('student', 'industry', 'academician', 'institution')
    if clean_role not in allowed_roles:
        raise ValueError(f"Invalid role '{clean_role}'. Must be one of {allowed_roles}.")

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role, age, gender)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (clean_name, clean_email, password_hash, clean_role, clean_age, clean_gender)
        )
        connection.commit()
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "name": clean_name,
            "email": clean_email,
            "role": clean_role,
            "age": clean_age,
            "gender": clean_gender
        }
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "users.email" in err_msg:
            raise ValueError(f"An account with email '{clean_email}' already exists.")
        raise ValueError(f"Database constraint error: {str(e)}")
    finally:
        connection.close()


def get_user_by_email(email: str, db_path: str = None) -> dict:
    """
    READ: Finds a user by email address (case-insensitive).
    """
    clean_email = email.strip().lower()
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, email, password_hash, role, age, gender, created_at
            FROM users
            WHERE LOWER(email) = LOWER(?);
            """,
            (clean_email,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        connection.close()


def get_user_by_id(user_id: int, db_path: str = None) -> dict:
    """
    READ: Finds a user by their primary key ID.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, email, password_hash, role, age, gender, created_at
            FROM users
            WHERE id = ?;
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        connection.close()


# =========================================================
# SKILLS CRUD FUNCTIONS (Preserved from Stage 2)
# =========================================================

def get_all_skills(db_path: str = None) -> list:
    """
    READ: Retrieves all skills from the skills table, ordered by ID.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM skills ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [{"id": row["id"], "name": row["name"]} for row in rows]
    finally:
        connection.close()


def get_skill_by_id(skill_id: int, db_path: str = None) -> dict:
    """
    READ: Retrieves a single skill by its primary key ID.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM skills WHERE id = ?;", (skill_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row["id"], "name": row["name"]}
        return None
    finally:
        connection.close()


def get_skill_by_name(name: str, db_path: str = None) -> dict:
    """
    READ: Finds a skill by name (case-insensitive search).
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM skills WHERE LOWER(name) = LOWER(?);", (name.strip(),))
        row = cursor.fetchone()
        if row:
            return {"id": row["id"], "name": row["name"]}
        return None
    finally:
        connection.close()


def create_skill(name: str, db_path: str = None) -> dict:
    """
    CREATE: Adds a new skill to the skills table.
    """
    clean_name = name.strip()
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO skills (name) VALUES (?);", (clean_name,))
        connection.commit()
        new_id = cursor.lastrowid
        return {"id": new_id, "name": clean_name}
    except sqlite3.IntegrityError:
        raise ValueError(f"A skill named '{clean_name}' already exists.")
    finally:
        connection.close()


def update_skill(skill_id: int, new_name: str, db_path: str = None) -> dict:
    """
    UPDATE: Changes the name of an existing skill.
    """
    clean_name = new_name.strip()
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM skills WHERE id = ?;", (skill_id,))
        existing = cursor.fetchone()
        if not existing:
            return None

        cursor.execute("UPDATE skills SET name = ? WHERE id = ?;", (clean_name, skill_id))
        connection.commit()
        return {"id": skill_id, "name": clean_name}
    except sqlite3.IntegrityError:
        raise ValueError(f"A skill named '{clean_name}' already exists.")
    finally:
        connection.close()


def delete_skill(skill_id: int, db_path: str = None) -> bool:
    """
    DELETE: Removes a skill from the skills table by ID.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM skills WHERE id = ?;", (skill_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


# =========================================================
# STUDENT SKILLS FUNCTIONS (Stage 4 Assessment Storage)
# =========================================================

def get_student_skills(student_id: int, db_path: str = None) -> list:
    """
    READ: Retrieves all skill scores recorded for a specific student.
    Joins student_skills with skills table to include readable skill names.
    Returns:
        [{"skill_id": 1, "skill_name": "Python", "score": 100}, ...]
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT ss.skill_id, s.name AS skill_name, ss.score
            FROM student_skills ss
            JOIN skills s ON ss.skill_id = s.id
            WHERE ss.student_id = ?
            ORDER BY s.id ASC;
        """, (student_id,))
        rows = cursor.fetchall()
        return [
            {
                "skill_id": row["skill_id"],
                "skill_name": row["skill_name"],
                "score": row["score"]
            }
            for row in rows
        ]
    finally:
        connection.close()


def save_or_update_student_skill(student_id: int, skill_id: int, score: int, db_path: str = None) -> dict:
    """
    CREATE or UPDATE: Saves a student's score for a specific skill.
    
    If the student already has a recorded score for this skill, updates it.
    If not, inserts a new record.
    
    This ensures that retaking an assessment updates the profile rather
    than creating redundant duplicate rows in student_skills.
    """
    clamped_score = max(0, min(100, int(score)))
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        # Check if record already exists for this (student_id, skill_id) pair
        cursor.execute("""
            SELECT id FROM student_skills
            WHERE student_id = ? AND skill_id = ?;
        """, (student_id, skill_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE student_skills
                SET score = ?
                WHERE student_id = ? AND skill_id = ?;
            """, (clamped_score, student_id, skill_id))
            record_id = existing["id"]
        else:
            cursor.execute("""
                INSERT INTO student_skills (student_id, skill_id, score)
                VALUES (?, ?, ?);
            """, (student_id, skill_id, clamped_score))
            record_id = cursor.lastrowid

        connection.commit()
        return {
            "id": record_id,
            "student_id": student_id,
            "skill_id": skill_id,
            "score": clamped_score
        }
    finally:
        connection.close()


# =========================================================
# OPPORTUNITIES, MATCHING INPUTS & APPLICATIONS (MVP)
# =========================================================

def _row_to_opportunity(row: sqlite3.Row, skills: list = None) -> dict:
    """Convert an opportunity row into a JSON-safe dictionary."""
    result = {
        "id": row["id"],
        "industry_id": row["industry_id"],
        "title": row["title"],
        "description": row["description"] or "",
        "company_name": row["company_name"] or "Unnamed organization",
        "opportunity_type": row["opportunity_type"] or "internship",
        "created_at": row["created_at"],
    }
    if skills is not None:
        result["required_skills"] = skills
    return result


def _opportunity_skills(connection: sqlite3.Connection, opportunity_id: int) -> list:
    rows = connection.execute("""
        SELECT os.skill_id, s.name AS skill_name, os.required_score
        FROM opportunity_skills os
        JOIN skills s ON s.id = os.skill_id
        WHERE os.opportunity_id = ?
        ORDER BY s.id ASC;
    """, (opportunity_id,)).fetchall()
    return [
        {
            "skill_id": row["skill_id"],
            "skill_name": row["skill_name"],
            "required_score": row["required_score"],
        }
        for row in rows
    ]


def create_opportunity(
    industry_id: int,
    title: str,
    description: str,
    company_name: str,
    required_skills: list,
    db_path: str = None,
) -> dict:
    """
    Creates an opportunity and its required skills atomically.

    required_skills is a list of {"skill_id": int, "required_score": int}
    dictionaries. Skill IDs are resolved against the database so callers
    cannot attach an opportunity to a non-existent skill.
    """
    clean_title = title.strip()
    clean_description = (description or "").strip()
    clean_company = company_name.strip()
    if not clean_title or not clean_company:
        raise ValueError("Title and company name are required.")
    if not required_skills:
        raise ValueError("At least one required skill must be selected.")

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO opportunities
                (industry_id, title, description, company_name, opportunity_type)
            VALUES (?, ?, ?, ?, 'internship');
            """,
            (industry_id, clean_title, clean_description, clean_company),
        )
        opportunity_id = cursor.lastrowid

        seen_skill_ids = set()
        for required in required_skills:
            skill_id = int(required["skill_id"])
            required_score = max(0, min(100, int(required.get("required_score", 50))))
            if skill_id in seen_skill_ids:
                raise ValueError("Each required skill may only be added once.")
            skill = cursor.execute(
                "SELECT id FROM skills WHERE id = ?;", (skill_id,)
            ).fetchone()
            if not skill:
                raise ValueError(f"Skill with ID {skill_id} does not exist.")
            seen_skill_ids.add(skill_id)
            cursor.execute(
                """
                INSERT INTO opportunity_skills
                    (opportunity_id, skill_id, required_score)
                VALUES (?, ?, ?);
                """,
                (opportunity_id, skill_id, required_score),
            )

        connection.commit()
        row = cursor.execute(
            "SELECT * FROM opportunities WHERE id = ?;", (opportunity_id,)
        ).fetchone()
        return _row_to_opportunity(row, _opportunity_skills(connection, opportunity_id))
    except (sqlite3.IntegrityError, KeyError, TypeError, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


def get_opportunity(opportunity_id: int, db_path: str = None) -> dict:
    connection = get_connection(db_path)
    try:
        row = connection.execute(
            "SELECT * FROM opportunities WHERE id = ?;", (opportunity_id,)
        ).fetchone()
        if not row:
            return None
        return _row_to_opportunity(row, _opportunity_skills(connection, opportunity_id))
    finally:
        connection.close()


def get_opportunities(industry_id: int = None, db_path: str = None) -> list:
    connection = get_connection(db_path)
    try:
        if industry_id is None:
            rows = connection.execute(
                "SELECT * FROM opportunities ORDER BY created_at DESC, id DESC;"
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM opportunities
                WHERE industry_id = ?
                ORDER BY created_at DESC, id DESC;
                """,
                (industry_id,),
            ).fetchall()
        return [
            _row_to_opportunity(row, _opportunity_skills(connection, row["id"]))
            for row in rows
        ]
    finally:
        connection.close()


def create_application(student_id: int, opportunity_id: int, db_path: str = None) -> dict:
    connection = get_connection(db_path)
    try:
        opportunity = connection.execute(
            "SELECT id FROM opportunities WHERE id = ?;", (opportunity_id,)
        ).fetchone()
        if not opportunity:
            raise ValueError("Opportunity not found.")

        try:
            cursor = connection.execute(
                """
                INSERT INTO applications (student_id, opportunity_id, status)
                VALUES (?, ?, 'applied');
                """,
                (student_id, opportunity_id),
            )
            connection.commit()
        except sqlite3.IntegrityError as error:
            if "unique" in str(error).lower():
                raise ValueError("You have already applied to this opportunity.")
            raise

        row = connection.execute(
            """
            SELECT id, student_id, opportunity_id, status, applied_at
            FROM applications WHERE id = ?;
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return dict(row)
    finally:
        connection.close()


def get_student_applications(student_id: int, db_path: str = None) -> list:
    connection = get_connection(db_path)
    try:
        rows = connection.execute("""
            SELECT
                a.id, a.student_id, a.opportunity_id, a.status, a.applied_at,
                o.title, o.description, o.company_name, o.opportunity_type,
                o.industry_id, u.name AS industry_name,
                st.id AS screening_test_id,
                st.title AS screening_test_title,
                st.passing_score AS screening_passing_score,
                sa.score AS screening_score,
                sa.passed AS screening_passed
            FROM applications a
            JOIN opportunities o ON o.id = a.opportunity_id
            JOIN users u ON u.id = o.industry_id
            LEFT JOIN screening_tests st ON st.opportunity_id = o.id
            LEFT JOIN screening_attempts sa ON sa.test_id = st.id AND sa.student_id = a.student_id
            WHERE a.student_id = ?
            ORDER BY a.applied_at DESC, a.id DESC;
        """, (student_id,)).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["screening"] = {
                "score": d["screening_score"],
                "passed": bool(d["screening_passed"]) if d["screening_passed"] is not None else None,
            } if d.get("screening_score") is not None else None
            results.append(d)
        return results
    finally:
        connection.close()


def get_opportunity_applicants(opportunity_id: int, db_path: str = None) -> list:
    connection = get_connection(db_path)
    try:
        rows = connection.execute("""
            SELECT
                a.id AS application_id, a.student_id, a.opportunity_id,
                a.status, a.applied_at, u.name, u.email, u.age, u.gender,
                st.id AS screening_test_id,
                sa.score AS screening_score,
                sa.passed AS screening_passed,
                sa.attempted_at AS screening_attempted_at
            FROM applications a
            JOIN users u ON u.id = a.student_id
            LEFT JOIN screening_tests st ON st.opportunity_id = a.opportunity_id
            LEFT JOIN screening_attempts sa ON sa.test_id = st.id AND sa.student_id = a.student_id
            WHERE a.opportunity_id = ?
            ORDER BY a.applied_at DESC, a.id DESC;
        """, (opportunity_id,)).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["screening"] = {
                "score": d["screening_score"],
                "passed": bool(d["screening_passed"]) if d["screening_passed"] is not None else None,
                "attempted_at": d.get("screening_attempted_at"),
            } if d.get("screening_score") is not None else None
            results.append(d)
        return results
    finally:
        connection.close()


def update_application_status(
    application_id: int,
    industry_id: int,
    new_status: str,
    db_path: str = None,
) -> dict:
    clean_status = new_status.strip().lower()
    allowed_statuses = {"applied", "shortlisted", "rejected", "accepted"}
    if clean_status not in allowed_statuses:
        raise ValueError("Status must be applied, shortlisted, rejected, or accepted.")

    connection = get_connection(db_path)
    try:
        row = connection.execute("""
            SELECT a.id, a.student_id, a.opportunity_id, a.status, a.applied_at
            FROM applications a
            JOIN opportunities o ON o.id = a.opportunity_id
            WHERE a.id = ? AND o.industry_id = ?;
        """, (application_id, industry_id)).fetchone()
        if not row:
            return None
        connection.execute(
            "UPDATE applications SET status = ? WHERE id = ?;",
            (clean_status, application_id),
        )
        connection.commit()
        updated = dict(row)
        updated["status"] = clean_status
        return updated
    finally:
        connection.close()


def get_institution_statistics(db_path: str = None) -> dict:
    """Return aggregate readiness data without exposing individual students."""
    connection = get_connection(db_path)
    try:
        student_count = connection.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'student';"
        ).fetchone()[0]
        skill_rows = connection.execute("""
            SELECT
                s.name AS skill_name,
                COUNT(ss.id) AS assessed_students,
                ROUND(AVG(ss.score), 1) AS average_score,
                SUM(CASE WHEN ss.score < 50 THEN 1 ELSE 0 END) AS needs_improvement,
                SUM(CASE WHEN ss.score >= 80 THEN 1 ELSE 0 END) AS strong_students
            FROM skills s
            LEFT JOIN student_skills ss ON ss.skill_id = s.id
            GROUP BY s.id, s.name
            ORDER BY s.id ASC;
        """).fetchall()
        skills = [
            {
                "skill_name": row["skill_name"],
                "assessed_students": row["assessed_students"],
                "average_score": row["average_score"] or 0,
                "needs_improvement": row["needs_improvement"] or 0,
                "strong_students": row["strong_students"] or 0,
            }
            for row in skill_rows
        ]
        overall = connection.execute(
            "SELECT ROUND(AVG(score), 1) FROM student_skills;"
        ).fetchone()[0] or 0
        strongest = max(skills, key=lambda skill: skill["average_score"], default=None)
        assessed_skills = [
            skill for skill in skills if skill["assessed_students"] > 0
        ]
        weakest = min(
            assessed_skills or skills,
            key=lambda skill: skill["average_score"],
            default=None,
        )
        return {
            "student_count": student_count,
            "assessed_student_count": connection.execute(
                """
                SELECT COUNT(DISTINCT student_id)
                FROM student_skills;
                """
            ).fetchone()[0],
            "overall_readiness": overall,
            "skills": skills,
            "strongest_skill": strongest,
            "common_skill_gap": weakest,
        }
    finally:
        connection.close()


# =========================================================
# DATABASE DIAGNOSTICS & HEALTH CHECKS
# =========================================================

def get_database_health(db_path: str = None) -> dict:
    """
    Diagnostic function to verify:
    1. Database connection is working
    2. All expected tables are present
    3. Foreign key enforcement status
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        tables = [row["name"] for row in cursor.fetchall()]

        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]

        return {
            "status": "healthy",
            "database": "connected",
            "tables": tables,
            "foreign_keys": "enabled" if fk_status == 1 else "disabled"
        }
    finally:
        connection.close()


def get_foreign_key_relationships(db_path: str = None) -> dict:
    """
    Diagnostic function to inspect and list foreign key relationships
    defined across all tables in the database.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]

        tables = [
            "users", "skills", "student_skills", "opportunities",
            "opportunity_skills", "applications", "student_gamification",
            "badges", "user_badges", "xp_activities"
        ]
        relationships = {}

        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = cursor.fetchall()
            relationships[table] = [
                {
                    "from_column": fk["from"],
                    "target_table": fk["table"],
                    "target_column": fk["to"]
                }
                for fk in fks
            ]

        return {
            "foreign_keys_enforced": fk_status == 1,
            "relationships": relationships
        }
    finally:
        connection.close()


# =========================================================
# GAMIFICATION ENGINE (XP, STREAKS, BADGES & LEADERBOARD)
# =========================================================

def calculate_level_info(total_xp: int) -> dict:
    """
    Calculates student level, title, thresholds, and progress percentage from total XP.
    """
    xp = max(0, int(total_xp or 0))
    level = 1
    title = "Novice Explorer"
    current_threshold = 0
    next_threshold = 100

    for idx, (lvl, thresh, name) in enumerate(LEVEL_THRESHOLDS):
        if xp >= thresh:
            level = lvl
            title = name
            current_threshold = thresh
            if idx + 1 < len(LEVEL_THRESHOLDS):
                next_threshold = LEVEL_THRESHOLDS[idx + 1][1]
            else:
                next_threshold = current_threshold + 1000
        else:
            break

    span = max(next_threshold - current_threshold, 1)
    progress_xp = max(0, xp - current_threshold)
    progress_pct = min(100, int((progress_xp / span) * 100))

    return {
        "level": level,
        "title": title,
        "current_threshold": current_threshold,
        "next_threshold": next_threshold,
        "xp_to_next": max(0, next_threshold - xp),
        "progress_percentage": progress_pct,
    }


def get_or_create_student_gamification(student_id: int, db_path: str = None) -> dict:
    """
    Retrieves or initializes the student's gamification profile.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM student_gamification WHERE student_id = ?;",
            (student_id,)
        )
        row = cursor.fetchone()
        today_str = date.today().isoformat()
        if not row:
            cursor.execute(
                """
                INSERT INTO student_gamification (student_id, xp, streak, last_active_date, level)
                VALUES (?, 0, 1, ?, 1);
                """,
                (student_id, today_str),
            )
            connection.commit()
            cursor.execute(
                "SELECT * FROM student_gamification WHERE student_id = ?;",
                (student_id,)
            )
            row = cursor.fetchone()
        return dict(row)
    finally:
        connection.close()


def record_xp_activity(student_id: int, activity_type: str, xp_earned: int, description: str, db_path: str = None) -> dict:
    """
    Awards XP to a student, logs the event in xp_activities, updates level,
    and returns the new XP and level state.
    """
    if xp_earned <= 0:
        return {"student_id": student_id, "xp_earned": 0}

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        # 1. Log activity
        cursor.execute(
            """
            INSERT INTO xp_activities (user_id, activity_type, xp_earned, description)
            VALUES (?, ?, ?, ?);
            """,
            (student_id, activity_type, xp_earned, description),
        )

        # 2. Get current profile
        cursor.execute(
            "SELECT xp FROM student_gamification WHERE student_id = ?;",
            (student_id,)
        )
        row = cursor.fetchone()
        current_xp = row["xp"] if row else 0
        new_xp = current_xp + xp_earned
        lvl_info = calculate_level_info(new_xp)
        today_str = date.today().isoformat()

        cursor.execute(
            """
            INSERT INTO student_gamification (student_id, xp, streak, last_active_date, level, updated_at)
            VALUES (?, ?, 1, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id) DO UPDATE SET
                xp = excluded.xp,
                level = excluded.level,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (student_id, new_xp, today_str, lvl_info["level"]),
        )
        connection.commit()
        return {
            "student_id": student_id,
            "new_xp": new_xp,
            "xp_earned": xp_earned,
            "level": lvl_info["level"],
            "title": lvl_info["title"],
        }
    finally:
        connection.close()


def update_student_streak(student_id: int, db_path: str = None) -> dict:
    """
    Updates the student's learning streak based on their last activity date.
    Awards daily streak bonus XP when applicable.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT streak, last_active_date, xp FROM student_gamification WHERE student_id = ?;",
            (student_id,)
        )
        row = cursor.fetchone()
        today = date.today()
        today_str = today.isoformat()
        yesterday_str = (today - timedelta(days=1)).isoformat()

        bonus_xp = 0
        streak = 1

        if not row:
            bonus_xp = 15
            lvl = calculate_level_info(15)["level"]
            cursor.execute(
                """
                INSERT INTO student_gamification (student_id, xp, streak, last_active_date, level)
                VALUES (?, 15, 1, ?, ?);
                """,
                (student_id, today_str, lvl),
            )
        else:
            current_streak = row["streak"] or 1
            last_active = row["last_active_date"]

            if last_active == today_str:
                streak = current_streak
            elif last_active == yesterday_str:
                streak = current_streak + 1
                bonus_xp = 15
                new_xp = (row["xp"] or 0) + bonus_xp
                lvl = calculate_level_info(new_xp)["level"]
                cursor.execute(
                    """
                    UPDATE student_gamification
                    SET streak = ?, last_active_date = ?, xp = ?, level = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE student_id = ?;
                    """,
                    (streak, today_str, new_xp, lvl, student_id),
                )
            else:
                streak = 1
                bonus_xp = 10
                new_xp = (row["xp"] or 0) + bonus_xp
                lvl = calculate_level_info(new_xp)["level"]
                cursor.execute(
                    """
                    UPDATE student_gamification
                    SET streak = 1, last_active_date = ?, xp = ?, level = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE student_id = ?;
                    """,
                    (today_str, new_xp, lvl, student_id),
                )

        if bonus_xp > 0:
            cursor.execute(
                """
                INSERT INTO xp_activities (user_id, activity_type, xp_earned, description)
                VALUES (?, 'streak_checkin', ?, ?);
                """,
                (student_id, bonus_xp, f"Daily streak check-in (Streak: {streak} days)"),
            )

        connection.commit()
        return {"streak": streak, "bonus_xp": bonus_xp, "active_today": True}
    finally:
        connection.close()


def evaluate_and_award_badges(student_id: int, db_path: str = None) -> list:
    """
    Evaluates milestone badge criteria for a student.
    Awards any newly unlocked badges and bonus XP.
    Returns list of newly awarded badge dictionaries.
    """
    connection = get_connection(db_path)
    newly_awarded = []
    try:
        cursor = connection.cursor()

        # Existing awarded badge IDs
        cursor.execute(
            "SELECT badge_id FROM user_badges WHERE user_id = ?;",
            (student_id,)
        )
        existing_badge_ids = {r["badge_id"] for r in cursor.fetchall()}

        # Student skill scores
        cursor.execute(
            """
            SELECT s.name as skill_name, ss.score
            FROM student_skills ss
            JOIN skills s ON ss.skill_id = s.id
            WHERE ss.student_id = ?;
            """,
            (student_id,)
        )
        skills_map = {r["skill_name"]: r["score"] for r in cursor.fetchall()}

        # Application count
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM applications WHERE student_id = ?;",
            (student_id,)
        )
        app_count = cursor.fetchone()["cnt"]

        # Gamification stats
        cursor.execute(
            "SELECT streak, xp FROM student_gamification WHERE student_id = ?;",
            (student_id,)
        )
        g_row = cursor.fetchone()
        streak = g_row["streak"] if g_row else 1
        xp = g_row["xp"] if g_row else 0

        badges_to_award = []

        # Criteria 1: First Step (completed at least 1 assessment)
        if len(skills_map) >= 1 and "first_step" not in existing_badge_ids:
            badges_to_award.append("first_step")

        # Criteria 2: High scores on individual domains (>= 80%)
        if skills_map.get("Python", 0) >= 80 and "python_pro" not in existing_badge_ids:
            badges_to_award.append("python_pro")
        if skills_map.get("Java", 0) >= 80 and "java_champ" not in existing_badge_ids:
            badges_to_award.append("java_champ")
        if skills_map.get("Web Development", 0) >= 80 and "web_architect" not in existing_badge_ids:
            badges_to_award.append("web_architect")
        if skills_map.get("Data Structures", 0) >= 80 and "algo_ace" not in existing_badge_ids:
            badges_to_award.append("algo_ace")

        # Criteria 3: Skill All-Rounder (completed all 4 foundational skills)
        core_skills = {"Python", "Java", "Web Development", "Data Structures"}
        if core_skills.issubset(skills_map.keys()) and "skill_master" not in existing_badge_ids:
            badges_to_award.append("skill_master")

        # Criteria 4: Opportunity Hunter (applied to at least 1 opportunity)
        if app_count >= 1 and "first_app" not in existing_badge_ids:
            badges_to_award.append("first_app")

        # Criteria 5: Streaks (3-day and 7-day)
        if streak >= 3 and "streak_3" not in existing_badge_ids:
            badges_to_award.append("streak_3")
        if streak >= 7 and "streak_7" not in existing_badge_ids:
            badges_to_award.append("streak_7")

        # Criteria 6: Screening Star (passed at least 1 company screening test)
        cursor.execute("SELECT COUNT(*) as cnt FROM screening_attempts WHERE student_id = ? AND passed = 1;", (student_id,))
        scr_passed = cursor.fetchone()["cnt"]
        if scr_passed >= 1 and "screening_star" not in existing_badge_ids:
            badges_to_award.append("screening_star")

        for b_id in badges_to_award:
            cursor.execute("SELECT * FROM badges WHERE id = ?;", (b_id,))
            b_info = cursor.fetchone()
            if b_info:
                cursor.execute(
                    "INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?);",
                    (student_id, b_id)
                )
                xp_bonus = b_info["xp_bonus"]
                cursor.execute(
                    """
                    INSERT INTO xp_activities (user_id, activity_type, xp_earned, description)
                    VALUES (?, 'badge_unlocked', ?, ?);
                    """,
                    (student_id, xp_bonus, f"Unlocked Badge: {b_info['name']}"),
                )
                new_xp = xp + xp_bonus
                lvl = calculate_level_info(new_xp)["level"]
                cursor.execute(
                    """
                    UPDATE student_gamification
                    SET xp = ?, level = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE student_id = ?;
                    """,
                    (new_xp, lvl, student_id)
                )
                xp = new_xp
                newly_awarded.append(dict(b_info))

        connection.commit()
        return newly_awarded
    finally:
        connection.close()


def get_student_gamification_profile(student_id: int, db_path: str = None) -> dict:
    """
    Returns full gamification state for a student: XP, level, streak,
    all badges (with unlocked state), and recent activity feed.
    """
    get_or_create_student_gamification(student_id, db_path)
    evaluate_and_award_badges(student_id, db_path)

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM student_gamification WHERE student_id = ?;", (student_id,))
        g_row = dict(cursor.fetchone())

        level_info = calculate_level_info(g_row["xp"])

        # Badges list with unlocked status
        cursor.execute(
            """
            SELECT b.id, b.name, b.description, b.icon, b.category, b.xp_bonus, ub.awarded_at
            FROM badges b
            LEFT JOIN user_badges ub ON b.id = ub.badge_id AND ub.user_id = ?
            ORDER BY ub.awarded_at DESC NULLS LAST, b.id;
            """,
            (student_id,)
        )
        badges = []
        for b in cursor.fetchall():
            bd = dict(b)
            bd["is_unlocked"] = bd["awarded_at"] is not None
            badges.append(bd)

        # Recent activities
        cursor.execute(
            """
            SELECT activity_type, xp_earned, description, created_at
            FROM xp_activities
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 8;
            """,
            (student_id,)
        )
        activities = [dict(a) for a in cursor.fetchall()]

        # Leaderboard rank
        cursor.execute(
            """
            SELECT COUNT(*) + 1 as rank
            FROM student_gamification
            WHERE xp > ?;
            """,
            (g_row["xp"],)
        )
        rank_row = cursor.fetchone()
        rank = rank_row["rank"] if rank_row else 1

        cursor.execute("SELECT COUNT(*) as total FROM student_gamification;")
        total_students = cursor.fetchone()["total"]

        return {
            "xp": g_row["xp"],
            "level": level_info["level"],
            "level_title": level_info["title"],
            "current_threshold": level_info["current_threshold"],
            "next_threshold": level_info["next_threshold"],
            "xp_to_next": level_info["xp_to_next"],
            "progress_percentage": level_info["progress_percentage"],
            "streak": g_row["streak"],
            "last_active_date": g_row["last_active_date"],
            "active_today": g_row["last_active_date"] == date.today().isoformat(),
            "rank": rank,
            "total_students": max(total_students, 1),
            "badges": badges,
            "unlocked_badges_count": sum(1 for b in badges if b["is_unlocked"]),
            "total_badges_count": len(badges),
            "recent_activities": activities,
        }
    finally:
        connection.close()


def get_leaderboard_data(current_student_id: int = None, limit: int = 20, db_path: str = None) -> dict:
    """
    Returns ranked student leaderboard with podium (Top 3) and current user ranking.
    """
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                u.id as student_id,
                u.name,
                u.email,
                COALESCE(g.xp, 0) as xp,
                COALESCE(g.streak, 1) as streak,
                COALESCE(g.level, 1) as level,
                (SELECT COUNT(*) FROM user_badges WHERE user_id = u.id) as badges_count
            FROM users u
            LEFT JOIN student_gamification g ON u.id = g.student_id
            WHERE u.role = 'student'
            ORDER BY COALESCE(g.xp, 0) DESC, COALESCE(g.streak, 1) DESC, u.name ASC
            LIMIT ?;
            """,
            (limit,)
        )
        rows = cursor.fetchall()

        leaderboard = []
        for rank, r in enumerate(rows, start=1):
            s_dict = dict(r)
            s_dict["rank"] = rank
            lvl_info = calculate_level_info(s_dict["xp"])
            s_dict["level_title"] = lvl_info["title"]

            cursor.execute(
                """
                SELECT s.name, ss.score
                FROM student_skills ss
                JOIN skills s ON ss.skill_id = s.id
                WHERE ss.student_id = ?
                ORDER BY ss.score DESC
                LIMIT 1;
                """,
                (s_dict["student_id"],)
            )
            top_skill = cursor.fetchone()
            s_dict["top_skill"] = top_skill["name"] if top_skill else "Foundations"
            s_dict["top_skill_score"] = top_skill["score"] if top_skill else 0
            leaderboard.append(s_dict)

        podium = leaderboard[:3]

        current_user_rank = None
        if current_student_id:
            for entry in leaderboard:
                if entry["student_id"] == current_student_id:
                    current_user_rank = entry
                    break

            if not current_user_rank:
                cursor.execute(
                    """
                    SELECT COUNT(*) + 1 as rank, COALESCE(g.xp, 0) as xp, COALESCE(g.streak, 1) as streak
                    FROM users u
                    LEFT JOIN student_gamification g ON u.id = g.student_id
                    WHERE u.role = 'student' AND (
                        COALESCE(g.xp, 0) > (SELECT COALESCE(xp, 0) FROM student_gamification WHERE student_id = ?)
                    );
                    """,
                    (current_student_id,)
                )
                cr = cursor.fetchone()
                cursor.execute("SELECT name FROM users WHERE id = ?;", (current_student_id,))
                u_row = cursor.fetchone()
                if u_row:
                    current_user_rank = {
                        "student_id": current_student_id,
                        "name": u_row["name"],
                        "rank": cr["rank"] if cr else len(leaderboard) + 1,
                        "xp": cr["xp"] if cr else 0,
                        "streak": cr["streak"] if cr else 1,
                    }

        return {
            "podium": podium,
            "leaderboard": leaderboard,
            "total_participants": len(leaderboard),
            "current_user_rank": current_user_rank,
        }
    finally:
        connection.close()


def get_all_badges(db_path: str = None) -> list:
    """Returns all badges in the catalog."""
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM badges ORDER BY id;")
        return [dict(r) for r in cursor.fetchall()]
    finally:
        connection.close()


def seed_demo_leaderboard_data(db_path: str = None):
    """
    Seeds realistic cohort students, skill scores, streaks, XP, and badges
    to ensure the leaderboard is vibrant and presentation-ready for SIH judges.
    """
    from backend.auth import hash_password
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()

        demo_students = [
            {
                "name": "Aarav Sharma",
                "email": "aarav.sharma@skillbridge.demo",
                "xp": 1150,
                "streak": 7,
                "skills": {"Python": 95, "Data Structures": 92, "Java": 85, "Web Development": 88},
                "badges": ["first_step", "python_pro", "java_champ", "web_architect", "algo_ace", "skill_master", "streak_3", "streak_7", "top_tier"],
            },
            {
                "name": "Priya Patel",
                "email": "priya.patel@skillbridge.demo",
                "xp": 820,
                "streak": 5,
                "skills": {"Data Structures": 90, "Web Development": 86, "Python": 78, "Java": 82},
                "badges": ["first_step", "algo_ace", "web_architect", "java_champ", "streak_3", "first_app", "top_tier"],
            },
            {
                "name": "Rohan Mehta",
                "email": "rohan.mehta@skillbridge.demo",
                "xp": 640,
                "streak": 4,
                "skills": {"Web Development": 92, "Python": 84, "Data Structures": 72},
                "badges": ["first_step", "web_architect", "python_pro", "streak_3", "first_app", "top_tier"],
            },
            {
                "name": "Sneha Reddy",
                "email": "sneha.reddy@skillbridge.demo",
                "xp": 430,
                "streak": 3,
                "skills": {"Java": 88, "Python": 80, "Web Development": 70},
                "badges": ["first_step", "java_champ", "python_pro", "streak_3"],
            },
            {
                "name": "Vikram Iyer",
                "email": "vikram.iyer@skillbridge.demo",
                "xp": 260,
                "streak": 2,
                "skills": {"Python": 82, "Data Structures": 76},
                "badges": ["first_step", "python_pro"],
            },
        ]

        dummy_pw = hash_password("DemoStudent123!")
        today_str = date.today().isoformat()

        # Skill id lookup
        cursor.execute("SELECT id, name FROM skills;")
        skill_ids = {r["name"]: r["id"] for r in cursor.fetchall()}

        for s in demo_students:
            cursor.execute("SELECT id FROM users WHERE email = ?;", (s["email"],))
            user_row = cursor.fetchone()
            if not user_row:
                cursor.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role)
                    VALUES (?, ?, ?, 'student');
                    """,
                    (s["name"], s["email"], dummy_pw),
                )
                student_id = cursor.lastrowid
            else:
                student_id = user_row["id"]

            lvl_info = calculate_level_info(s["xp"])
            cursor.execute(
                """
                INSERT INTO student_gamification (student_id, xp, streak, last_active_date, level)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    xp = excluded.xp,
                    streak = excluded.streak,
                    level = excluded.level;
                """,
                (student_id, s["xp"], s["streak"], today_str, lvl_info["level"]),
            )

            for sk_name, score in s["skills"].items():
                if sk_name in skill_ids:
                    save_or_update_student_skill(student_id, skill_ids[sk_name], score, db_path)

            for b_id in s["badges"]:
                cursor.execute(
                    """
                    INSERT INTO user_badges (user_id, badge_id)
                    VALUES (?, ?)
                    ON CONFLICT(user_id, badge_id) DO NOTHING;
                    """,
                    (student_id, b_id),
                )

        connection.commit()
    finally:
        connection.close()

# =========================================================
# INDUSTRY SCREENING TESTS & CANDIDATE EVALUATION
# =========================================================

def create_or_update_screening_test(
    opportunity_id: int,
    title: str,
    description: str = "",
    passing_score: int = 60,
    questions: list = None,
    db_path: str = None
) -> dict:
    clean_title = title.strip()
    clean_desc = (description or "").strip()
    passing_score = max(10, min(100, int(passing_score)))
    questions = questions or []

    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM opportunities WHERE id = ?;", (opportunity_id,))
        if not cursor.fetchone():
            raise ValueError(f"Opportunity #{opportunity_id} not found.")

        cursor.execute("SELECT id FROM screening_tests WHERE opportunity_id = ?;", (opportunity_id,))
        existing = cursor.fetchone()
        if existing:
            test_id = existing["id"]
            cursor.execute("""
                UPDATE screening_tests
                SET title = ?, description = ?, passing_score = ?
                WHERE id = ?;
            """, (clean_title, clean_desc, passing_score, test_id))
            cursor.execute("DELETE FROM screening_questions WHERE test_id = ?;", (test_id,))
        else:
            cursor.execute("""
                INSERT INTO screening_tests (opportunity_id, title, description, passing_score)
                VALUES (?, ?, ?, ?);
            """, (opportunity_id, clean_title, clean_desc, passing_score))
            test_id = cursor.lastrowid

        saved_questions = []
        for q in questions:
            q_text = q.get("question_text", "").strip()
            opts = q.get("options", [])
            correct_idx = int(q.get("correct_option", 0))
            if not q_text or len(opts) < 2:
                continue
            cursor.execute("""
                INSERT INTO screening_questions (test_id, question_text, options_json, correct_option)
                VALUES (?, ?, ?, ?);
            """, (test_id, q_text, json.dumps(opts), correct_idx))
            saved_questions.append({
                "id": cursor.lastrowid,
                "question_text": q_text,
                "options": opts,
                "correct_option": correct_idx
            })

        connection.commit()
        return {
            "id": test_id,
            "opportunity_id": opportunity_id,
            "title": clean_title,
            "description": clean_desc,
            "passing_score": passing_score,
            "questions": saved_questions
        }
    finally:
        connection.close()


def get_screening_test_by_opportunity(
    opportunity_id: int,
    include_answers: bool = False,
    db_path: str = None
) -> dict:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, opportunity_id, title, description, passing_score, created_at
            FROM screening_tests
            WHERE opportunity_id = ?;
        """, (opportunity_id,))
        test_row = cursor.fetchone()
        if not test_row:
            return None

        test_data = dict(test_row)
        cursor.execute("""
            SELECT id, question_text, options_json, correct_option
            FROM screening_questions
            WHERE test_id = ?
            ORDER BY id ASC;
        """, (test_data["id"],))
        q_rows = cursor.fetchall()
        questions = []
        for row in q_rows:
            q_dict = {
                "id": row["id"],
                "question_text": row["question_text"],
                "options": json.loads(row["options_json"])
            }
            if include_answers:
                q_dict["correct_option"] = row["correct_option"]
            questions.append(q_dict)

        test_data["questions"] = questions
        return test_data
    finally:
        connection.close()


def get_screening_test_by_id(
    test_id: int,
    include_answers: bool = False,
    db_path: str = None
) -> dict:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, opportunity_id, title, description, passing_score, created_at
            FROM screening_tests
            WHERE id = ?;
        """, (test_id,))
        test_row = cursor.fetchone()
        if not test_row:
            return None

        test_data = dict(test_row)
        cursor.execute("""
            SELECT id, question_text, options_json, correct_option
            FROM screening_questions
            WHERE test_id = ?
            ORDER BY id ASC;
        """, (test_id,))
        q_rows = cursor.fetchall()
        questions = []
        for row in q_rows:
            q_dict = {
                "id": row["id"],
                "question_text": row["question_text"],
                "options": json.loads(row["options_json"])
            }
            if include_answers:
                q_dict["correct_option"] = row["correct_option"]
            questions.append(q_dict)

        test_data["questions"] = questions
        return test_data
    finally:
        connection.close()


def record_screening_attempt(
    test_id: int,
    student_id: int,
    answers: dict,
    db_path: str = None
) -> dict:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, opportunity_id, title, passing_score
            FROM screening_tests
            WHERE id = ?;
        """, (test_id,))
        test_row = cursor.fetchone()
        if not test_row:
            raise ValueError(f"Screening test #{test_id} not found.")

        opp_id = test_row["opportunity_id"]
        passing_score = test_row["passing_score"]

        cursor.execute("""
            SELECT id, correct_option
            FROM screening_questions
            WHERE test_id = ?;
        """, (test_id,))
        questions = cursor.fetchall()
        if not questions:
            raise ValueError("This screening test has no questions configured.")

        total_questions = len(questions)
        correct_count = 0
        for q in questions:
            qid_str = str(q["id"])
            if qid_str in answers and int(answers[qid_str]) == q["correct_option"]:
                correct_count += 1

        score = round((correct_count / total_questions) * 100)
        passed = score >= passing_score

        cursor.execute("""
            INSERT INTO screening_attempts
            (test_id, student_id, opportunity_id, score, passed, answers_json, attempted_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id, test_id) DO UPDATE SET
                score = excluded.score,
                passed = excluded.passed,
                answers_json = excluded.answers_json,
                attempted_at = CURRENT_TIMESTAMP;
        """, (test_id, student_id, opp_id, score, 1 if passed else 0, json.dumps(answers)))

        if passed:
            cursor.execute("""
                UPDATE applications
                SET status = 'shortlisted'
                WHERE student_id = ? AND opportunity_id = ? AND status = 'applied';
            """, (student_id, opp_id))

        connection.commit()
    finally:
        connection.close()

    xp_bonus = 50 if passed else 25
    desc = f"Completed screening test for '{test_row['title']}' (Score: {score}%, {'Passed' if passed else 'Needs Practice'})"
    new_badges = []
    try:
        record_xp_activity(student_id, "Screening Test", xp_bonus, desc, db_path=db_path)
        update_student_streak(student_id, db_path=db_path)
        new_badges = evaluate_and_award_badges(student_id, db_path=db_path) or []
    except Exception:
        pass

    badge_ids = [b["id"] if isinstance(b, dict) else str(b) for b in new_badges]

    return {
        "test_id": test_id,
        "opportunity_id": opp_id,
        "score": score,
        "passed": passed,
        "passing_score": passing_score,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "xp_earned": xp_bonus,
        "xp_awarded": xp_bonus,
        "new_badges": badge_ids,
        "unlocked_badges": new_badges,
        "message": "Congratulations! You passed the company screening test!" if passed else f"You scored {score}%. Passing score is {passing_score}%."
    }


def get_student_screening_attempt(
    student_id: int,
    test_id: int,
    db_path: str = None
) -> dict:
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, test_id, student_id, opportunity_id, score, passed, attempted_at
            FROM screening_attempts
            WHERE student_id = ? AND test_id = ?;
        """, (student_id, test_id))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["passed"] = bool(res["passed"])
        return res
    finally:
        connection.close()


def seed_demo_screening_test(db_path: str = None):
    connection = get_connection(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, title FROM opportunities ORDER BY id ASC LIMIT 1;")
        row = cursor.fetchone()
        if not row:
            return
        opp_id = row["id"]
        cursor.execute("SELECT id FROM screening_tests WHERE opportunity_id = ?;", (opp_id,))
        if cursor.fetchone():
            return

        create_or_update_screening_test(
            opportunity_id=opp_id,
            title=f"{row['title']} — Technical Screening",
            description="Official company screening test covering core architecture, web communication, and algorithms.",
            passing_score=60,
            questions=[
                {
                    "question_text": "What is the primary difference between a process and a thread in Python?",
                    "options": [
                        "Threads share memory space while processes have separate memory",
                        "Processes cannot run concurrently",
                        "Threads bypass the Global Interpreter Lock (GIL) completely",
                        "Processes always share identical memory space"
                    ],
                    "correct_option": 0
                },
                {
                    "question_text": "Which HTTP status code signifies that a resource was successfully created on the server?",
                    "options": [
                        "200 OK",
                        "201 Created",
                        "204 No Content",
                        "301 Moved Permanently"
                    ],
                    "correct_option": 1
                },
                {
                    "question_text": "What does a B-Tree indexing operation in SQLite primarily optimize?",
                    "options": [
                        "Write speed during batch inserts",
                        "Query search and filtering speed at the expense of slight write overhead",
                        "Database compression ratio on disk",
                        "Automatic schema migration compatibility"
                    ],
                    "correct_option": 1
                },
                {
                    "question_text": "Which data structure provides O(1) average-time complexity for key-based lookups?",
                    "options": [
                        "Linked List",
                        "Binary Search Tree",
                        "Hash Map / Dictionary",
                        "Array List"
                    ],
                    "correct_option": 2
                }
            ],
            db_path=db_path
        )
    finally:
        connection.close()
