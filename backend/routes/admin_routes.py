"""
Admin Routes
Handles admin dashboard, subject/unit management, PDF upload, and analytics
"""
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
from werkzeug.utils import secure_filename
from backend.services.auth_service import verify_token
from backend.services.rag_service import rag_service
from backend.models.database import SessionLocal, User, Subject, Unit, Document, QuizAttempt, FlashcardSession

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {'pdf'}

def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "No token provided"}), 401
        
        token = auth_header.split(' ')[1]
        result = verify_token(token)
        
        if not result["success"]:
            return jsonify({"success": False, "message": result["message"]}), 401
        
        if result["payload"]["role"] != "admin":
            return jsonify({"success": False, "message": "Admin access required"}), 403
        
        request.user_id = result["payload"]["user_id"]
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/analytics', methods=['GET'])
@require_admin
def get_analytics():
    """Get admin analytics dashboard data"""
    db = SessionLocal()
    try:
        total_students = db.query(User).filter(User.role == "student").count()
        
        subjects = db.query(Subject).all()
        subject_stats = []
        
        for subject in subjects:
            quiz_count = db.query(QuizAttempt).filter(
                QuizAttempt.subject_id == subject.id
            ).count()
            
            flashcard_count = db.query(FlashcardSession).filter(
                FlashcardSession.subject_id == subject.id
            ).count()
            
            units = db.query(Unit).filter(Unit.subject_id == subject.id).all()
            unit_stats = []
            
            for unit in units:
                unit_quizzes = db.query(QuizAttempt).filter(
                    QuizAttempt.unit_id == unit.id
                ).count()
                
                doc_count = db.query(Document).filter(
                    Document.unit_id == unit.id,
                    Document.is_processed == True
                ).count()
                
                unit_stats.append({
                    "unit_id": unit.id,
                    "unit_name": unit.name,
                    "quiz_count": unit_quizzes,
                    "document_count": doc_count
                })
            
            subject_stats.append({
                "subject_id": subject.id,
                "subject_name": subject.name,
                "quiz_count": quiz_count,
                "flashcard_count": flashcard_count,
                "units": unit_stats
            })
        
        return jsonify({
            "success": True,
            "analytics": {
                "total_students": total_students,
                "total_quizzes": db.query(QuizAttempt).count(),
                "total_flashcard_sessions": db.query(FlashcardSession).count(),
                "total_documents": db.query(Document).filter(Document.is_processed == True).count(),
                "subjects": subject_stats
            }
        }), 200
    finally:
        db.close()

@admin_bp.route('/subjects', methods=['GET'])
@require_admin
def get_admin_subjects():
    """Get all subjects with units for admin"""
    db = SessionLocal()
    try:
        subjects = db.query(Subject).all()
        result = []
        
        for subject in subjects:
            units = db.query(Unit).filter(Unit.subject_id == subject.id).order_by(Unit.unit_number).all()
            
            unit_list = []
            for unit in units:
                doc_count = db.query(Document).filter(
                    Document.unit_id == unit.id,
                    Document.is_processed == True
                ).count()
                
                unit_list.append({
                    "id": unit.id,
                    "unit_number": unit.unit_number,
                    "name": unit.name,
                    "description": unit.description,
                    "document_count": doc_count
                })
            
            result.append({
                "id": subject.id,
                "name": subject.name,
                "short_name": subject.short_name,
                "description": subject.description,
                "icon": subject.icon,
                "units": unit_list
            })
        
        return jsonify({
            "success": True,
            "subjects": result
        }), 200
    finally:
        db.close()

@admin_bp.route('/subjects', methods=['POST'])
@require_admin
def create_subject():
    """Create a new subject"""
    data = request.get_json()
    
    name = data.get('name', '').strip()
    short_name = data.get('short_name', '').strip()
    description = data.get('description', '').strip()
    icon = data.get('icon', 'book').strip()
    
    if not name:
        return jsonify({"success": False, "message": "Subject name is required"}), 400
    
    db = SessionLocal()
    try:
        subject = Subject(
            name=name,
            short_name=short_name,
            description=description,
            icon=icon
        )
        db.add(subject)
        db.flush()
        
        for i in range(1, 6):
            unit = Unit(
                subject_id=subject.id,
                unit_number=i,
                name=f"Unit {i}",
                description=f"Unit {i} of {name}"
            )
            db.add(unit)
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Subject created successfully",
            "subject": {
                "id": subject.id,
                "name": subject.name,
                "short_name": subject.short_name,
                "description": subject.description,
                "icon": subject.icon
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

@admin_bp.route('/subjects/<int:subject_id>', methods=['PUT'])
@require_admin
def update_subject(subject_id):
    """Update a subject"""
    data = request.get_json()
    
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        
        if not subject:
            return jsonify({"success": False, "message": "Subject not found"}), 404
        
        if 'name' in data:
            subject.name = data['name']
        if 'short_name' in data:
            subject.short_name = data['short_name']
        if 'description' in data:
            subject.description = data['description']
        if 'icon' in data:
            subject.icon = data['icon']
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Subject updated successfully"
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

@admin_bp.route('/upload', methods=['POST'])
@require_admin
def upload_document():
    """Upload PDF document for a subject/unit"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['file']
    subject_id = request.form.get('subject_id')
    unit_id = request.form.get('unit_id')
    
    if not subject_id or not unit_id:
        return jsonify({"success": False, "message": "Subject and unit are required"}), 400
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Only PDF files are allowed"}), 400
    
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        
        if not subject or not unit:
            return jsonify({"success": False, "message": "Subject or unit not found"}), 404
        
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file.save(file_path)
        
        document = Document(
            unit_id=int(unit_id),
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path
        )
        db.add(document)
        db.flush()
        
        chunk_count = rag_service.ingest_document(
            file_path,
            int(subject_id),
            int(unit_id),
            document.id
        )
        
        document.chunk_count = chunk_count
        document.is_processed = chunk_count > 0
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": f"Document uploaded and processed. {chunk_count} chunks created.",
            "document": {
                "id": document.id,
                "filename": original_filename,
                "chunk_count": chunk_count
            }
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()

@admin_bp.route('/documents', methods=['GET'])
@require_admin
def get_documents():
    """Get all uploaded documents"""
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        
        result = []
        for doc in documents:
            unit = db.query(Unit).filter(Unit.id == doc.unit_id).first()
            subject = None
            if unit:
                subject = db.query(Subject).filter(Subject.id == unit.subject_id).first()
            
            result.append({
                "id": doc.id,
                "filename": doc.original_filename,
                "subject_name": subject.name if subject else "Unknown",
                "unit_name": unit.name if unit else "Unknown",
                "chunk_count": doc.chunk_count,
                "is_processed": doc.is_processed,
                "uploaded_at": doc.created_at.isoformat() if doc.created_at else None
            })
        
        return jsonify({
            "success": True,
            "documents": result
        }), 200
    finally:
        db.close()

@admin_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@require_admin
def delete_document(doc_id):
    """Delete a document"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        
        if not document:
            return jsonify({"success": False, "message": "Document not found"}), 404
        
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.delete(document)
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Document deleted successfully"
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()
