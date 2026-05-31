import os
import json
import uuid
import datetime

MANIFEST_DIR = "study_data"
MANIFEST_FILE = os.path.join(MANIFEST_DIR, "exports_manifest.json")
EXPORTS_DIR = os.path.join(MANIFEST_DIR, "exports")

class ExportManager:
    def __init__(self):
        os.makedirs(MANIFEST_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        self.manifest_file = MANIFEST_FILE
        self.exports_dir = EXPORTS_DIR

    def load_manifest(self):
        if not os.path.exists(self.manifest_file):
            return []
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_manifest(self, manifest):
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)

    def add_export(self, filename, filepath, file_type, file_size_kb, video_title, sections):
        manifest = self.load_manifest()
        export_id = str(uuid.uuid4())
        record = {
            "id": export_id,
            "filename": filename,
            "filepath": filepath,
            "file_type": file_type,
            "size_kb": file_size_kb,
            "video_title": video_title,
            "sections": sections,
            "date": datetime.datetime.now().isoformat(),
            "favorite": False
        }
        manifest.append(record)
        self.save_manifest(manifest)
        return record

    def delete_export(self, export_id):
        manifest = self.load_manifest()
        new_manifest = []
        for record in manifest:
            if record["id"] == export_id:
                # Remove file from disk
                if os.path.exists(record["filepath"]):
                    try:
                        os.remove(record["filepath"])
                    except Exception as e:
                        print(f"Error deleting file {record['filepath']}: {e}")
            else:
                new_manifest.append(record)
        self.save_manifest(new_manifest)

    def rename_export(self, export_id, new_name):
        manifest = self.load_manifest()
        for record in manifest:
            if record["id"] == export_id:
                old_filepath = record["filepath"]
                # Ensure new name has correct extension
                ext = os.path.splitext(old_filepath)[1]
                if not new_name.endswith(ext):
                    new_name += ext
                
                new_filepath = os.path.join(self.exports_dir, new_name)
                
                if os.path.exists(old_filepath):
                    try:
                        os.rename(old_filepath, new_filepath)
                        record["filename"] = new_name
                        record["filepath"] = new_filepath
                    except Exception as e:
                        print(f"Error renaming file: {e}")
                        break
        self.save_manifest(manifest)

    def toggle_favorite(self, export_id):
        manifest = self.load_manifest()
        for record in manifest:
            if record["id"] == export_id:
                record["favorite"] = not record.get("favorite", False)
                break
        self.save_manifest(manifest)
