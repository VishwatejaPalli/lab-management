from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class LabEntry(Base):
    __tablename__ = "lab_entries"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("pc_assignments.id"), nullable=True)
    entry_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    method = Column(String(30), nullable=False, default="manual")
    status = Column(String(20), nullable=False, default="in_lab")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="lab_entries")
    lab = relationship("Lab", back_populates="lab_entries")
    assignment = relationship("PCAssignment", back_populates="lab_entries")
    sessions = relationship("Session", back_populates="lab_entry")
