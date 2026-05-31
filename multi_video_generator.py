import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import google.generativeai as genai
import math
import numpy as np

def analyze_video_independently(transcript, title, selected_model="gemini-2.5-flash"):
    """
    Analyzes a single video transcript to extract chapter summaries and key concepts.
    """
    model = ChatGoogleGenerativeAI(model=selected_model)
    prompt = f"""
    Analyze the following video transcript titled "{title}".
    Extract the key concepts and a brief summary of the main points.
    Return ONLY a valid JSON object with the following structure:
    {{
        "video_title": "{title}",
        "summary": "Overall summary of the video",
        "concepts": [
            {{
                "name": "Concept Name",
                "description": "Explanation of the concept",
                "importance_score": 85
            }}
        ]
    }}
    Transcript: {transcript[:15000]}
    """
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        json_text = response.content.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error analyzing video {title}: {e}")
        return None

def detect_insights(video_analyses, selected_model="gemini-2.5-flash"):
    """
    Analyzes concepts across all videos to find Common Insights and Unique Insights.
    """
    model = ChatGoogleGenerativeAI(model=selected_model)
    analyses_json = json.dumps(video_analyses, indent=2)
    prompt = f"""
    Analyze the following extracted concepts from multiple videos.
    Identify:
    1. Common Insights: Concepts that appear in multiple videos.
    2. Unique Insights: Ideas found in only one video.
    
    Return ONLY a valid JSON object with the following structure:
    {{
        "common_insights": [
            {{
                "concept": "Concept Name",
                "videos_mentioning": ["Video 1", "Video 2"],
                "frequency": 2,
                "importance_score": 90
            }}
        ],
        "unique_insights": [
            {{
                "concept": "Unique Concept Name",
                "source_video": "Video 3",
                "importance_score": 75,
                "reason_for_uniqueness": "Only discussed in this specific context"
            }}
        ]
    }}
    Video Analyses: {analyses_json}
    """
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        json_text = response.content.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error detecting insights: {e}")
        return {"common_insights": [], "unique_insights": []}

def detect_contradictions(video_analyses, selected_model="gemini-2.5-flash"):
    """
    Looks for conflicting statements between video concepts.
    """
    model = ChatGoogleGenerativeAI(model=selected_model)
    analyses_json = json.dumps(video_analyses, indent=2)
    prompt = f"""
    Analyze the following extracted concepts from multiple videos.
    Identify any potential contradictions or conflicting statements between different videos.
    
    Return ONLY a valid JSON object with the following structure:
    {{
        "contradictions": [
            {{
                "topic": "Topic Name",
                "video_a": "Title of first video",
                "statement_a": "What first video says",
                "video_b": "Title of second video",
                "statement_b": "What second video says",
                "explanation": "Why they contradict"
            }}
        ]
    }}
    Video Analyses: {analyses_json}
    """
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        json_text = response.content.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error detecting contradictions: {e}")
        return {"contradictions": []}

def generate_comparison_table(video_analyses, selected_model="gemini-2.5-flash"):
    """
    Outputs a structured Markdown matrix comparing topics across videos.
    """
    model = ChatGoogleGenerativeAI(model=selected_model)
    analyses_json = json.dumps(video_analyses, indent=2)
    prompt = f"""
    Based on the following extracted concepts from multiple videos, create a comparison table in Markdown format.
    Rows should be topics/concepts, and columns should be the video titles.
    Use 'Yes' or 'No' or brief text to indicate if/how a topic is covered in each video.
    
    Return ONLY the raw Markdown table. No other text.
    
    Video Analyses: {analyses_json}
    """
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        print(f"Error generating comparison table: {e}")
        return ""

def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2) if norm_v1 and norm_v2 else 0.0

