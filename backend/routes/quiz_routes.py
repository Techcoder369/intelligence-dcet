"""
Quiz and Flashcard Routes
Handles quiz generation, submission, and flashcard operations
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
from backend.services.auth_service import verify_token
from backend.services.ai_service import generate_quiz, generate_flashcards
from backend.models.database import SessionLocal, QuizAttempt, FlashcardSession, Subject, Unit

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "No token provided"}), 401
        
        token = auth_header.split(' ')[1]
        result = verify_token(token)
        
        if not result["success"]:
            return jsonify({"success": False, "message": result["message"]}), 401
        
        request.user_id = result["payload"]["user_id"]
        request.user_role = result["payload"]["role"]
        return f(*args, **kwargs)
    return decorated

@quiz_bp.route('/generate', methods=['POST'])
@require_auth
def generate_quiz_route():
    """Generate a quiz for a subject and unit"""
    data = request.get_json()
    
    subject_id = data.get('subject_id')
    unit_id = data.get('unit_id')
    difficulty = data.get('difficulty', 'medium')
    mode = data.get('mode', 'quiz')
    
    if not subject_id or not unit_id:
        return jsonify({"success": False, "message": "Subject and unit are required"}), 400
    
    if difficulty not in ['easy', 'medium', 'hard']:
        difficulty = 'medium'
    
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        
        if not subject or not unit:
            return jsonify({"success": False, "message": "Subject or unit not found"}), 404
        
        if mode == 'flashcard':
            result = generate_flashcards(subject_id, unit_id, difficulty)
            
            if result["success"]:
                session = FlashcardSession(
                    user_id=request.user_id,
                    subject_id=subject_id,
                    unit_id=unit_id,
                    total_cards=len(result["flashcards"]),
                    flashcards_data=json.dumps(result["flashcards"])
                )
                db.add(session)
                db.commit()
                
                result["session_id"] = session.id
        else:
            result = generate_quiz(subject_id, unit_id, difficulty)
            
            if result["success"]:
                attempt = QuizAttempt(
                    user_id=request.user_id,
                    subject_id=subject_id,
                    unit_id=unit_id,
                    difficulty=difficulty,
                    total_questions=len(result["questions"]),
                    questions_data=json.dumps(result["questions"])
                )
                db.add(attempt)
                db.commit()
                
                result["attempt_id"] = attempt.id
        
        result["subject_name"] = subject.name
        result["unit_name"] = unit.name
        
        return jsonify(result), 200 if result["success"] else 400
    finally:
        db.close()

@quiz_bp.route('/submit', methods=['POST'])
@require_auth
def submit_quiz():
    """Submit quiz answers and calculate score"""
    data = request.get_json()
    
    attempt_id = data.get('attempt_id')
    answers = data.get('answers', [])
    time_spent = data.get('time_spent_seconds', 0)
    
    if not attempt_id:
        return jsonify({"success": False, "message": "Attempt ID is required"}), 400
    
    db = SessionLocal()
    try:
        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == request.user_id
        ).first()
        
        if not attempt:
            return jsonify({"success": False, "message": "Quiz attempt not found"}), 404
        
        questions = json.loads(attempt.questions_data)
        
        correct_count = 0
        results = []
        
        for i, question in enumerate(questions):
            user_answer = answers[i] if i < len(answers) else -1
            is_correct = user_answer == question["correct_index"]
            if is_correct:
                correct_count += 1
            
            results.append({
                "question": question["question"],
                "options": question["options"],
                "correct_index": question["correct_index"],
                "user_answer": user_answer,
                "is_correct": is_correct,
                "explanation": question["explanation"]
            })
        
        score_percentage = (correct_count / len(questions) * 100) if questions else 0
        
        attempt.correct_answers = correct_count
        attempt.score_percentage = score_percentage
        attempt.answers_data = json.dumps(answers)
        attempt.completed_at = datetime.utcnow()
        attempt.time_spent_seconds = time_spent
        
        db.commit()
        
        return jsonify({
            "success": True,
            "score": correct_count,
            "total": len(questions),
            "percentage": round(score_percentage, 1),
            "results": results,
            "time_spent_seconds": time_spent
        }), 200
    finally:
        db.close()

@quiz_bp.route('/flashcard/complete', methods=['POST'])
@require_auth
def complete_flashcard_session():
    """Complete a flashcard session and save stats"""
    data = request.get_json()
    
    session_id = data.get('session_id')
    cards_known = data.get('cards_known', 0)
    cards_unknown = data.get('cards_unknown', 0)
    time_spent = data.get('time_spent_seconds', 0)
    
    if not session_id:
        return jsonify({"success": False, "message": "Session ID is required"}), 400
    
    db = SessionLocal()
    try:
        session = db.query(FlashcardSession).filter(
            FlashcardSession.id == session_id,
            FlashcardSession.user_id == request.user_id
        ).first()
        
        if not session:
            return jsonify({"success": False, "message": "Flashcard session not found"}), 404
        
        session.cards_known = cards_known
        session.cards_unknown = cards_unknown
        session.completed_at = datetime.utcnow()
        session.time_spent_seconds = time_spent
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Flashcard session completed",
            "cards_known": cards_known,
            "cards_unknown": cards_unknown,
            "total_cards": session.total_cards
        }), 200
    finally:
        db.close()

@quiz_bp.route('/history', methods=['GET'])
@require_auth
def get_quiz_history():
    """Get quiz attempt history for current user"""
    db = SessionLocal()
    try:
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == request.user_id
        ).order_by(QuizAttempt.started_at.desc()).limit(20).all()
        
        history = []
        for attempt in attempts:
            subject = db.query(Subject).filter(Subject.id == attempt.subject_id).first()
            unit = db.query(Unit).filter(Unit.id == attempt.unit_id).first()
            
            history.append({
                "id": attempt.id,
                "subject_name": subject.name if subject else "Unknown",
                "unit_name": unit.name if unit else "Unknown",
                "difficulty": attempt.difficulty,
                "score": attempt.correct_answers,
                "total": attempt.total_questions,
                "percentage": attempt.score_percentage,
                "date": attempt.started_at.isoformat() if attempt.started_at else None,
                "completed": attempt.completed_at is not None
            })
        
        return jsonify({
            "success": True,
            "history": history
        }), 200
    finally:
        db.close()
