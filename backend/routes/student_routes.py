"""
Student Routes
Handles student profile, statistics, and quiz/flashcard operations
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from functools import wraps

from backend.services.auth_service import verify_token
from backend.models.database import (
    SessionLocal,
    User,
    Subject,
    QuizAttempt,
    FlashcardSession
)

student_bp = Blueprint("students", __name__, url_prefix="/students")

# ======================================================
# AUTH DECORATOR
# ======================================================
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "No token provided"}), 401

        token = auth_header.split(" ")[1]
        result = verify_token(token)

        if not result["success"]:
            return jsonify({"success": False, "message": result["message"]}), 401

        request.user_id = result["payload"]["user_id"]
        return f(*args, **kwargs)

    return decorated

# ======================================================
# PROFILE (GET)
# ======================================================
@student_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                # ✅ REQUIRED BY FRONTEND
                "full_name": user.username,
                "dcet_reg_number": user.dcet_reg_number,
                "mobile_number": user.mobile_number,

                # editable academic info
                "college_name": user.college_name,
                "branch": user.branch,
                "semester": user.semester,
                "target_dcet_year": user.target_dcet_year,
            }
        }), 200
    finally:
        db.close()

# ======================================================
# PROFILE (UPDATE) – SAFE FIELDS ONLY
# ======================================================
@student_bp.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    data = request.get_json()
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # ❌ DO NOT allow editing name or DCET
        user.college_name = data.get("college_name", user.college_name)
        user.branch = data.get("branch", user.branch)
        user.semester = data.get("semester", user.semester)
        user.target_dcet_year = data.get("target_dcet_year", user.target_dcet_year)
        user.updated_at = datetime.utcnow()

        db.commit()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "college_name": user.college_name,
                "branch": user.branch,
                "semester": user.semester,
                "target_dcet_year": user.target_dcet_year
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

# ======================================================
# DAILY STATS (LAST 7 DAYS)
# ======================================================
@student_bp.route("/stats/daily", methods=["GET"])
@require_auth
def get_daily_stats():
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        stats = []

        for i in range(7):
            day = today - timedelta(days=i)
            start = datetime.combine(day, datetime.min.time())
            end = datetime.combine(day, datetime.max.time())

            quizzes = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == request.user_id,
                QuizAttempt.started_at >= start,
                QuizAttempt.started_at <= end
            ).all()

            flashcards = db.query(FlashcardSession).filter(
                FlashcardSession.user_id == request.user_id,
                FlashcardSession.started_at >= start,
                FlashcardSession.started_at <= end
            ).all()

            total_questions = sum(q.total_questions for q in quizzes)
            correct_answers = sum(q.correct_answers for q in quizzes)

            accuracy = round((correct_answers / total_questions) * 100, 1) if total_questions else 0
            time_spent = sum(q.time_spent_seconds for q in quizzes) + \
                         sum(f.time_spent_seconds for f in flashcards)

            stats.append({
                "date": day.isoformat(),
                "quizzes_taken": len(quizzes),
                "flashcards_reviewed": sum(f.total_cards for f in flashcards),
                "accuracy": accuracy,
                "time_spent_minutes": round(time_spent / 60, 1)
            })

        return jsonify({"success": True, "stats": stats}), 200
    finally:
        db.close()

# ======================================================
# SUBJECT PERFORMANCE
# ======================================================
@student_bp.route("/stats/subjects", methods=["GET"])
@require_auth
def get_stats_by_subject():
    db = SessionLocal()
    try:
        subjects = db.query(Subject).all()
        stats = []

        for subject in subjects:
            quizzes = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == request.user_id,
                QuizAttempt.subject_id == subject.id
            ).all()

            total_questions = sum(q.total_questions for q in quizzes)
            correct_answers = sum(q.correct_answers for q in quizzes)
            accuracy = round((correct_answers / total_questions) * 100, 1) if total_questions else 0

            stats.append({
                "subject_id": subject.id,
                "subject_name": subject.name,
                "short_name": subject.short_name,
                "quizzes_taken": len(quizzes),
                "accuracy": accuracy
            })

        return jsonify({"success": True, "stats": stats}), 200
    finally:
        db.close()
