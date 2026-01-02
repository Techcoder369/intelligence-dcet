

import os
import enum
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Boolean, Float, ForeignKey
)
from sqlalchemy.orm import (
    sessionmaker, relationship, declarative_base
)

# ======================================================
# DATABASE (RAILWAY ONLY)
# ======================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ======================================================
# ENUMS
# ======================================================
class UserRole(enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"

# ======================================================
# USER MODEL
# ======================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True)
    password_hash = Column(String(255))
    mobile_number = Column(String(15), unique=True)
    dcet_reg_number = Column(String(50), unique=True)
    college_name = Column(String(200))
    branch = Column(String(100))
    semester = Column(String(20))
    target_dcet_year = Column(String(10))
    username = Column(String(100), unique=True)
    role = Column(String(20), default=UserRole.STUDENT.value)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all,delete")
    flashcard_sessions = relationship("FlashcardSession", back_populates="user", cascade="all,delete")
    performance = relationship("StudentPerformance", back_populates="user", cascade="all,delete")

# ======================================================
# OTP MODEL
# ======================================================
class OTPSession(Base):
    __tablename__ = "otp_sessions"

    id = Column(Integer, primary_key=True)
    mobile_number = Column(String(15), nullable=False)
    otp_code = Column(String(6), nullable=False)

    dcet_reg_number = Column(String(50))
    college_name = Column(String(200))

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_verified = Column(Boolean, default=False)

# ======================================================
# SUBJECTS & UNITS
# ======================================================
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    short_name = Column(String(50))
    description = Column(Text)
    icon = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)

    units = relationship("Unit", back_populates="subject", cascade="all,delete")

class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"))
    unit_number = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="units")
    documents = relationship("Document", back_populates="unit", cascade="all,delete")

# ======================================================
# DOCUMENTS (PDF / RAG)
# ======================================================
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"))

    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)

    chunk_count = Column(Integer, default=0)
    is_processed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("Unit", back_populates="documents")

# ======================================================
# QUIZ ATTEMPTS
# ======================================================
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    unit_id = Column(Integer, ForeignKey("units.id"))

    difficulty = Column(String(20), nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)

    questions_data = Column(Text)
    answers_data = Column(Text)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    time_spent_seconds = Column(Integer, default=0)

    user = relationship("User", back_populates="quiz_attempts")

# ======================================================
# FLASHCARDS
# ======================================================
class FlashcardSession(Base):
    __tablename__ = "flashcard_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    unit_id = Column(Integer, ForeignKey("units.id"))

    total_cards = Column(Integer, nullable=False)
    cards_known = Column(Integer, default=0)
    cards_unknown = Column(Integer, default=0)

    flashcards_data = Column(Text)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    time_spent_seconds = Column(Integer, default=0)

    user = relationship("User", back_populates="flashcard_sessions")

# ======================================================
# STUDENT PERFORMANCE
# ======================================================
class StudentPerformance(Base):
    __tablename__ = "student_performance"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    unit_id = Column(Integer, ForeignKey("units.id"))

    total_attempted = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="performance")
    unit = relationship("Unit")

# ======================================================
# DB HELPERS
# ======================================================
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================
# SEED DATA
# ======================================================
def seed_initial_data():
    from passlib.hash import pbkdf2_sha256

    db = SessionLocal()
    try:
        if db.query(Subject).count() == 0:
            subjects = [
                ("Engineering Mathematics", "Math", "calculate"),
                ("Project Management Skills", "PMS", "assignment"),
                ("Fundamentals of Electrical & Electronics Engineering", "FEEE", "electrical_services"),
                ("Statistics & Analytics", "S&A", "analytics"),
                ("IT Skills", "IT", "computer"),
            ]

            for name, short, icon in subjects:
                subject = Subject(name=name, short_name=short, icon=icon)
                db.add(subject)
                db.flush()

                for i in range(1, 6):
                    db.add(Unit(
                        subject_id=subject.id,
                        unit_number=i,
                        name=f"Unit {i}",
                        description=f"Unit {i} of {name}"
                    ))

            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=pbkdf2_sha256.hash("admin123"),
                role=UserRole.ADMIN.value
            )
            db.add(admin)

            db.commit()
            print("✅ Initial PostgreSQL data seeded")

    except Exception as e:
        db.rollback()
        print("❌ Seed error:", e)
    finally:
        db.close()

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    init_db()
    seed_initial_data()
    print("✅ PostgreSQL database initialized successfully")
