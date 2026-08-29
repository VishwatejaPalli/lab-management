from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class SessionSoftware(Base):
    __tablename__ = "session_software"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    software_id = Column(Integer, ForeignKey("software.id"), nullable=False)

    __table_args__ = (UniqueConstraint("session_id", "software_id"),)

    session = relationship("Session", back_populates="software_used")
    software = relationship("Software", back_populates="session_software")
