from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Software(Base):
    __tablename__ = "software"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(50))
    category = Column(String(50))
    license_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session_software = relationship("SessionSoftware", back_populates="software")
