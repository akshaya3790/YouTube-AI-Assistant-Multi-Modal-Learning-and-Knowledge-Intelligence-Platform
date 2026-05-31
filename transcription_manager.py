import os
import json
import hashlib
import time
import streamlit as st
import tempfile

class TranscriptionManager:
    def __init__(self, cache_dir="study_data"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "transcript_cache.json")
        self._ensure_cache()

    def _ensure_cache(self):
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, "w") as f:
                json.dump({}, f)

    def _load_cache(self):
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save_cache(self, data):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_transcript(self, source_id, audio_path=None, is_youtube=True):
        """
        Waterfall: Cache -> YouTube API -> Local Whisper -> Groq -> Gemini -> OpenAI
        Returns: (transcript_text, provider_name, raw_segments)
        """
        cache = self._load_cache()
        if source_id in cache:
            return cache[source_id]["text"], "Cache", cache[source_id].get("segments")

        transcript_text, segments, provider = None, None, None

        # 1. Try YouTube API
        if is_youtube:
            print(f"TRANSCRIPTION_MANAGER: Attempting YouTube API for {source_id}")
            text, segs = self._try_youtube_api(source_id)
            if text:
                transcript_text, segments, provider = text, segs, "YouTube Transcript"

        # 2. Try Local Whisper
        if not transcript_text and audio_path and os.path.exists(audio_path):
            print(f"TRANSCRIPTION_MANAGER: Attempting Local Whisper for {source_id}")
            text, segs = self._try_local_whisper(audio_path)
            if text:
                transcript_text, segments, provider = text, segs, "Local Whisper"

        # 3. Try Groq API
        if not transcript_text and audio_path and os.path.exists(audio_path):
            print(f"TRANSCRIPTION_MANAGER: Attempting Groq API for {source_id}")
            text = self._try_groq(audio_path)
            if text:
                transcript_text, segments, provider = text, None, "Groq"

        # 4. Try Gemini API
        if not transcript_text and audio_path and os.path.exists(audio_path):
            print(f"TRANSCRIPTION_MANAGER: Attempting Gemini API for {source_id}")
            text = self._try_gemini(audio_path)
            if text:
                transcript_text, segments, provider = text, None, "Gemini"

        # 5. Try OpenAI API
        if not transcript_text and audio_path and os.path.exists(audio_path):
            print(f"TRANSCRIPTION_MANAGER: Attempting OpenAI API for {source_id}")
            text = self._try_openai(audio_path)
            if text:
                transcript_text, segments, provider = text, None, "OpenAI"

        if transcript_text:
            cache[source_id] = {
                "text": transcript_text,
                "segments": segments,
                "provider": provider,
                "timestamp": time.time()
            }
            self._save_cache(cache)
            return transcript_text, provider, segments
            
        print("TRANSCRIPTION_MANAGER: ALL PROVIDERS FAILED.")
        return None, None, None

    def _try_youtube_api(self, video_id):
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            try:
                api_instance = YouTubeTranscriptApi()
                transcript_list_obj = api_instance.list(video_id)
                transcript_obj = transcript_list_obj.find_transcript(['en', 'hi', 'te', 'ta', 'kn', 'ml'])
                raw_transcript = transcript_obj.fetch()
                
                transcript_list = []
                for item in raw_transcript:
                    transcript_list.append({
                        'text': getattr(item, 'text', item.get('text', '')),
                        'start': getattr(item, 'start', item.get('start', 0.0))
                    })
            except AttributeError:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'te', 'ta', 'kn', 'ml'])
            
            transcript_text = " ".join([item['text'] for item in transcript_list])
            return transcript_text, transcript_list
        except Exception as e:
            print(f"YouTube API Failed: {e}")
            return None, None

    def _try_local_whisper(self, audio_path):
        try:
            from faster_whisper import WhisperModel
            # Load tiny or base model to ensure CPU can handle it in a reasonable time
            model_size = "base"
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            
            segments, info = model.transcribe(audio_path, beam_size=5)
            print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
            
            transcript_text = ""
            raw_segments = []
            for segment in segments:
                transcript_text += segment.text + " "
                raw_segments.append({
                    "text": segment.text,
                    "start": segment.start
                })
            return transcript_text.strip(), raw_segments
        except ImportError:
            print("faster-whisper is not installed.")
            return None, None
        except Exception as e:
            print(f"Local Whisper Failed: {e}")
            return None, None

    def _try_groq(self, audio_path):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("GROQ_API_KEY missing.")
            return None
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            with open(audio_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model="whisper-large-v3",
                )
            return transcription.text
        except Exception as e:
            print(f"Groq API Failed: {e}")
            return None

    def _try_gemini(self, audio_path):
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("GEMINI_API_KEY missing.")
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            uploaded_file = genai.upload_file(path=audio_path)
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
                
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini processing failed.")
                
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response = model.generate_content([uploaded_file, "Transcribe this audio file verbatim without summarization."])
            
            genai.delete_file(uploaded_file.name)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API Failed: {e}")
            return None

    def _try_openai(self, audio_path):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY missing.")
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcription.text
        except Exception as e:
            print(f"OpenAI API Failed: {e}")
            return None
