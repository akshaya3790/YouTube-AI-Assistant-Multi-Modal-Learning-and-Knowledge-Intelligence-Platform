import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def generate_learning_roadmap(transcript, title, selected_model="gemini-2.5-flash"):
    """
    Generates a personalized 4-tier skill pathway roadmap based on the video context.
    """
    prompt = f"""
    You are a Senior AI Educational Architect and Career Developer.
    Analyze the following video transcript/context and generate a complete step-by-step Learning Roadmap from Beginner to Expert.
    
    Even if the video is just a beginner tutorial, use your internal knowledge to extrapolate a FULL domain roadmap (Beginner, Intermediate, Advanced, Expert) for the overarching topic.
    
    Video Title: {title}
    Transcript snippet:
    {transcript[:28000]}
    
    Return ONLY a raw, valid JSON object following the schema below. 
    Do NOT include markdown syntax (like ```json or ```), backticks, comments, or any other surrounding text.

    JSON Schema:
    {{
      "domain": "Main Topic Name (e.g. Python Programming, Machine Learning)",
      "total_estimated_time": "16 Weeks",
      "roadmap": [
        {{
          "level": "Beginner",
          "focus": "Fundamentals and Core Concepts",
          "estimated_time": "4 Weeks",
          "topics": [
            {{
              "name": "Topic Name",
              "description": "Brief explanation",
              "prerequisites": ["None or other skills"],
              "importance": "High"
            }}
          ],
          "projects": [
            {{
              "name": "Project Name",
              "description": "What to build to practice these skills"
            }}
          ],
          "resources": ["Resource 1", "Resource 2"]
        }}
      ]
    }}
    
    Note: The 'roadmap' array MUST contain exactly 4 objects corresponding to Beginner, Intermediate, Advanced, and Expert levels.
    """
    try:
        model = ChatGoogleGenerativeAI(model=selected_model)
        response = model.invoke([HumanMessage(content=prompt)])
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        report = json.loads(clean_text)
        return report
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return get_fallback_roadmap(title)

def analyze_skill_gap(target_role, current_skills, transcript_context, selected_model="gemini-2.5-flash"):
    """
    Generates a gap analysis roadmap to bridge the user's current skills to a target role.
    """
    prompt = f"""
    You are a Career Path Consultant.
    Perform a professional Skill Gap Analysis.
    
    Target Job Role: {target_role}
    Current Skills: {current_skills}
    Context of recently watched video:
    {transcript_context[:10000]}
    
    Return ONLY a raw, valid JSON object matching this schema. No markdown:
    {{
      "match_score": 60,
      "missing_skills": [
        {{
          "name": "Missing Skill",
          "why_needed": "Explanation"
        }}
      ],
      "learning_roadmap": [
        "Step 1: Learn X",
        "Step 2: Build Y"
      ],
      "recommended_projects": ["Project A", "Project B"]
    }}
    """
    try:
        model = ChatGoogleGenerativeAI(model=selected_model)
        response = model.invoke([HumanMessage(content=prompt)])
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error generating skill gap analysis: {e}")
        return {"match_score": 0, "missing_skills": [], "learning_roadmap": [], "recommended_projects": []}

def get_fallback_roadmap(title):
    return {
      "domain": title,
      "total_estimated_time": "12 Weeks",
      "roadmap": [
        {
          "level": "Beginner",
          "focus": "Fundamentals",
          "estimated_time": "3 Weeks",
          "topics": [{"name": "Basics", "description": "Core ideas", "prerequisites": [], "importance": "High"}],
          "projects": [{"name": "Hello World App", "description": "Basic execution"}],
          "resources": ["Official Documentation"]
        },
        {
          "level": "Intermediate",
          "focus": "Applied Learning",
          "estimated_time": "3 Weeks",
          "topics": [{"name": "Modules", "description": "Reusability", "prerequisites": ["Basics"], "importance": "High"}],
          "projects": [{"name": "CLI Tool", "description": "Interactive terminal app"}],
          "resources": ["Intermediate Tutorials"]
        },
        {
          "level": "Advanced",
          "focus": "Architecture",
          "estimated_time": "3 Weeks",
          "topics": [{"name": "Optimization", "description": "Performance", "prerequisites": ["Modules"], "importance": "High"}],
          "projects": [{"name": "Web App", "description": "Full stack"}],
          "resources": ["Advanced Books"]
        },
        {
          "level": "Expert",
          "focus": "System Design",
          "estimated_time": "3 Weeks",
          "topics": [{"name": "Scalability", "description": "Scale", "prerequisites": ["Optimization"], "importance": "High"}],
          "projects": [{"name": "Distributed System", "description": "Microservices"}],
          "resources": ["Whitepapers"]
        }
      ]
    }

def create_roadmap_markdown(roadmap):
    md = f"# 🗺️ AI Learning Roadmap: {roadmap.get('domain', 'Learning Path')}\n"
    md += f"**Total Estimated Time:** {roadmap.get('total_estimated_time', 'N/A')}\n\n"
    
    for level in roadmap.get("roadmap", []):
        md += f"## 📈 Level: {level.get('level', 'Unknown').upper()}\n"
        md += f"**Focus**: {level.get('focus', '')} | **Time**: {level.get('estimated_time', '')}\n\n"
        
        md += "### 📚 Core Topics:\n"
        for t in level.get("topics", []):
            reqs = ", ".join(t.get("prerequisites", []))
            md += f"- **{t.get('name')}**: {t.get('description')} (Importance: {t.get('importance')})\n"
            if reqs and reqs.lower() != "none":
                md += f"  - *Prerequisites:* {reqs}\n"
        
        md += "\n### 🚀 Recommended Projects:\n"
        for p in level.get("projects", []):
            md += f"- **{p.get('name')}**: {p.get('description')}\n"
            
        md += "\n### 📖 Resources:\n"
        for r in level.get("resources", []):
            md += f"- {r}\n"
        
        md += "\n---\n\n"
        
    return md
