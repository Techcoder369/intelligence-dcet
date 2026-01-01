from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from .database import Base

class LoginLog(Base):
    __tablename__ = "login_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    role = Column(String(20))
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    success = Column(Boolean, default=True)
    login_time = Column(DateTime, default=datetime.utcnow)
