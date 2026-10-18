import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """User entity (simplified for MVP, ready for full auth)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, index=True, nullable=False, default="guest")
    email = Column(String(128), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")


class Submission(Base):
    """Source code submission record."""
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    language = Column(String(32), default="java", nullable=False)
    source_code = Column(Text, nullable=False)
    compile_success = Column(Boolean, default=False, nullable=False)
    compilation_time = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    user = relationship("User", back_populates="submissions")
    errors = relationship("CompilerErrorRecord", back_populates="submission", cascade="all, delete-orphan")
    warnings = relationship("StaticWarningRecord", back_populates="submission", cascade="all, delete-orphan")


class CompilerErrorRecord(Base):
    """Parsed compiler error associated with a submission."""
    __tablename__ = "compiler_errors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)
    category = Column(String(64), nullable=False)
    subcategory = Column(String(64), nullable=True)
    severity = Column(String(16), default="error", nullable=False)
    line = Column(Integer, nullable=True)
    column = Column(Integer, nullable=True)
    compiler_message = Column(Text, nullable=False)
    raw_snippet = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="errors")
    analysis = relationship("AnalysisRecord", back_populates="error", uselist=False, cascade="all, delete-orphan")


class AnalysisRecord(Base):
    """Explanation and fix generated for an error."""
    __tablename__ = "error_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    error_id = Column(String(36), ForeignKey("compiler_errors.id"), nullable=False)
    title = Column(String(256), nullable=False)
    explanation = Column(Text, nullable=False)
    cause = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=False)
    corrected_code = Column(Text, nullable=True)
    prevention_tip = Column(Text, nullable=False)
    concept_to_learn = Column(String(128), nullable=True)
    ai_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    error = relationship("CompilerErrorRecord", back_populates="analysis")


class StaticWarningRecord(Base):
    """Static analysis warning detected in submission."""
    __tablename__ = "static_warnings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)
    rule_id = Column(String(64), nullable=False)
    severity = Column(String(16), default="warning", nullable=False)
    line = Column(Integer, nullable=True)
    message = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="warnings")
