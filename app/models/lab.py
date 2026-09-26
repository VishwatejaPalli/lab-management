from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Lab(Base):
    __tablename__ = "labs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    room_number = Column(String(30), nullable=False)
    building = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False, default=40)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    computers = relationship("Computer", back_populates="lab_ref")
    lab_entries = relationship("LabEntry", back_populates="lab")
    lab_classes = relationship("LabClass", back_populates="lab")
