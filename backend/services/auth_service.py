"""
Authentication Service
Handles JWT token management for students and admin login
"""
import os
from datetime import datetime, timedelta
import jwt
from passlib.hash import pbkdf2_sha256
from backend.models.database import SessionLocal, User

SECRET_KEY = os.environ.get('SESSION_SECRET', 'dcet-quiz-secret-key-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def student_register(email: str, password: str, username: str, dcet_reg_number: str, college_name: str, mobile_number: str = None):
    """Register a new student"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"success": False, "message": "Email already registered"}
        
        user = User(
            email=email,
            password_hash=pbkdf2_sha256.hash(password),
            dcet_reg_number=dcet_reg_number,
            username=username,
            college_name=college_name,
            mobile_number=mobile_number,
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        token = create_access_token(user.id, user.role)
        return {
            "success": True, 
            "message": "Registration successful", 
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()

def student_login(email: str, password: str):
    """Student login with email and password"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == email,
            User.role == "student"
        ).first()
        
        if not user:
            print(f"Login failed: User with email {email} not found")
            return {"success": False, "message": "Invalid email or password"}
            
        if not user.password_hash or not pbkdf2_sha256.verify(password, user.password_hash):
            print(f"Login failed: Password mismatch for {email}")
            return {"success": False, "message": "Invalid email or password"}
        
        token = create_access_token(user.id, user.role)
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "dcet_reg_number": user.dcet_reg_number,
                "college_name": user.college_name,
                "role": user.role
            }
        }
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()

def admin_login(username: str, password: str):
    """
    Admin login with username and password
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.username == username,
            User.role == "admin"
        ).first()
        
        if not user:
            print(f"Admin login failed: User {username} not found")
            return {"success": False, "message": "Invalid credentials"}
            
        if not user.password_hash or not pbkdf2_sha256.verify(password, user.password_hash):
            print(f"Admin login failed: Password mismatch for {username}")
            return {"success": False, "message": "Invalid credentials"}
        
        token = create_access_token(user.id, user.role)
        
        return {
            "success": True,
            "message": "Admin login successful",
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }
    except Exception as e:
        print(f"Admin login error: {str(e)}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()

def create_access_token(user_id: int, role: str):
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"success": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "message": "Token expired"}
    except jwt.InvalidTokenError:
        return {"success": False, "message": "Invalid token"}

def get_current_user(token: str):
    """Get current user from token"""
    result = verify_token(token)
    if not result["success"]:
        return None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == result["payload"]["user_id"]).first()
        if user:
            return {
                "id": user.id,
                "mobile_number": user.mobile_number,
                "username": user.username,
                "dcet_reg_number": user.dcet_reg_number,
                "college_name": user.college_name,
                "branch": user.branch,
                "semester": user.semester,
                "target_dcet_year": user.target_dcet_year,
                "username": user.username,
                "role": user.role
            }
        return None
    finally:
        db.close()
