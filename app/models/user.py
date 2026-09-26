from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    department = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sessions = relationship("Session", back_populates="student")
    projects_created = relationship("Project", back_populates="created_by_user")
    supervised_research = relationship("Research", back_populates="supervisor")
    pc_assignments = relationship("PCAssignment", back_populates="student")
    lab_entries = relationship("LabEntry", back_populates="student")
    lab_classes = relationship("LabClass", back_populates="faculty")
