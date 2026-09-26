from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PCAgent(Base):
    __tablename__ = "pc_agents"

    id = Column(Integer, primary_key=True, index=True)
    pc_id = Column(Integer, ForeignKey("computers.id"), nullable=False, unique=True)
    hostname = Column(String(100), nullable=False)
    agent_version = Column(String(50), nullable=True)
    auth_token_hash = Column(String(128), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="inactive")
    os = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    computer = relationship("Computer", back_populates="agent")
