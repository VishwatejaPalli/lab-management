from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PCAssignment(Base):
    __tablename__ = "pc_assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    pc_id = Column(Integer, ForeignKey("computers.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active")

    student = relationship("User", back_populates="pc_assignments")
    computer = relationship("Computer", back_populates="pc_assignments")
    session = relationship("Session", back_populates="assignment", foreign_keys=[session_id])
    lab_entries = relationship("LabEntry", back_populates="assignment")
