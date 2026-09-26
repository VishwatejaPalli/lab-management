from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Computer(Base):
    __tablename__ = "computers"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(50), unique=True, nullable=False)
    lab = Column(String(50), nullable=False)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True, index=True)
    ip_address = Column(String(45))
    status = Column(String(20), default="available")
    realtime_status = Column(String(20), default="unknown", nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    specs = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("Session", back_populates="computer")
    lab_ref = relationship("Lab", back_populates="computers")
    agent = relationship("PCAgent", back_populates="computer", uselist=False)
    metrics = relationship("PCMetric", back_populates="computer")
    pc_assignments = relationship("PCAssignment", back_populates="computer")
