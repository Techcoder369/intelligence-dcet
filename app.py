"""
Intelligence DCET Quiz Generator
Main Flask Application
"""

import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.models.database import init_db, seed_initial_data
from backend.routes.auth_routes import auth_bp
from backend.routes.student_routes import student_bp
from backend.routes.quiz_routes import quiz_bp
from backend.routes.subject_routes import subject_bp
from backend.routes.admin_routes import admin_bp


def create_app():
    app = Flask(
        __name__,
        static_folder="frontend",
        static_url_path=""
    )

    # ---------------- CONFIG ----------------
    app.config["SECRET_KEY"] = os.getenv(
        "SESSION_SECRET", "dcet-quiz-secret-key-2024"
    )
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    CORS(app)

    # ---------------- API BLUEPRINTS ----------------
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(quiz_bp, url_prefix="/quiz")

    # These blueprints already define their own prefixes
    app.register_blueprint(student_bp)   # /students/*
    app.register_blueprint(subject_bp)   # /subjects/*

    # Admin APIs
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ---------------- FRONTEND PAGES ----------------
    @app.route("/")
    def serve_index():
        return send_from_directory("frontend", "index.html")

    @app.route("/dashboard")
    def serve_dashboard():
        return send_from_directory("frontend/pages", "dashboard.html")

    @app.route("/subject")
    def serve_subject():
        return send_from_directory("frontend/pages", "subject.html")

    @app.route("/quiz")
    def serve_quiz_page():
        return send_from_directory("frontend/pages", "quiz.html")

    @app.route("/flashcard")
    def serve_flashcard():
        return send_from_directory("frontend/pages", "flashcard.html")

    @app.route("/profile")
    def serve_profile():
        return send_from_directory("frontend/pages", "profile.html")

    @app.route("/admin-login")
    def serve_admin_login():
        return send_from_directory("frontend/pages", "admin-login.html")

    @app.route("/admin")
    def serve_admin_dashboard():
        return send_from_directory("frontend/pages", "admin.html")

    # ---------------- STATIC FILES ----------------
    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory("frontend/css", filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory("frontend/js", filename)

    @app.route("/pages/<path:filename>")
    def serve_pages(filename):
        return send_from_directory("frontend/pages", filename)

    # ---------------- HEALTH CHECK ----------------
    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "app": "Intelligence DCET Quiz Generator"
        })

    return app


# ✅ THIS IS REQUIRED FOR GUNICORN
app = create_app()


# ---------------- LOCAL DEV ONLY ----------------
if __name__ == "__main__":
    init_db()
    seed_initial_data()
    app.run(host="0.0.0.0", port=5000, debug=True)
