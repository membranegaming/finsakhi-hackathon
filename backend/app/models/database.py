from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from pathlib import Path

# Get database path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "data" / "finsakhi.db"

# Create data directory if doesn't exist
DATABASE_PATH.parent.mkdir(exist_ok=True)

# SQLite connection string
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine - SQLite specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
    echo=False  # Set to True to see SQL queries (helpful for debugging)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# DATABASE MODELS
# ============================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)  # Optional during OTP signup
    password_hash = Column(String(255), nullable=True)  # Not used with OTP
    language = Column(String(10), default="en")
    otp = Column(String(6), nullable=True)  # Store current OTP
    otp_expiry = Column(DateTime, nullable=True)  # OTP expiration time
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    financial_profile = relationship("FinancialProfile", back_populates="user", uselist=False)
    gamification = relationship("UserGamification", back_populates="user", uselist=False)
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    learning_progress = relationship("LearningProgress", back_populates="user")
    investments = relationship("Investment", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")

class FinancialProfile(Base):
    __tablename__ = "financial_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    monthly_income = Column(Float, nullable=True)
    income_source = Column(String(100), nullable=True)  # salary, business, farming, etc.
    risk_appetite = Column(String(20), default="medium")
    occupation = Column(String(100), nullable=True)
    marital_status = Column(String(20), nullable=True)  # married/unmarried
    children_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="financial_profile")

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="in_progress")  # in_progress, completed
    current_step = Column(Integer, default=0)  # Current question index
    profile_data = Column(Text, nullable=True)  # JSON: collected profile info
    questions_asked = Column(Text, nullable=True)  # JSON: list of questions + answers
    total_score = Column(Integer, default=0)
    literacy_level = Column(String(20), nullable=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class LiteracyAssessment(Base):
    __tablename__ = "literacy_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_score = Column(Integer, nullable=False)
    literacy_level = Column(String(20), nullable=False)
    budgeting_score = Column(Integer)
    investing_score = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)

class Module(Base):
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    pillar = Column(String(50), nullable=False)  # savings, credit, investments, small_business
    level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    title_en = Column(String(255), nullable=False)
    title_hi = Column(String(255), nullable=False)
    description_en = Column(Text)
    description_hi = Column(Text)
    order_index = Column(Integer, default=0)
    
    lessons = relationship("Lesson", back_populates="module")

class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    title_en = Column(String(255), nullable=False)
    title_hi = Column(String(255), nullable=False)
    # Story-based audio script
    story_en = Column(Text, nullable=False)
    story_hi = Column(Text, nullable=False)
    # Key takeaway
    takeaway_en = Column(Text, nullable=True)
    takeaway_hi = Column(Text, nullable=True)
    # Scenario question (JSON: question, options with correct flag)
    scenario_en = Column(Text, nullable=True)  # JSON
    scenario_hi = Column(Text, nullable=True)  # JSON
    # Tool suggestion (budget_tool, emi_calculator, savings_goal, etc.)
    tool_suggestion = Column(String(50), nullable=True)
    xp_reward = Column(Integer, default=10)
    order_index = Column(Integer, default=0)
    
    module = relationship("Module", back_populates="lessons")
    progress = relationship("LearningProgress", back_populates="lesson")

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    scenario_correct = Column(Boolean, nullable=True)  # Did user pick right scenario choice?
    tool_used = Column(Boolean, default=False)  # Did user use the suggested tool?
    personalized_content = Column(Text, nullable=True)  # JSON: LLM-generated personalized lesson
    
    user = relationship("User", back_populates="learning_progress")
    lesson = relationship("Lesson", back_populates="progress")

class UserFinancialHealth(Base):
    __tablename__ = "user_financial_health"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    health_score = Column(Integer, default=0)  # 0-100
    lessons_completed = Column(Integer, default=0)
    scenarios_correct = Column(Integer, default=0)
    scenarios_total = Column(Integer, default=0)
    tools_used = Column(Integer, default=0)
    unsafe_choices = Column(Integer, default=0)
    current_level = Column(String(20), default="beginner")  # beginner/intermediate/advanced
    beginner_unlocked = Column(Boolean, default=True)
    intermediate_unlocked = Column(Boolean, default=False)
    advanced_unlocked = Column(Boolean, default=False)
    revision_mode = Column(Boolean, default=False)  # Smart lock: paused for revision
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserGamification(Base):
    __tablename__ = "user_gamification"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    total_xp = Column(Integer, default=0)
    current_level = Column(Integer, default=1)
    login_streak = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="gamification")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    xp_reward = Column(Integer, default=100)
    badge_icon = Column(String(255))

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    earned_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    total_invested = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    total_returns = Column(Float, default=0.0)
    
    user = relationship("User", back_populates="portfolio")

class Investment(Base):
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    asset_symbol = Column(String(50), nullable=False)
    asset_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="investments")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_en = Column(Text, nullable=False)
    question_hi = Column(Text, nullable=False)
    options_en = Column(Text, nullable=False)  # JSON string
    options_hi = Column(Text, nullable=False)  # JSON string
    correct_answer = Column(Integer, nullable=False)
    category = Column(String(50))


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    conversation_id = Column(String(50), index=True, nullable=False)  # Groups messages into conversations
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    context_snapshot = Column(Text, nullable=True)  # JSON: user context at time of message
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")


# ============================================
# CREATE ALL TABLES
# ============================================
def init_db():
    """Call this to create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created in SQLite!")
    print(f"📁 Database location: {DATABASE_PATH}")

if __name__ == "__main__":
    init_db()