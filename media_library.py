import os
import json
import uuid

STORAGE_DIR = "study_data"
MEDIA_LIBRARY_DIR = os.path.join(STORAGE_DIR, "media_library")

class MediaLibrary:
    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        os.makedirs(MEDIA_LIBRARY_DIR, exist_ok=True)
        
        self.uploads_dir = os.path.join(MEDIA_LIBRARY_DIR, "uploads")
        self.audio_dir = os.path.join(MEDIA_LIBRARY_DIR, "audio")
        self.transcripts_dir = os.path.join(MEDIA_LIBRARY_DIR, "transcripts")
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.transcripts_dir, exist_ok=True)
        
        self.manifest_file = os.path.join(MEDIA_LIBRARY_DIR, "manifest.json")
        self.ensure_manifest()

    def ensure_manifest(self):
        if not os.path.exists(self.manifest_file):
            with open(self.manifest_file, "w") as f:
                json.dump([], f)

    def load_manifest(self):
        try:
            with open(self.manifest_file, "r") as f:
                return json.load(f)
        except:
            return []

    def save_manifest(self, manifest):
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=4)

    def add_media(self, filename, filepath, file_type, metadata):
        manifest = self.load_manifest()
        media_id = str(uuid.uuid4())
        
        record = {
            "id": media_id,
            "filename": filename,
            "filepath": filepath,
            "file_type": file_type,
            "metadata": metadata,
            "transcript": None,
            "uploaded_at": str(os.path.getctime(filepath)) if os.path.exists(filepath) else None
        }
        manifest.append(record)
        self.save_manifest(manifest)
        return media_id

    def save_uploaded_file(self, file_id, file_name, file_bytes, is_video=True):
        print(f"FILE RECEIVED: {file_name}")
        ext = os.path.splitext(file_name)[1].lower()
        target_path = os.path.join(self.uploads_dir, f"{file_id}{ext}")
        
        with open(target_path, "wb") as f:
            f.write(file_bytes)
            
        print(f"FILE SAVED: {target_path}")
        
        manifest = self.load_manifest()
        record = {
            "id": file_id,
            "filename": file_name,
            "filepath": target_path,
            "file_type": "video" if is_video else "audio",
            "metadata": {},
            "transcript": None,
            "uploaded_at": str(os.path.getctime(target_path))
        }
        manifest.append(record)
        self.save_manifest(manifest)
        return target_path

    def save_transcript(self, file_id, text):
        manifest = self.load_manifest()
        for record in manifest:
            if record["id"] == file_id:
                target_path = os.path.join(self.transcripts_dir, f"{file_id}.txt")
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(text)
                record["transcript_path"] = target_path
                self.save_manifest(manifest)
                return target_path
        return None
        
    def get_file_info(self, file_id):
        manifest = self.load_manifest()
        for record in manifest:
            if record["id"] == file_id:
                return {
                    "is_video": record["file_type"] == "video",
                    "original_name": record["filename"],
                    "path": record["filepath"]
                }
        return None

    def update_transcript(self, media_id, transcript_text):
        manifest = self.load_manifest()
        for record in manifest:
            if record["id"] == media_id:
                record["transcript"] = transcript_text
                break
        self.save_manifest(manifest)

    def get_media(self, media_id):
        manifest = self.load_manifest()
        for record in manifest:
            if record["id"] == media_id:
                return record
        return None

    def delete_media(self, media_id):
        manifest = self.load_manifest()
        new_manifest = [r for r in manifest if r["id"] != media_id]
        if len(manifest) != len(new_manifest):
            self.save_manifest(new_manifest)
            return True
        return False
