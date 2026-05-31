import os
# Fix for OpenMP duplicate library error
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import yt_dlp
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import time

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "AIzaSyCefTl5p31gixkgkTFfaO7WJefK_VbB_RQ"
genai.configure(api_key=GEMINI_API_KEY)
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

def download_audio(url):
    print(f"Downloading audio from: {url}")
    if not os.path.exists("temp_audio"):
        os.makedirs("temp_audio")
        
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'temp_audio/%(id)s.%(ext)s',
        'quiet': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

def process_with_gemini(file_path):
    print("Uploading to Gemini...")
    audio_file = genai.upload_file(path=file_path)
    
    print("Waiting for processing...")
    wait_start_time = time.time()
    while audio_file.state.name == "PROCESSING":
        time.sleep(5)
        audio_file = genai.get_file(audio_file.name)
        if time.time() - wait_start_time > 600:
            raise Exception("Processing timed out.")
            
    if audio_file.state.name == "FAILED":
        raise Exception("AI failed to process the audio file.")
        
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    prompt = "Summarize the key points of this video audio."
    
    print("Generating summary...")
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "media", "file_uri": audio_file.uri, "mime_type": audio_file.mime_type}
        ]
    )
    response = model.invoke([message])
    return response.content

if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=h5id4erwD4s"
    print("###############################################")
    print("Starting Pure-Python Gemini Video Summarizer")
    print("###############################################")
    
    try:
        audio_path = download_audio(youtube_url)
        if audio_path:
            summary = process_with_gemini(audio_path)
            print("\n--- RESULTS ---\n")
            print(summary)
            
            # Clean up
            os.remove(audio_path)
    except Exception as e:
        print(f"Error: {e}")