def calculate_similarity_matrix(video_titles, video_transcripts):
    """
    Calculates cosine similarity between videos using text embeddings.
    """
    try:
        embeddings = []
        for text in video_transcripts:
            # truncate for embedding
            text = text[:8000]
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result["embedding"])
            
        matrix = []
        for i in range(len(embeddings)):
            row = []
            for j in range(len(embeddings)):
                sim = cosine_similarity(embeddings[i], embeddings[j])
                row.append(round(sim * 100, 2))
            matrix.append({"title": video_titles[i], "scores": row})
            
        return matrix
    except Exception as e:
        print(f"Error calculating similarity matrix: {e}")
        return []

def generate_consolidated_summary(transcripts, length_mode="Medium", selected_model="gemini-1.5-pro-latest"):
    """
    Writes a master summary combining all knowledge.
    """
    model = ChatGoogleGenerativeAI(model=selected_model)
    length_instruction = {
        "Short": "300-500 words.",
        "Medium": "1000-2000 words.",
        "Detailed": "3000-5000 words. Provide extreme detail and thorough explanations."
    }.get(length_mode, "1000-2000 words.")
    
    combined_text = "\n\n--- NEXT VIDEO ---\n\n".join(transcripts)
    
    prompt = f"""
    You are an expert AI Research Analyst.
    I have provided transcripts from multiple videos on a related subject.
    Your task is to generate a comprehensive Consolidated Master Summary combining the knowledge from ALL these sources.
    
    Length requirement: {length_instruction}
    
    Structure the report with these sections:
    # 📚 Master Summary
    ## 📋 Overview
    ## 🧩 Major Concepts
    ## 🔗 Common Findings
    ## 💡 Unique Perspectives
    ## 🛠️ Best Practices & Recommendations
    ## 🏁 Final Conclusion
    
    Transcripts:
    {combined_text[:100000]}
    """
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        print(f"Error generating consolidated summary: {e}")
        return "Failed to generate consolidated summary."

def identify_best_videos(video_analyses, selected_model="gemini-2.5-flash"):
    """
    Categorizes videos (Most Detailed, Beginner Friendly, etc.).
    """
    model = ChatGoogleGenerativeAI(model=selected_model)
    analyses_json = json.dumps(video_analyses, indent=2)
    prompt = f"""
    Analyze the following extracted concepts and summaries from multiple videos.
    Identify the "Best" video for each of the following categories:
    - Most Detailed Explanation
    - Most Beginner Friendly Explanation
    - Most Technical Explanation
    - Most Practical Explanation
    
    Return ONLY a valid JSON object with the following structure:
    {{
        "categories": [
            {{
                "category": "Most Detailed Explanation",
                "video_title": "Title of the video",
                "reason": "Why this video is best for this category"
            }}
        ]
    }}
    Video Analyses: {analyses_json}
    """
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        json_text = response.content.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error identifying best videos: {e}")
        return {"categories": []}

def compile_multi_video_report(transcripts_dict, length_mode="Medium", selected_model="gemini-2.5-flash"):
    """
    Orchestrates the entire multi-video analysis pipeline.
    transcripts_dict: dict of { "video_title": "transcript text" }
    """
    titles = list(transcripts_dict.keys())
    transcripts = list(transcripts_dict.values())
    
    video_analyses = []
    for title, text in transcripts_dict.items():
        analysis = analyze_video_independently(text, title, selected_model)
        if analysis:
            video_analyses.append(analysis)
            
    insights = detect_insights(video_analyses, selected_model)
    contradictions = detect_contradictions(video_analyses, selected_model)
    comparison_table = generate_comparison_table(video_analyses, selected_model)
    similarity_matrix = calculate_similarity_matrix(titles, transcripts)
    best_videos = identify_best_videos(video_analyses, selected_model)
    
    # Use Pro model for the large consolidated summary if possible
    pro_model = "gemini-1.5-pro-latest" if "pro" in selected_model else selected_model
    consolidated_summary = generate_consolidated_summary(transcripts, length_mode, pro_model)
    
    return {
        "video_analyses": video_analyses,
        "insights": insights,
        "contradictions": contradictions,
        "comparison_table": comparison_table,
        "similarity_matrix": similarity_matrix,
        "best_videos": best_videos,
        "consolidated_summary": consolidated_summary
    }
