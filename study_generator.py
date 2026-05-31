import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def generate_flashcard_deck(transcript, title, chapters, difficulty, selected_model="gemini-2.5-flash"):
    """
    Queries Gemini to parse key entities, definitions, formulas, and concepts into a study flashcards deck.
    """
    chapters_text = ""
    if chapters:
        for i, ch in enumerate(chapters):
            chapters_text += f"- Chapter {i+1}: {ch.get('title', 'Chapter')} ({ch.get('start_time', '00:00')}) - Summary: {ch.get('summary', '')}\n"

    prompt = f"""
    You are an expert Educational Content Designer and Learning Experience Specialist.
    Analyze the transcript and chapter info for the video "{title}" and generate a set of highly effective study flashcards.
    
    Difficulty Level: {difficulty}
    
    Video Content:
    {chapters_text}
    
    Transcript snippet:
    {transcript[:28000]}
    
    Instructions:
    1. Generate 10-15 flashcards.
    2. Categories should be: "Basic Q&A", "Definition", "Concept", "Interview", "Scenario-Based", "Formula".
    3. Ensure questions are clear, concise, and encourage active recall.
    4. Provide accurate, clear, and comprehensive answers.
    5. Attach timestamp estimates and corresponding chapter names.
    
    Return ONLY a raw, valid JSON list of flashcard objects following the schema below. 
    Do NOT include markdown syntax (like ```json or ```), backticks, comments, or any other surrounding text.

    JSON Schema:
    [
      {{
        "question": "Question text here?",
        "answer": "Answer text here.",
        "category": "Concept",  // Basic Q&A, Definition, Concept, Interview, Scenario-Based, Formula
        "difficulty": "Intermediate", // Beginner, Intermediate, Advanced
        "chapter": "Chapter Name",
        "timestamp": "MM:SS",
        "importance_score": 85
      }}
    ]
    """
    
    try:
        model = ChatGoogleGenerativeAI(model=selected_model)
        response = model.invoke([HumanMessage(content=prompt)])
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        
        # Isolate JSON list
        start_idx = clean_text.find("[")
        end_idx = clean_text.rfind("]")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        cards = json.loads(clean_text)
        
        # Enrich cards with spaced repetition defaults
        for card in cards:
            card["status"] = "New"
            card["interval_days"] = 0
            card["reviews_count"] = 0
            card["bookmarked"] = False
            
        return cards
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return get_fallback_flashcards(title)

def get_fallback_flashcards(title):
    return [
        {
            "question": f"What is the main topic of {title}?",
            "answer": "The main topic revolves around the concepts, tools, and workflows presented in the video.",
            "category": "Basic Q&A",
            "difficulty": "Beginner",
            "chapter": "Introduction",
            "timestamp": "00:00",
            "importance_score": 90,
            "status": "New",
            "interval_days": 0,
            "reviews_count": 0,
            "bookmarked": False
        },
        {
            "question": "What is the primary benefit of the methods described?",
            "answer": "They streamline workflows, improve efficiency, and enable data-driven decision making.",
            "category": "Concept",
            "difficulty": "Beginner",
            "chapter": "Overview",
            "timestamp": "01:30",
            "importance_score": 80,
            "status": "New",
            "interval_days": 0,
            "reviews_count": 0,
            "bookmarked": False
        }
    ]

def generate_advanced_quiz(transcript, title, chapters, num_questions=10, quiz_type="Mixed Quiz", difficulty="Mixed", selected_model="gemini-2.5-flash"):
    """
    Queries Gemini to create MCQ, True/False, and Fill in the Blanks questions from the transcript.
    """
    chapters_text = ""
    if chapters:
        for i, ch in enumerate(chapters):
            chapters_text += f"- Chapter {i+1}: {ch.get('title', 'Chapter')} ({ch.get('start_time', '00:00')}) - Summary: {ch.get('summary', '')}\n"

    prompt = f"""
    You are a professional Assessment Designer and Exam Compiler.
    Analyze the transcript and chapter info for the video "{title}" and compile a high-quality quiz.
    
    Quiz Specifications:
    - Number of questions: {num_questions}
    - Quiz Type: {quiz_type} (options: "MCQ Only", "True/False Only", "Fill in the Blanks Only", "Mixed Quiz")
    - Difficulty: {difficulty} (options: "Easy", "Medium", "Hard", "Mixed")
    
    Video Breakdown:
    {chapters_text}
    
    Transcript snippet:
    {transcript[:26000]}
    
    Instructions:
    1. Questions must evaluate conceptual understanding, not just trivia.
    2. For Multiple Choice (MCQ): Include 4 unique options, 1 correct, 3 plausible distractors (no silly choices).
    3. For True/False: Provide statement, correct answer as "True" or "False".
    4. For Fill in the Blanks: Provide sentence with a blank (use underscores e.g., "_____ is a framework"), and correct term.
    5. Include detailed explanations, referenced chapters, and referenced timestamp estimates.
    
    Return ONLY a raw, valid JSON list of question objects following the schema below.
    Do NOT include markdown syntax (like ```json or ```), backticks, comments, or any other surrounding text.

    JSON Schema:
    [
      {{
        "type": "MCQ",  // MCQ, True/False, Fill in the Blanks
        "question": "Question content here?",
        "options": ["Option A", "Option B", "Option C", "Option D"], // Only for MCQ. Empty list otherwise.
        "answer": "Option B", // For MCQ, must match exactly. For True/False, "True" or "False". For Fill in the Blanks, the exact word.
        "explanation": "Detailed explanation of the correct answer.",
        "difficulty": "Medium", // Easy, Medium, Hard
        "chapter": "Chapter Title",
        "timestamp": "MM:SS",
        "relevance_score": 90
      }}
    ]
    """
    
    try:
        model = ChatGoogleGenerativeAI(model=selected_model)
        response = model.invoke([HumanMessage(content=prompt)])
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        
        start_idx = clean_text.find("[")
        end_idx = clean_text.rfind("]")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        questions = json.loads(clean_text)
        return questions
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return get_fallback_quiz(title)

