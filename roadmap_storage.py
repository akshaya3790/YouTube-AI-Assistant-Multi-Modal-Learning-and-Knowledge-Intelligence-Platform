import os
import json
import uuid

STORAGE_DIR = "study_data"
ROADMAPS_DIR = os.path.join(STORAGE_DIR, "roadmaps")

class RoadmapStorage:
    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        os.makedirs(ROADMAPS_DIR, exist_ok=True)

    def _get_file_path(self, video_id):
        return os.path.join(ROADMAPS_DIR, f"{video_id}_roadmap.json")

    def get_roadmap(self, video_id):
        file_path = self._get_file_path(video_id)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return None

    def save_roadmap(self, video_id, roadmap_data):
        # Initialize completion states if not present
        if "completed_topics" not in roadmap_data:
            roadmap_data["completed_topics"] = []
            
        file_path = self._get_file_path(video_id)
        with open(file_path, "w") as f:
            json.dump(roadmap_data, f, indent=4)
        return True

    def toggle_topic_completion(self, video_id, topic_name, is_completed):
        roadmap = self.get_roadmap(video_id)
        if not roadmap:
            return False
            
        completed_list = roadmap.get("completed_topics", [])
        
        if is_completed and topic_name not in completed_list:
            completed_list.append(topic_name)
        elif not is_completed and topic_name in completed_list:
            completed_list.remove(topic_name)
            
        roadmap["completed_topics"] = completed_list
        return self.save_roadmap(video_id, roadmap)

    def delete_roadmap(self, video_id):
        file_path = self._get_file_path(video_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
