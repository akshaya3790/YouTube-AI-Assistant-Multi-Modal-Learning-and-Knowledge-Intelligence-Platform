import os
import sys

project_dir = r"c:\Users\prama\OneDrive\Desktop\YouTube-Video-Summarization-App-main\YouTube-Video-Summarization-App-main"
sys.path.append(project_dir)

from media_library import MediaLibrary

def test_upload_system():
    print("Testing Universal Media Upload System...")
    ml = MediaLibrary()
    
    # Simulate a file upload
    test_id = "test_local_file_001"
    test_content = b"fake audio content"
    
    path = ml.save_uploaded_file(test_id, "test_audio.mp3", test_content, is_video=False)
    assert os.path.exists(path)
    
    # Save transcript
    t_path = ml.save_transcript(test_id, "This is a local transcript.")
    assert os.path.exists(t_path)
    
    # Get info
    info = ml.get_file_info(test_id)
    assert info["is_video"] == False
    assert info["original_name"] == "test_audio.mp3"
    
    print("All Universal Media Upload tests passed successfully!")

if __name__ == "__main__":
    test_upload_system()
