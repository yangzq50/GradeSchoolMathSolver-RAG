"""Database models for storing math problems and answers"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class MathProblem(Base):
    """Model for storing math problems"""
    __tablename__ = "math_problems"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_text = Column(String, nullable=False)
    problem_type = Column(String, nullable=False)  # addition, subtraction, multiplication, division
    correct_answer = Column(Float, nullable=False)
    difficulty = Column(Integer, default=1)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)

class Answer(Base):
    """Model for tracking student answers"""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, nullable=False)
    user_answer = Column(Float, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_taken = Column(Float, nullable=True)  # seconds
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
