import os
import json
from datetime import datetime

class StudyStorage:
    def __init__(self, directory="study_data"):
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            
    def get_flashcard_path(self, video_id):
        # Sanitize video_id for filenames
        safe_id = "".join([c for c in video_id if c.isalnum() or c in ("-", "_")])
        return os.path.join(self.directory, f"flashcards_{safe_id}.json")
        
    def save_flashcards(self, video_id, cards_list):
        path = self.get_flashcard_path(video_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cards_list, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving flashcards: {e}")
            return False
            
    def load_flashcards(self, video_id):
        path = self.get_flashcard_path(video_id)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading flashcards: {e}")
            return []

    def get_user_profile_path(self):
        return os.path.join(self.directory, "user_profile.json")

    def save_user_profile(self, profile):
        path = self.get_user_profile_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False

    def load_user_profile(self):
        path = self.get_user_profile_path()
        default_profile = {
            "xp": 0,
            "streak": 0,
            "last_active": None,
            "badges": []
        }
        if not os.path.exists(path):
            return default_profile
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all default keys exist
                for k, v in default_profile.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return default_profile

    def update_streak(self):
        """
        Updates the daily learning streak based on activity date comparison.
        """
        profile = self.load_user_profile()
        today = datetime.now().strftime("%Y-%m-%d")
        last_active = profile.get("last_active")
        
        if last_active is None:
            profile["streak"] = 1
            profile["last_active"] = today
        elif last_active == today:
            # Already active today, streak stays the same
            pass
        else:
            try:
                last_dt = datetime.strptime(last_active, "%Y-%m-%d")
                today_dt = datetime.strptime(today, "%Y-%m-%d")
                delta_days = (today_dt - last_dt).days
                
                if delta_days == 1:
                    profile["streak"] += 1
                elif delta_days > 1:
                    # Streak broken, reset
                    profile["streak"] = 1
                profile["last_active"] = today
            except:
                profile["streak"] = 1
                profile["last_active"] = today
                
        # Check streak achievements
        if profile["streak"] >= 7 and "7-Day Streak" not in profile["badges"]:
            profile["badges"].append("7-Day Streak")
            
        self.save_user_profile(profile)
        return profile["streak"]

    def add_xp(self, amount):
        """
        Adds XP points and checks badge thresholds.
        """
        profile = self.load_user_profile()
        profile["xp"] += amount
        
        # Check XP achievements
        if profile["xp"] >= 100 and "100 XP Milestone" not in profile["badges"]:
            profile["badges"].append("100 XP Milestone")
        if profile["xp"] >= 500 and "500 XP Quiz Master" not in profile["badges"]:
            profile["badges"].append("500 XP Quiz Master")
            
        self.save_user_profile(profile)
        return profile
