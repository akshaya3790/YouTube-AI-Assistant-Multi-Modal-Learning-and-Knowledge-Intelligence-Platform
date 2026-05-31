import os
import json

STORAGE_DIR = "study_data"
MULTI_VIDEO_DIR = os.path.join(STORAGE_DIR, "multi_video")

class MultiVideoStorage:
    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        os.makedirs(MULTI_VIDEO_DIR, exist_ok=True)

    def save_session(self, session_id, report_data):
        filepath = os.path.join(MULTI_VIDEO_DIR, f"{session_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving multi-video session: {e}")
            return False

    def load_session(self, session_id):
        filepath = os.path.join(MULTI_VIDEO_DIR, f"{session_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading multi-video session: {e}")
            return None

    def get_all_sessions(self):
        sessions = []
        if not os.path.exists(MULTI_VIDEO_DIR):
            return sessions
            
        for filename in os.listdir(MULTI_VIDEO_DIR):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                sessions.append(session_id)
        return sessions

    def delete_session(self, session_id):
        filepath = os.path.join(MULTI_VIDEO_DIR, f"{session_id}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")
                return False
        return False
