import os
import tempfile
import google.generativeai as genai
from moviepy import VideoFileClip
import time

def extract_metadata(file_path):
    """
    Extracts metadata from a media file using moviepy.
    """
    ext = os.path.splitext(file_path)[1].lower()
    is_video = ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.mpeg', '.m4v', '.flv']
    is_audio = ext in ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma']
    
    metadata = {
        "filename": os.path.basename(file_path),
        "extension": ext,
        "is_video": is_video,
        "is_audio": is_audio,
        "size_bytes": os.path.getsize(file_path),
        "duration_sec": 0,
    }
    
    try:
        if is_video or is_audio:
            with VideoFileClip(file_path) if is_video else None as clip:
                # If it's pure audio, moviepy AudioFileClip can be used but usually we just use the API
                if is_video and clip:
                    metadata["duration_sec"] = clip.duration
                    metadata["fps"] = clip.fps
                    metadata["resolution"] = clip.size
    except Exception as e:
        print(f"Metadata extraction error: {e}")
        
    return metadata

def extract_audio_from_video(video_path, output_dir="temp_audio"):
    """
    Extracts audio from video to an mp3 file to save upload size for Gemini API.
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")
    
    try:
        with VideoFileClip(video_path) as clip:
            if clip.audio is None:
                return None
            clip.audio.write_audiofile(audio_path, logger=None)
        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

def transcribe_audio(audio_path, api_key=None):
    """
    Transcribes audio using Gemini 1.5 Pro File API.
    Returns transcript text with basic timestamps if requested.
    """
    if api_key:
        genai.configure(api_key=api_key)
        
    try:
        # Upload the file to Gemini
        print(f"Uploading {audio_path} to Gemini...")
        uploaded_file = genai.upload_file(path=audio_path)
        
        # Wait for processing if necessary
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini failed to process the audio file.")
            
        # Use Gemini 1.5 Pro for transcription
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        
        prompt = "Transcribe this audio file accurately. Please provide the full transcript. Do not summarize. Just provide the verbatim transcription."
        
        print("Generating transcript...")
        response = model.generate_content([uploaded_file, prompt])
        
        # Clean up
        genai.delete_file(uploaded_file.name)
        
        return response.text.strip()
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None
