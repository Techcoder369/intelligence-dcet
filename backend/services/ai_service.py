"""
AI Service - Smart Content Generator (FINAL VERSION)
MCQs + Flashcards generated fully from document context based on difficulty
"""

import os
import json
import re
from typing import Dict, List

# ======================================================
# GROQ SETUP
# ======================================================

GROQ_AVAILABLE = False
client = None

try:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if api_key and len(api_key) > 20:
        client = Groq(api_key=api_key)
        GROQ_AVAILABLE = True
        print("✅ Groq AI connected")
    else:
        print("⚠ GROQ_API_KEY missing or invalid")

except Exception as e:
    print(f"⚠ Groq init failed: {e}")
    GROQ_AVAILABLE = False


# ======================================================
# RAG SERVICE
# ======================================================

try:
    from backend.services.rag_service import rag_service
    RAG_AVAILABLE = True
except Exception as e:
    print(f"⚠ RAG service import failed: {e}")
    RAG_AVAILABLE = False


# ======================================================
# DIFFICULTY CONFIG
# ======================================================

DIFFICULTY_QUESTION_COUNT = {
    "easy": 5,
    "medium": 8,
    "hard": 10
}

FLASHCARD_COUNT = DIFFICULTY_QUESTION_COUNT


# ======================================================
# MCQ GENERATOR (UNCHANGED)
# ======================================================

def _generate_mcq_from_context(context: str) -> Dict:
    if not GROQ_AVAILABLE or not client:
        return {}

    prompt = f"""
Generate ONE exam-oriented MCQ.

Rules:
- Don't repeat any question in the same quiz
- ask questions meaningfully based on the study material you can also generate questiosn beyond the context if needed 
- Concept based
- 4 relevant options
- One correct answer
- Short explanation
- DCET/Diploma level
- Don't repate question question 

Study Material:
{context[:3500]}

Return ONLY valid JSON:
{{
  "question": "",
  "options": ["", "", "", ""],
  "correct_index": 0,
  "explanation": ""
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=500
    )

    text = response.choices[0].message.content.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return json.loads(match.group()) if match else {}


# ======================================================
# FLASHCARD GENERATOR (EXPLANATION-ONLY BACKSIDE)
# ======================================================

def _generate_flashcards_from_context(context: str, count: int) -> List[Dict]:
    if not GROQ_AVAILABLE or not client:
        return []

    prompt = f"""
You are an exam revision assistant.

Generate EXACTLY {count} flashcards from the following MCQ-based study material.

RULES FOR EACH FLASHCARD:

-ask questions meaningfully based on the study material you can also generate questiosn beyond the context if needed 

FRONT:
- Only the question text

BACK:
- ONLY a clear explanation in sentence form
- DO NOT list options
- DO NOT mention option letters (a, b, c, d)
- DO NOT mention "All of the above"
- If the correct answer implies multiple reasons,
  explain all of them naturally in the explanation
- Simple, exam-oriented language

Study Material:
{context[:4000]}

Return ONLY valid JSON array:

[
  {{
    "front": "Question text",
    "back": "Clear explanation in plain text"
  }}
]
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200
    )

    text = response.choices[0].message.content.strip()

    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group())

    flashcards = []
    for card in data:
        front = str(card.get("front", "")).strip()
        back = str(card.get("back", "")).strip()
        if front and back:
            flashcards.append({
                # frontend-safe keys
                "question": front,
                "answer": back,
                "front": front,
                "back": back
            })

    return flashcards


# ======================================================
# PUBLIC API: MCQs
# ======================================================

def generate_quiz(subject_id: int, unit_id: int, difficulty: str = "medium") -> Dict:
    if not RAG_AVAILABLE:
        return _empty_quiz("Document service not available")

    count = DIFFICULTY_QUESTION_COUNT.get(difficulty, 8)
    chunks = _get_chunks(subject_id, unit_id, top_k=40)

    context = " ".join(c.get("text", "") for c in chunks if c.get("text"))
    if len(context) < 200:
        return _empty_quiz("Insufficient content")

    questions = []
    for _ in range(count):
        mcq = _generate_mcq_from_context(context)
        if mcq:
            questions.append(mcq)

    return {
        "success": True,
        "difficulty": difficulty,
        "questions": questions
    }


# ======================================================
# PUBLIC API: FLASHCARDS
# ======================================================

def generate_flashcards(subject_id: int, unit_id: int, difficulty: str = "medium") -> Dict:
    if not RAG_AVAILABLE:
        return {"success": False, "flashcards": []}

    count = FLASHCARD_COUNT.get(difficulty, 8)
    chunks = _get_chunks(subject_id, unit_id, top_k=30)

    context = " ".join(c.get("text", "") for c in chunks if c.get("text"))
    if len(context) < 200:
        return {"success": False, "flashcards": []}

    flashcards = _generate_flashcards_from_context(context, count)

    return {
        "success": True,
        "difficulty": difficulty,
        "flashcards": flashcards
    }


# ======================================================
# HELPERS
# ======================================================

def _get_chunks(subject_id: int, unit_id: int, top_k: int = 20):
    try:
        return rag_service.retrieve_context(
            subject_id=subject_id,
            unit_id=unit_id,
            top_k=top_k
        )
    except Exception:
        return []


def _empty_quiz(message: str) -> Dict:
    return {
        "success": False,
        "message": message,
        "questions": []
    }


# ======================================================
# EXPORTS
# ======================================================

__all__ = ["generate_quiz", "generate_flashcards"]
