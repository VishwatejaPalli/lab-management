from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.agent_service import (
    authenticate_agent,
    ingest_heartbeat,
    ingest_metric,
    ingest_application_usage,
    confirm_session_presence,
)

router = APIRouter(prefix="/agent", tags=["agent"])


class HeartbeatPayload(BaseModel):
    pc_id: int
    hostname: str
    agent_version: Optional[str] = None
    os: Optional[str] = None
    ip_address: Optional[str] = None


class MetricPayload(BaseModel):
    pc_id: int
    session_id: Optional[int] = None
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    gpu_percent: Optional[float] = None
    gpu_memory: Optional[float] = None
    network_rx: int = 0
    network_tx: int = 0


class AppUsagePayload(BaseModel):
    pc_id: int
    session_id: int
    application_name: str
    process_name: str
    started_at: datetime
    ended_at: Optional[datetime] = None


class PresencePayload(BaseModel):
    pc_id: int
    session_id: int
    student_id: int


@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatPayload,
    db: AsyncSession = Depends(get_db),
    x_agent_key: Optional[str] = Header(None),
):
    try:
        await authenticate_agent(db, payload.pc_id, x_agent_key)
        agent = await ingest_heartbeat(
            db,
            pc_id=payload.pc_id,
            hostname=payload.hostname,
            agent_version=payload.agent_version,
            os_name=payload.os,
            ip_address=payload.ip_address,
        )
        return {"status": "ok", "agent_id": agent.id, "last_seen": agent.last_seen}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/metrics")
async def metrics(
    payload: MetricPayload,
    db: AsyncSession = Depends(get_db),
    x_agent_key: Optional[str] = Header(None),
):
    try:
        await authenticate_agent(db, payload.pc_id, x_agent_key)
        metric = await ingest_metric(
            db,
            pc_id=payload.pc_id,
            session_id=payload.session_id,
            cpu_percent=payload.cpu_percent,
            ram_percent=payload.ram_percent,
            disk_percent=payload.disk_percent,
            gpu_percent=payload.gpu_percent,
            gpu_memory=payload.gpu_memory,
            network_rx=payload.network_rx,
            network_tx=payload.network_tx,
        )
        return {"status": "ok", "metric_id": metric.id, "timestamp": metric.timestamp}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/application")
async def application_usage(
    payload: AppUsagePayload,
    db: AsyncSession = Depends(get_db),
    x_agent_key: Optional[str] = Header(None),
):
    try:
        await authenticate_agent(db, payload.pc_id, x_agent_key)
        usage = await ingest_application_usage(
            db,
            session_id=payload.session_id,
            application_name=payload.application_name,
            process_name=payload.process_name,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
        )
        return {"status": "ok", "application_usage_id": usage.id}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/presence")
async def presence(
    payload: PresencePayload,
    db: AsyncSession = Depends(get_db),
    x_agent_key: Optional[str] = Header(None),
):
    try:
        await authenticate_agent(db, payload.pc_id, x_agent_key)
        session = await confirm_session_presence(
            db,
            session_id=payload.session_id,
            student_id=payload.student_id,
            computer_id=payload.pc_id,
        )
        return {"status": "ok", "session_id": session.id, "presence_confirmed_at": session.presence_confirmed_at}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
