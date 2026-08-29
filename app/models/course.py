from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(50))
    semester = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    experiments = relationship("Experiment", back_populates="course")
    projects = relationship("Project", back_populates="course")
    sessions = relationship("Session", back_populates="course")
