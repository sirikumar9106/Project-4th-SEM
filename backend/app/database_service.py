# database_service.py

import os
import json
import psycopg2
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Dict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DatabaseService:
    def __init__(self):
        # Load .env from 2 levels up (backend/.env)
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(dotenv_path)

        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING") or os.getenv("DATABASE_URL")
        if not self.connection_string:
            print("⚠️ WARNING: SUPABASE_CONNECTION_STRING or DATABASE_URL is not set.")
            self.conn = None
        else:
            try:
                print("Trying to connect to PostgreSQL/Supabase...")
                self.conn = psycopg2.connect(self.connection_string)
                self.conn.autocommit = True
                self.init_db()
                print("✅ PostgreSQL/Supabase connected and initialized successfully.")
            except Exception as e:
                print(f"❌ PostgreSQL/Supabase connection failed: {e}")
                self.conn = None

    def init_db(self):
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cur:
                # Create users table
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """)
                # Create quiz_results table
                cur.execute("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id SERIAL PRIMARY KEY,
                    path VARCHAR(500) UNIQUE NOT NULL,
                    student_id VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    quiz_type VARCHAR(255) NOT NULL,
                    quiz_name VARCHAR(255) NOT NULL,
                    timestamp VARCHAR(255) NOT NULL,
                    performance_breakdown JSONB NOT NULL,
                    time_taken_seconds INTEGER,
                    scoring_summary JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_results_path ON quiz_results(path);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_quiz_results_student_id ON quiz_results(student_id);")
                print("✅ Database tables and indexes verified/created successfully.")
        except Exception as e:
            print(f"❌ Failed to initialize database tables: {e}")

    def create_user(self, username: str, email: str, password: str):
        if not self.conn:
            return {"status": "error", "message": "Database not connected."}
        try:
            with self.conn.cursor() as cur:
                # Check username
                cur.execute("SELECT username FROM users WHERE username = %s;", (username,))
                if cur.fetchone():
                    return {"status": "error", "message": "Username already exists."}
                # Check email
                cur.execute("SELECT email FROM users WHERE email = %s;", (email,))
                if cur.fetchone():
                    return {"status": "error", "message": "Email already registered."}
                
                hashed_password = pwd_context.hash(password)
                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s);",
                    (username, email, hashed_password)
                )
                return {"status": "success", "message": "User created successfully."}
        except Exception as e:
            print(f"Error creating user: {e}")
            return {"status": "error", "message": f"Could not create user: {str(e)}"}

    def authenticate_user(self, username: str, password: str):
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT username, email, password_hash FROM users WHERE username = %s;", (username,))
                row = cur.fetchone()
                if not row:
                    return False
                user = {"username": row[0], "email": row[1], "password_hash": row[2]}
                if not pwd_context.verify(password, user["password_hash"]):
                    return False
                return user
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def check_username_exists(self, username: str) -> bool:
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s;", (username,))
                return cur.fetchone() is not None
        except Exception as e:
            print(f"Error checking username: {e}")
            return False

    def check_email_exists(self, email: str) -> bool:
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE email = %s;", (email,))
                return cur.fetchone() is not None
        except Exception as e:
            print(f"Error checking email: {e}")
            return False

    def get_user_quiz_history_summary(self, username: str) -> dict:
        if not self.conn:
            return {'unique_unit_quizzes_attempted': 0}
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT quiz_name FROM quiz_results WHERE student_id = %s AND quiz_type = 'Unit-Quizzes';",
                    (username,)
                )
                rows = cur.fetchall()
                return {'unique_unit_quizzes_attempted': len(rows)}
        except Exception as e:
            print(f"Error getting quiz history summary: {e}")
            return {'unique_unit_quizzes_attempted': 0}

    def save_quiz_result(self, result_data: dict):
        if not self.conn:
            return {"status": "error", "message": "Database not connected."}

        student_id = result_data.get("student_id")
        subject = result_data.get("subject")
        quiz_type = result_data.get("quiz_type")
        quiz_name = result_data.get("quiz_name")
        timestamp = result_data.get("timestamp") or datetime.now().isoformat()
        performance = result_data.get("performance_breakdown")
        time_taken = result_data.get("time_taken_seconds", None)

        total_score = sum(q.get("marks_obtained", 0) for q in performance)
        max_score = sum(q.get("marks_possible", 0) for q in performance)
        correct_answers = sum(1 for q in performance if q.get("is_correct"))

        difficulty_counts = {}
        type_counts = {}
        topics = set()
        subtopics = set()

        for q in performance:
            difficulty = q.get("difficulty_level", "unknown")
            dtype = q.get("difficulty_type", "unknown")
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
            if q.get("topic_name"): topics.add(q["topic_name"])
            if q.get("subtopic_name"): subtopics.add(q["subtopic_name"])

        scoring_summary = {
            "total_score": total_score,
            "max_score": max_score,
            "correct_answers_count": correct_answers,
            "total_questions": len(performance),
            "difficulty_breakdown": difficulty_counts,
            "type_breakdown": type_counts,
            "topics_covered": list(topics),
            "subtopics_covered": list(subtopics)
        }

        path = f"{student_id}/{subject}/{'Grand-Quiz' if quiz_type == 'Grand-Quiz' else quiz_name}/{timestamp}"

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quiz_results 
                    (path, student_id, subject, quiz_type, quiz_name, timestamp, performance_breakdown, time_taken_seconds, scoring_summary) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        path, student_id, subject, quiz_type, quiz_name, timestamp,
                        json.dumps(performance), time_taken, json.dumps(scoring_summary)
                    )
                )
                return {"status": "success", "message": "Quiz result saved with structured path."}
        except Exception as e:
            print(f"Error saving quiz result: {e}")
            return {"status": "error", "message": f"Could not save quiz result: {str(e)}"}

    def get_full_quiz_history(self, username: str = None) -> List[Dict]:
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cur:
                if username:
                    cur.execute(
                        "SELECT path, student_id, subject, quiz_type, quiz_name, timestamp, performance_breakdown, time_taken_seconds, scoring_summary FROM quiz_results WHERE student_id = %s ORDER BY timestamp DESC;",
                        (username,)
                    )
                else:
                    cur.execute(
                        "SELECT path, student_id, subject, quiz_type, quiz_name, timestamp, performance_breakdown, time_taken_seconds, scoring_summary FROM quiz_results ORDER BY timestamp DESC;"
                    )
                rows = cur.fetchall()
                results = []
                for r in rows:
                    results.append({
                        "path": r[0],
                        "student_id": r[1],
                        "subject": r[2],
                        "quiz_type": r[3],
                        "quiz_name": r[4],
                        "timestamp": r[5],
                        "performance_breakdown": r[6] if isinstance(r[6], list) else json.loads(r[6]) if isinstance(r[6], str) else r[6],
                        "time_taken_seconds": r[7],
                        "scoring_summary": r[8] if isinstance(r[8], dict) else json.loads(r[8]) if isinstance(r[8], str) else r[8],
                    })
                return results
        except Exception as e:
            print(f"Error getting full quiz history: {e}")
            return []

    def get_full_quiz_history_for_unit(self, username: str, unit_name: str) -> List[Dict]:
        if not self.conn:
            return []
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT path, student_id, subject, quiz_type, quiz_name, timestamp, performance_breakdown, time_taken_seconds, scoring_summary FROM quiz_results WHERE student_id = %s AND quiz_name = %s ORDER BY timestamp DESC;",
                    (username, unit_name)
                )
                rows = cur.fetchall()
                results = []
                for r in rows:
                    results.append({
                        "path": r[0],
                        "student_id": r[1],
                        "subject": r[2],
                        "quiz_type": r[3],
                        "quiz_name": r[4],
                        "timestamp": r[5],
                        "performance_breakdown": r[6] if isinstance(r[6], list) else json.loads(r[6]) if isinstance(r[6], str) else r[6],
                        "time_taken_seconds": r[7],
                        "scoring_summary": r[8] if isinstance(r[8], dict) else json.loads(r[8]) if isinstance(r[8], str) else r[8],
                    })
                return results
        except Exception as e:
            print(f"Error getting quiz history for unit: {e}")
            return []
    
    def get_dashboard_analytics(self, username: str, time_period_days: int) -> Dict:
        """
        Fetches and aggregates user performance data for the dashboard view.
        Filters by a specific time period.
        """
        if not self.conn:
            return {}
        
        try:
            with self.conn.cursor() as cur:
                if time_period_days > 0:
                    start_date = datetime.now() - timedelta(days=time_period_days)
                    cur.execute(
                        "SELECT performance_breakdown FROM quiz_results WHERE student_id = %s AND timestamp >= %s;",
                        (username, start_date.isoformat())
                    )
                else:
                    cur.execute(
                        "SELECT performance_breakdown FROM quiz_results WHERE student_id = %s;",
                        (username,)
                    )
                rows = cur.fetchall()

                dashboard_data = {}
                levels = ["easy", "medium", "hard"]
                types = ["direct", "logical reasoning", "aptitude"]

                for level in levels:
                    dashboard_data[level] = {}
                    for type_ in types:
                        dashboard_data[level][type_] = {"total": 0, "correct": 0}

                for r in rows:
                    pb = r[0]
                    if isinstance(pb, str):
                        pb = json.loads(pb)
                    for question in pb:
                        level = question.get("difficulty_level", "unknown")
                        type_ = question.get("difficulty_type", "unknown")

                        if level in levels and type_ in types:
                            dashboard_data[level][type_]["total"] += 1
                            if question.get("is_correct"):
                                dashboard_data[level][type_]["correct"] += 1
                
                return dashboard_data
        except Exception as e:
            print(f"Error getting dashboard analytics: {e}")
            return {}

    def get_performance_data_for_dashboard(self, username: str, time_period_days: int) -> List[Dict]:
        """
        Fetches all quiz results for a user within a specific time period.
        If time_period_days is 0, it fetches all results.
        """
        if not self.conn:
            return []

        try:
            with self.conn.cursor() as cur:
                if time_period_days > 0:
                    start_date = datetime.now() - timedelta(days=time_period_days)
                    cur.execute(
                        "SELECT path, student_id, subject, quiz_type, quiz_name, timestamp, performance_breakdown, time_taken_seconds, scoring_summary FROM quiz_results WHERE student_id = %s AND timestamp >= %s;",
                        (username, start_date.isoformat())
                    )
                else:
                    cur.execute(
                        "SELECT path, student_id, subject, quiz_type, quiz_name, timestamp, performance_breakdown, time_taken_seconds, scoring_summary FROM quiz_results WHERE student_id = %s;",
                        (username,)
                    )
                rows = cur.fetchall()
                results = []
                for r in rows:
                    results.append({
                        "path": r[0],
                        "student_id": r[1],
                        "subject": r[2],
                        "quiz_type": r[3],
                        "quiz_name": r[4],
                        "timestamp": r[5],
                        "performance_breakdown": r[6] if isinstance(r[6], list) else json.loads(r[6]) if isinstance(r[6], str) else r[6],
                        "time_taken_seconds": r[7],
                        "scoring_summary": r[8] if isinstance(r[8], dict) else json.loads(r[8]) if isinstance(r[8], str) else r[8],
                    })
                return results
        except Exception as e:
            print(f"Error getting performance data for dashboard: {e}")
            return []
    
# Instantiate globally
database_service = DatabaseService()
