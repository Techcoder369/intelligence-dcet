"""
Subject and Unit Routes
Handles subject and unit listing
"""
from flask import Blueprint, app, request, jsonify
from backend.models.database import SessionLocal, Subject, Unit

subject_bp = Blueprint('subjects', __name__, url_prefix='/subjects')



@subject_bp.route('', methods=['GET'])
def get_subjects():
    """Get all subjects"""
    db = SessionLocal()
    try:
        subjects = db.query(Subject).all()
        
        result = []
        for subject in subjects:
            result.append({
                "id": subject.id,
                "name": subject.name,
                "short_name": subject.short_name,
                "description": subject.description,
                "icon": subject.icon
            })
        
        return jsonify({
            "success": True,
            "subjects": result
        }), 200
    finally:
        db.close()

@subject_bp.route('/<int:subject_id>', methods=['GET'])
def get_subject(subject_id):
    """Get a specific subject with its units"""
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        
        if not subject:
            return jsonify({"success": False, "message": "Subject not found"}), 404
        
        units = db.query(Unit).filter(Unit.subject_id == subject_id).order_by(Unit.unit_number).all()
        
        return jsonify({
            "success": True,
            "subject": {
                "id": subject.id,
                "name": subject.name,
                "short_name": subject.short_name,
                "description": subject.description,
                "icon": subject.icon
            },
            "units": [
                {
                    "id": unit.id,
                    "unit_number": unit.unit_number,
                    "name": unit.name,
                    "description": unit.description
                }
                for unit in units
            ]
        }), 200
    finally:
        db.close()

@subject_bp.route('/<int:subject_id>/units', methods=['GET'])
def get_subject_units(subject_id):
    """Get all units for a subject"""
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        
        if not subject:
            return jsonify({"success": False, "message": "Subject not found"}), 404
        
        units = db.query(Unit).filter(Unit.subject_id == subject_id).order_by(Unit.unit_number).all()
        
        return jsonify({
            "success": True,
            "subject_name": subject.name,
            "units": [
                {
                    "id": unit.id,
                    "unit_number": unit.unit_number,
                    "name": unit.name,
                    "description": unit.description
                }
                for unit in units
            ]
        }), 200
    finally:
        db.close()
