from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PCMetric(Base):
    __tablename__ = "pc_metrics"

    id = Column(Integer, primary_key=True, index=True)
    pc_id = Column(Integer, ForeignKey("computers.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    cpu_percent = Column(Float, nullable=False, default=0.0)
    ram_percent = Column(Float, nullable=False, default=0.0)
    disk_percent = Column(Float, nullable=False, default=0.0)
    gpu_percent = Column(Float, nullable=True)
    gpu_memory = Column(Float, nullable=True)
    network_rx = Column(BigInteger, nullable=False, default=0)
    network_tx = Column(BigInteger, nullable=False, default=0)

    computer = relationship("Computer", back_populates="metrics")
    session = relationship("Session", back_populates="metrics")
