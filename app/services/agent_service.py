import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pc_agent import PCAgent
from app.models.computer import Computer
from app.models.pc_metric import PCMetric
from app.models.application_usage import ApplicationUsage
from app.models.session import Session
from app.services.operations_service import get_active_assignment_for_student
from app.config import get_settings


def hash_agent_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def authenticate_agent(db: AsyncSession, pc_id: int, raw_key: Optional[str]) -> PCAgent:
    result = await db.execute(select(PCAgent).where(PCAgent.pc_id == pc_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise ValueError("Agent not registered for this PC.")

    if agent.auth_token_hash:
        if not raw_key:
            raise ValueError("Missing agent key.")
        if hash_agent_key(raw_key) != agent.auth_token_hash:
            raise ValueError("Invalid agent key.")
    return agent


async def mark_stale_agents(db: AsyncSession) -> None:
    settings = get_settings()
    stale_before = datetime.now(timezone.utc) - timedelta(minutes=settings.AGENT_STALE_MINUTES)
    stale_agents = (
        await db.execute(
            select(PCAgent).where(and_(PCAgent.last_seen.is_not(None), PCAgent.last_seen < stale_before))
        )
    ).scalars().all()

    for agent in stale_agents:
        agent.status = "stale"
        if agent.computer:
            agent.computer.realtime_status = "offline"
            if agent.computer.status != "in_use":
                agent.computer.status = "offline"


async def ingest_heartbeat(
    db: AsyncSession,
    pc_id: int,
    hostname: str,
    agent_version: Optional[str],
    os_name: Optional[str],
    ip_address: Optional[str],
) -> PCAgent:
    result = await db.execute(select(PCAgent).where(PCAgent.pc_id == pc_id))
    agent = result.scalar_one_or_none()
    computer = await db.get(Computer, pc_id)
    if not computer:
        raise ValueError("Computer not found.")

    now = datetime.now(timezone.utc)
    if not agent:
        agent = PCAgent(pc_id=pc_id, hostname=hostname, status="active")
        db.add(agent)

    agent.hostname = hostname
    agent.agent_version = agent_version
    agent.os = os_name
    agent.ip_address = ip_address
    agent.last_seen = now
    agent.status = "active"

    computer.last_seen_at = now
    computer.realtime_status = "online"
    if computer.status == "offline":
        computer.status = "available"

    await mark_stale_agents(db)
    await db.flush()
    return agent


async def ingest_metric(
    db: AsyncSession,
    pc_id: int,
    session_id: Optional[int],
    cpu_percent: float,
    ram_percent: float,
    disk_percent: float,
    gpu_percent: Optional[float],
    gpu_memory: Optional[float],
    network_rx: int,
    network_tx: int,
) -> PCMetric:
    metric = PCMetric(
        pc_id=pc_id,
        session_id=session_id,
        cpu_percent=cpu_percent,
        ram_percent=ram_percent,
        disk_percent=disk_percent,
        gpu_percent=gpu_percent,
        gpu_memory=gpu_memory,
        network_rx=network_rx,
        network_tx=network_tx,
    )
    db.add(metric)
    await db.flush()
    return metric


async def ingest_application_usage(
    db: AsyncSession,
    session_id: int,
    application_name: str,
    process_name: str,
    started_at: datetime,
    ended_at: Optional[datetime],
) -> ApplicationUsage:
    duration = None
    is_active = ended_at is None
    if ended_at:
        duration = int((ended_at - started_at).total_seconds())

    usage = ApplicationUsage(
        session_id=session_id,
        application_name=application_name,
        process_name=process_name,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        is_active=is_active,
    )
    db.add(usage)
    await db.flush()
    return usage


async def confirm_session_presence(
    db: AsyncSession,
    session_id: int,
    student_id: int,
    computer_id: int,
) -> Session:
    session = await db.get(Session, session_id)
    if not session:
        raise ValueError("Session not found.")
    if session.student_id != student_id:
        raise ValueError("Session/student mismatch.")
    if session.computer_id != computer_id:
        raise ValueError("Session/PC mismatch.")

    assignment = await get_active_assignment_for_student(db, student_id)
    if assignment and assignment.pc_id != computer_id:
        raise ValueError("Assignment mismatch detected.")

    session.presence_confirmed_at = datetime.now(timezone.utc)
    await db.flush()
    return session


async def purge_old_metrics(db: AsyncSession, retention_days: int = 14) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    old_ids = (
        await db.execute(select(PCMetric.id).where(PCMetric.timestamp < cutoff).limit(10000))
    ).scalars().all()
    if not old_ids:
        return 0

    await db.execute(PCMetric.__table__.delete().where(PCMetric.id.in_(old_ids)))
    return len(old_ids)


async def get_latest_metric_map(db: AsyncSession) -> dict:
    subq = (
        select(PCMetric.pc_id, func.max(PCMetric.timestamp).label("max_ts"))
        .group_by(PCMetric.pc_id)
        .subquery()
    )
    rows = (
        await db.execute(
            select(PCMetric).join(subq, and_(PCMetric.pc_id == subq.c.pc_id, PCMetric.timestamp == subq.c.max_ts))
        )
    ).scalars().all()
    return {m.pc_id: m for m in rows}
