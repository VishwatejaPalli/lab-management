from sqlalchemy import Column, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    computer_id = Column(Integer, ForeignKey("computers.id"), nullable=False)
    activity_type_id = Column(Integer, ForeignKey("activity_types.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    research_id = Column(Integer, ForeignKey("research.id"))
    assignment_id = Column(Integer, ForeignKey("pc_assignments.id"), nullable=True)
    lab_entry_id = Column(Integer, ForeignKey("lab_entries.id"), nullable=True)
    presence_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    started_by_agent = Column(Boolean, nullable=False, default=False)
    ended_by_agent = Column(Boolean, nullable=False, default=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="sessions")
    computer = relationship("Computer", back_populates="sessions")
    activity_type = relationship("ActivityType", back_populates="sessions")
    course = relationship("Course", back_populates="sessions")
    experiment = relationship("Experiment", back_populates="sessions")
    project = relationship("Project", back_populates="sessions")
    research = relationship("Research", back_populates="sessions")
    software_used = relationship("SessionSoftware", back_populates="session")
    assignment = relationship("PCAssignment", back_populates="session", foreign_keys=[assignment_id], post_update=True)
    lab_entry = relationship("LabEntry", back_populates="sessions")
    metrics = relationship("PCMetric", back_populates="session")
    application_usage = relationship("ApplicationUsage", back_populates="session")