def get_fallback_quiz(title):
    return [
        {
            "type": "MCQ",
            "question": f"What is the primary topic of the video: {title}?",
            "options": ["Machine Learning and AI", "Web Development", "Hardware Architecture", "Graphic Design"],
            "answer": "Machine Learning and AI",
            "explanation": "The video content details workflows in machine learning, neural networks, and applications.",
            "difficulty": "Easy",
            "chapter": "Introduction",
            "timestamp": "00:00",
            "relevance_score": 95
        },
        {
            "type": "True/False",
            "question": "Unsupervised learning requires fully labeled training datasets.",
            "options": [],
            "answer": "False",
            "explanation": "Unsupervised learning maps similarities in unlabeled datasets; supervised learning requires labeled data.",
            "difficulty": "Easy",
            "chapter": "Clustering",
            "timestamp": "01:30",
            "relevance_score": 90
        }
    ]

def generate_booster_quiz(transcript, weak_topics, selected_model="gemini-2.5-flash"):
    """
    Generates 5 specialized questions focusing on topics the user got wrong.
    """
    prompt = f"""
    You are an Adaptive Learning Assistant.
    Generate a quiz focusing specifically on these weak concept areas: {', '.join(weak_topics)}.
    
    Transcript context:
    {transcript[:20000]}
    
    Instructions:
    Generate exactly 5 questions (mix of MCQ and True/False) addressing these topics to help the student master their weak areas.
    
    Return ONLY a raw, valid JSON list of question objects matching the standard schema:
    [
      {{
        "type": "MCQ", // MCQ or True/False
        "question": "Question text?",
        "options": ["A", "B", "C", "D"], // Only for MCQ
        "answer": "A",
        "explanation": "Explanation focused on clearing up misconceptions.",
        "difficulty": "Medium",
        "chapter": "Review",
        "timestamp": "00:00",
        "relevance_score": 90
      }}
    ]
    """
    try:
        model = ChatGoogleGenerativeAI(model=selected_model)
        response = model.invoke([HumanMessage(content=prompt)])
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        
        start_idx = clean_text.find("[")
        end_idx = clean_text.rfind("]")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error generating booster quiz: {e}")
        return []

def export_anki_format(cards):
    """
    Formats flashcards in Anki tab-separated text import layout.
    Question \t Answer \t Tags
    """
    lines = []
    for card in cards:
        q = card['question'].replace('\n', '<br>').replace('\t', ' ')
        a = card['answer'].replace('\n', '<br>').replace('\t', ' ')
        tag = f"flashcards,{card.get('category','Concept')},{card.get('difficulty','Medium')}".replace(" ", "_")
        lines.append(f"{q}\t{a}\t{tag}")
    return "\n".join(lines)

def export_moodle_gift(questions):
    """
    Formats questions in Moodle GIFT assessment format.
    """
    gift_lines = []
    for idx, q in enumerate(questions):
        q_type = q.get("type", "MCQ")
        title = f"Question_{idx+1}"
        text = q.get("question", "")
        
        if q_type == "MCQ":
            opts = []
            correct = q.get("answer", "")
            for o in q.get("options", []):
                if o == correct:
                    opts.append(f"={o}")
                else:
                    opts.append(f"~{o}")
            options_str = " ".join(opts)
            gift_lines.append(f"::{title}:: {text} {{{options_str}}}")
        elif q_type == "True/False":
            ans = "T" if str(q.get("answer", "")).lower() in ("true", "t", "yes") else "F"
            gift_lines.append(f"::{title}:: {text} {{{ans}}}")
        elif q_type == "Fill in the Blanks":
            ans = q.get("answer", "")
            gift_lines.append(f"::{title}:: {text} {{{ans}}}")
            
    return "\n\n".join(gift_lines)

def export_google_forms(questions):
    """
    Formats questions for import into Google Forms add-ons.
    """
    lines = []
    for idx, q in enumerate(questions):
        lines.append(f"Question {idx+1}")
        lines.append(q["question"])
        
        if q.get("type") == "MCQ":
            correct = q.get("answer")
            for o in q.get("options", []):
                if o == correct:
                    lines.append(f"*{o}")
                else:
                    lines.append(o)
        elif q.get("type") == "True/False":
            correct = str(q.get("answer"))
            if correct.lower() in ("true", "t", "yes"):
                lines.append("*True")
                lines.append("False")
            else:
                lines.append("True")
                lines.append("*False")
        else:
            lines.append(f"Answer: {q.get('answer')}")
        lines.append("")
    return "\n".join(lines)
