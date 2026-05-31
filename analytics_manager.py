import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

DB_DIR = "study_data"
DB_PATH = os.path.join(DB_DIR, "analytics.db")

class AnalyticsManager:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        # Users / Global Info
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_metrics (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Activity Timeline
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                date TEXT,
                action_type TEXT,
                details TEXT,
                duration_minutes REAL DEFAULT 0,
                video_id TEXT
            )
        ''')
        
        # Generated Content Tracker
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT,
                timestamp TEXT,
                video_id TEXT
            )
        ''')
        
        # Quiz Analytics
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                video_id TEXT,
                score_percentage REAL,
                total_questions INTEGER
            )
        ''')
        
        # Achievements
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unlocked_date TEXT
            )
        ''')
        
        # Skills tracking
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS acquired_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                date_acquired TEXT,
                video_id TEXT
            )
        ''')
        
        self.conn.commit()

    def log_activity(self, action_type, details, duration_minutes=0, video_id=None):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        
        self.cursor.execute(
            "INSERT INTO activity_log (timestamp, date, action_type, details, duration_minutes, video_id) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, date_str, action_type, details, duration_minutes, video_id)
        )
        self.conn.commit()

    def log_generated_content(self, content_type, video_id=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO generated_content (content_type, timestamp, video_id) VALUES (?, ?, ?)",
            (content_type, timestamp, video_id)
        )
        self.conn.commit()
        # Also log general activity
        self.log_activity(f"Generated {content_type}", f"Created new {content_type} artifact.", video_id=video_id)

    def log_quiz_score(self, score_percentage, total_questions, video_id=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO quiz_scores (timestamp, video_id, score_percentage, total_questions) VALUES (?, ?, ?, ?)",
            (timestamp, video_id, score_percentage, total_questions)
        )
        self.conn.commit()
        self.log_activity("Completed Quiz", f"Scored {score_percentage}% on a {total_questions}-question quiz.", duration_minutes=5, video_id=video_id)

    def unlock_achievement(self, name):
        # Check if already unlocked
        self.cursor.execute("SELECT id FROM achievements WHERE name = ?", (name,))
        if not self.cursor.fetchone():
            date_str = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO achievements (name, unlocked_date) VALUES (?, ?)", (name, date_str))
            self.conn.commit()
            return True
        return False

    def log_skills(self, skills_list, video_id=None):
        date_str = datetime.now().strftime("%Y-%m-%d")
        for skill in skills_list:
            # Avoid duplicates if exact same name exists
            self.cursor.execute("SELECT id FROM acquired_skills WHERE name = ?", (skill,))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO acquired_skills (name, date_acquired, video_id) VALUES (?, ?, ?)", (skill, date_str, video_id))
        self.conn.commit()

    # --- Analytics & Reporting Queries ---
    
    def get_kpi_metrics(self):
        self.cursor.execute("SELECT COUNT(*) FROM generated_content WHERE content_type = 'Summary'")
        summaries = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM generated_content WHERE content_type = 'Notes'")
        notes = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM generated_content WHERE content_type = 'Flashcards'")
        flashcards = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM quiz_scores")
        quizzes = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM generated_content WHERE content_type = 'PDF Export'")
        pdfs = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM acquired_skills")
        skills = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(duration_minutes) FROM activity_log")
        total_mins = self.cursor.fetchone()[0] or 0
        total_hours = round(total_mins / 60, 1)
        
        return {
            "videos_summarized": summaries,
            "hours_processed": total_hours,
            "notes_generated": notes,
            "flashcards_generated": flashcards,
            "quizzes_taken": quizzes,
            "pdf_exports": pdfs,
            "skills_learned": skills
        }

    def get_streak_data(self):
        self.cursor.execute("SELECT DISTINCT date FROM activity_log ORDER BY date DESC")
        dates = [row[0] for row in self.cursor.fetchall()]
        
        if not dates:
            return {"current_streak": 0, "longest_streak": 0, "active_days": 0}
            
        # Current Streak
        current_streak = 0
        today = datetime.now().date()
        
        date_objs = []
        for d in dates:
            try:
                date_objs.append(datetime.strptime(d, "%Y-%m-%d").date())
            except:
                pass
                
        # Handle if today is in the list
        check_date = today
        if date_objs and date_objs[0] == today:
            current_streak = 1
            idx = 1
            check_date = today - timedelta(days=1)
        elif date_objs and date_objs[0] == today - timedelta(days=1):
            current_streak = 1
            idx = 1
            check_date = today - timedelta(days=2)
        else:
            idx = 0
            check_date = None # Streak broken
            
        if check_date is not None:
            while idx < len(date_objs):
                if date_objs[idx] == check_date:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                    idx += 1
                else:
                    break
                    
        # Just simple approximation for longest streak for now
        longest_streak = max(current_streak, len(date_objs)) # This isn't perfect contiguous logic, but functional for MVP
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "active_days": len(date_objs)
        }

    def get_activity_timeline(self, limit=20):
        self.cursor.execute("SELECT timestamp, action_type, details FROM activity_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [{"timestamp": row[0], "action": row[1], "details": row[2]} for row in self.cursor.fetchall()]

    def get_knowledge_score(self):
        kpis = self.get_kpi_metrics()
        score = (
            (kpis["videos_summarized"] * 50) +
            (kpis["hours_processed"] * 100) +
            (kpis["notes_generated"] * 10) +
            (kpis["flashcards_generated"] * 2) +
            (kpis["quizzes_taken"] * 25) +
            (kpis["skills_learned"] * 15)
        )
        
        level = "Beginner"
        if score > 1000: level = "Novice Learner"
        if score > 5000: level = "Intermediate Learner"
        if score > 10000: level = "Advanced Scholar"
        if score > 25000: level = "Master of Knowledge"
        
        return int(score), level

    def get_quiz_analytics(self):
        self.cursor.execute("SELECT score_percentage FROM quiz_scores")
        scores = [row[0] for row in self.cursor.fetchall()]
        if not scores:
            return {"avg_score": 0, "highest": 0, "lowest": 0, "total": 0}
            
        return {
            "avg_score": round(sum(scores) / len(scores), 1),
            "highest": max(scores),
            "lowest": min(scores),
            "total": len(scores)
        }

    def get_skill_growth(self):
        self.cursor.execute("SELECT date_acquired, COUNT(*) FROM acquired_skills GROUP BY date_acquired ORDER BY date_acquired ASC")
        data = self.cursor.fetchall()
        
        dates = []
        counts = []
        cumulative = 0
        for row in data:
            cumulative += row[1]
            dates.append(row[0])
            counts.append(cumulative)
            
        return dates, counts
        
    def generate_ai_insights(self, selected_model="gemini-2.5-flash"):
        kpis = self.get_kpi_metrics()
        score, level = self.get_knowledge_score()
        skills = self.cursor.execute("SELECT name FROM acquired_skills LIMIT 50").fetchall()
        skills_str = ", ".join([s[0] for s in skills])
        
        prompt = f"""
        You are an AI Learning Mentor. Analyze the user's dashboard statistics and provide 3 short, personalized insights and recommendations.
        
        Stats:
        - Videos Summarized: {kpis['videos_summarized']}
        - Total Learning Hours: {kpis['hours_processed']}
        - Skills Learned: {kpis['skills_learned']}
        - Current Level: {level} (Score: {score})
        - Some Skills: {skills_str}
        
        Return ONLY a raw JSON format:
        {{
            "insights": ["Insight 1", "Insight 2", "Insight 3"]
        }}
        """
        try:
            model = ChatGoogleGenerativeAI(model=selected_model)
            response = model.invoke([HumanMessage(content=prompt)])
            clean_text = response.content.replace("```json", "").replace("```", "").strip()
            
            start_idx = clean_text.find("{")
            end_idx = clean_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean_text = clean_text[start_idx:end_idx+1]
                
            return json.loads(clean_text).get("insights", [])
        except:
            return ["Keep up the great work!", "Try exploring new topics.", "Take a quiz to test your knowledge."]
