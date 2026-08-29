from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Computer(Base):
    __tablename__ = "computers"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(50), unique=True, nullable=False)
    lab = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    status = Column(String(20), default="available")
    specs = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("Session", back_populates="computer")
