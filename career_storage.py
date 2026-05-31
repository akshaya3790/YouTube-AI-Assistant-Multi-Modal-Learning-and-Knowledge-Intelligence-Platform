import os
import json
from datetime import datetime

class CareerStorage:
    def __init__(self, directory="study_data"):
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            
    def get_report_path(self, video_id):
        # Sanitize video_id for filenames
        safe_id = "".join([c for c in video_id if c.isalnum() or c in ("-", "_")])
        return os.path.join(self.directory, f"career_report_{safe_id}.json")
        
    def save_career_report(self, video_id, report):
        path = self.get_report_path(video_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving career report: {e}")
            return False
            
    def load_career_report(self, video_id):
        path = self.get_report_path(video_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading career report: {e}")
            return None

    def get_portfolio_path(self):
        return os.path.join(self.directory, "career_portfolio.json")

    def save_portfolio(self, portfolio):
        path = self.get_portfolio_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(portfolio, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving career portfolio: {e}")
            return False

    def load_portfolio(self):
        path = self.get_portfolio_path()
        default_portfolio = {
            "videos_processed": 0,
            "total_skills": 0,
            "total_technologies": 0,
            "total_frameworks": 0,
            "total_tools": 0,
            "total_hours": 0.0,
            "video_ids": [],
            "skill_history": [],
            "accumulated_skills": [],
            "accumulated_technologies": [],
            "accumulated_frameworks": [],
            "accumulated_tools": []
        }
        if not os.path.exists(path):
            return default_portfolio
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default_portfolio.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print(f"Error loading career portfolio: {e}")
            return default_portfolio

    def add_video_to_portfolio(self, video_id, title, duration_seconds, report):
        portfolio = self.load_portfolio()
        
        # If already added, we can check but still let it pass or update
        is_new = video_id not in portfolio["video_ids"]
        if is_new:
            portfolio["video_ids"].append(video_id)
            portfolio["total_hours"] += float(duration_seconds) / 3600.0
            
        # Parse items from report
        skills = [s["name"] for s in report.get("skills_learned", []) if "name" in s]
        techs = [t["name"] for t in report.get("technologies", []) if "name" in t]
        frameworks = [f["name"] for f in report.get("frameworks", []) if "name" in f]
        tools = [t["name"] for t in report.get("tools", []) if "name" in t]
        
        # Merge uniquely
        for item in skills:
            if item not in portfolio["accumulated_skills"]:
                portfolio["accumulated_skills"].append(item)
        for item in techs:
            if item not in portfolio["accumulated_technologies"]:
                portfolio["accumulated_technologies"].append(item)
        for item in frameworks:
            if item not in portfolio["accumulated_frameworks"]:
                portfolio["accumulated_frameworks"].append(item)
        for item in tools:
            if item not in portfolio["accumulated_tools"]:
                portfolio["accumulated_tools"].append(item)
                
        # History entry
        history_entry = {
            "video_id": video_id,
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "skills": skills,
            "duration": duration_seconds
        }
        
        # Avoid duplicate entries in history list for the same video_id
        portfolio["skill_history"] = [h for h in portfolio["skill_history"] if h["video_id"] != video_id]
        portfolio["skill_history"].append(history_entry)
        
        # Recalculate stats counts
        portfolio["videos_processed"] = len(portfolio["video_ids"])
        portfolio["total_skills"] = len(portfolio["accumulated_skills"])
        portfolio["total_technologies"] = len(portfolio["accumulated_technologies"])
        portfolio["total_frameworks"] = len(portfolio["accumulated_frameworks"])
        portfolio["total_tools"] = len(portfolio["accumulated_tools"])
        
        self.save_portfolio(portfolio)
        return portfolio
