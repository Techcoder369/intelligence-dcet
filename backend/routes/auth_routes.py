"""
Authentication Routes
Handles student registration, login, and admin login
"""

from flask import Blueprint, request, jsonify
from backend.services.auth_service import (
    student_login,
    student_register,
    admin_login,
    get_current_user
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ======================================================
# STUDENT LOGIN
# ======================================================
@auth_bp.route('/login', methods=['POST'])
def login_route():
    """Student login with email and password"""
    data = request.get_json() or {}

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    result = student_login(email, password)

    if result.get("success"):
        return jsonify(result), 200
    return jsonify(result), 401


# ======================================================
# STUDENT REGISTER  ✅ FIXED
# ======================================================
@auth_bp.route('/register', methods=['POST'])
def register_route():
    """Register a new student"""
    data = request.get_json() or {}

    username = data.get('username', '').strip()           # ✅ NEW
    email = data.get('email', '').strip()
    password = data.get('password', '')
    mobile = data.get('mobile_number', '').strip()        # ✅ NEW
    reg_no = data.get('dcet_reg_number', '').strip()
    college = data.get('college_name', '').strip()

    if not all([username, email, password, mobile, reg_no, college]):
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    result = student_register(
        username=username,
        email=email,
        password=password,
        mobile_number=mobile,
        dcet_reg_number=reg_no,
        college_name=college
    )

    if result.get("success"):
        return jsonify(result), 200

    return jsonify(result), 400


# ======================================================
# ADMIN LOGIN
# ======================================================
@auth_bp.route('/admin-login', methods=['POST'])
def admin_login_route():
    """Admin login with username and password"""
    data = request.get_json() or {}

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    result = admin_login(username, password)

    if result.get("success"):
        return jsonify(result), 200
    return jsonify(result), 401


# ======================================================
# VERIFY TOKEN (PROFILE DATA SOURCE)
# ======================================================
@auth_bp.route('/verify-token', methods=['GET'])
def verify_token_route():
    """Verify JWT token and return user info"""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return jsonify({
            "success": False,
            "message": "No token provided"
        }), 401

    token = auth_header.split(' ')[1]
    user = get_current_user(token)

    if user:
        return jsonify({
            "success": True,
            "user": user
        }), 200

    return jsonify({
        "success": False,
        "message": "Invalid token"
    }), 401
