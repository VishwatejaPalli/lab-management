from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.session_software import SessionSoftware
from app.models.computer import Computer
from app.models.pc_assignment import PCAssignment
from app.models.pc_agent import PCAgent
from app.models.lab_entry import LabEntry
from app.models.pc_metric import PCMetric
from app.models.application_usage import ApplicationUsage
from app.services.operations_service import (
    validate_pc_assignment,
    get_open_lab_entry_for_student,
)


async def start_session(
    db: AsyncSession,
    student_id: int,
    computer_id: int,
    activity_type_id: int,
    course_id: Optional[int] = None,
    experiment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    research_id: Optional[int] = None,
    started_by_agent: bool = False,
) -> Session:
    existing = await db.execute(
        select(Session).where(and_(Session.student_id == student_id, Session.end_time.is_(None)))
    )
    if existing.scalar_one_or_none():
        raise ValueError("You already have an active session. Stop it first.")

    computer = await db.get(Computer, computer_id)
    if not computer:
        raise ValueError("Computer not found.")
    if computer.status == "in_use":
        raise ValueError(f"{computer.hostname} is currently in use.")
    if computer.status == "offline":
        raise ValueError(f"{computer.hostname} is offline.")

    assignment = await validate_pc_assignment(db, student_id, computer_id)
    entry = await get_open_lab_entry_for_student(db, student_id)

    session = Session(
        student_id=student_id,
        computer_id=computer_id,
        activity_type_id=activity_type_id,
        course_id=course_id,
        experiment_id=experiment_id,
        project_id=project_id,
        research_id=research_id,
        assignment_id=assignment.id,
        lab_entry_id=entry.id if entry else None,
        started_by_agent=started_by_agent,
    )
    db.add(session)

    assignment.session_id = session.id
    computer.status = "in_use"
    computer.realtime_status = "in_use"
    await db.flush()

    assignment.session_id = session.id
    await db.flush()
    return session


async def stop_session(
    db: AsyncSession,
    session_id: int,
    software_ids: List[int],
    notes: Optional[str] = None,
    ended_by_agent: bool = False,
) -> Session:
    session = await db.get(Session, session_id)
    if not session:
        raise ValueError("Session not found.")
    if session.end_time:
        raise ValueError("Session already ended.")

    now = datetime.now(timezone.utc)
    session.end_time = now
    session.duration_minutes = int((now - session.start_time).total_seconds() / 60)
    session.notes = notes
    session.ended_by_agent = ended_by_agent

    for sw_id in software_ids:
        db.add(SessionSoftware(session_id=session_id, software_id=sw_id))

    computer = await db.get(Computer, session.computer_id)
    if computer:
        computer.status = "available"
        computer.realtime_status = "online"

    if session.assignment_id:
        assignment = await db.get(PCAssignment, session.assignment_id)
        if assignment and assignment.released_at is None:
            assignment.released_at = now
            assignment.status = "released"

    await db.flush()
    return session


async def get_active_session(db: AsyncSession, student_id: int) -> Optional[Session]:
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.computer),
            selectinload(Session.activity_type),
            selectinload(Session.course),
            selectinload(Session.experiment),
            selectinload(Session.project),
            selectinload(Session.research),
            selectinload(Session.assignment).selectinload(PCAssignment.computer),
            selectinload(Session.lab_entry).selectinload(LabEntry.lab),
            selectinload(Session.software_used).selectinload(SessionSoftware.software),
        )
        .where(and_(Session.student_id == student_id, Session.end_time.is_(None)))
    )
    return result.scalar_one_or_none()


async def get_student_sessions(db: AsyncSession, student_id: int, limit: int = 50) -> List[Session]:
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.computer),
            selectinload(Session.activity_type),
            selectinload(Session.course),
            selectinload(Session.experiment),
            selectinload(Session.project),
            selectinload(Session.research),
            selectinload(Session.assignment).selectinload(PCAssignment.computer),
            selectinload(Session.lab_entry).selectinload(LabEntry.lab),
            selectinload(Session.software_used).selectinload(SessionSoftware.software),
            selectinload(Session.application_usage),
        )
        .where(Session.student_id == student_id)
        .order_by(Session.start_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_dashboard_stats(db: AsyncSession) -> dict:
    total_pcs = (await db.execute(select(func.count(Computer.id)))).scalar() or 0
    active_pcs = (await db.execute(
        select(func.count(Computer.id)).where(Computer.status == "in_use")
    )).scalar() or 0
    available_pcs = (await db.execute(
        select(func.count(Computer.id)).where(Computer.status == "available")
    )).scalar() or 0
    offline_pcs = (await db.execute(
        select(func.count(Computer.id)).where(Computer.status == "offline")
    )).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_minutes = (await db.execute(
        select(func.coalesce(func.sum(Session.duration_minutes), 0))
        .where(Session.start_time >= today_start)
    )).scalar() or 0

    active_sessions_count = (await db.execute(
        select(func.count(Session.id)).where(Session.end_time.is_(None))
    )).scalar() or 0

    total_sessions_today = (await db.execute(
        select(func.count(Session.id)).where(Session.start_time >= today_start)
    )).scalar() or 0

    stale_agents = (await db.execute(
        select(func.count(PCAgent.id)).where(PCAgent.status == "stale")
    )).scalar() or 0

    metrics_today = (await db.execute(
        select(func.count(PCMetric.id)).where(PCMetric.timestamp >= today_start)
    )).scalar() or 0

    active_apps = (await db.execute(
        select(func.count(ApplicationUsage.id)).where(ApplicationUsage.is_active.is_(True))
    )).scalar() or 0

    open_entries = (await db.execute(
        select(func.count(LabEntry.id)).where(LabEntry.exit_time.is_(None))
    )).scalar() or 0

    return {
        "total_pcs": total_pcs,
        "active_pcs": active_pcs,
        "available_pcs": available_pcs,
        "offline_pcs": offline_pcs,
        "today_usage_hours": round(today_minutes / 60, 1),
        "active_sessions": active_sessions_count,
        "total_sessions_today": total_sessions_today,
        "stale_agents": stale_agents,
        "metrics_today": metrics_today,
        "active_apps": active_apps,
        "open_entries": open_entries,
    }


async def get_all_sessions(db: AsyncSession, limit: int = 100) -> List[Session]:
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.student),
            selectinload(Session.computer),
            selectinload(Session.activity_type),
            selectinload(Session.course),
            selectinload(Session.experiment),
            selectinload(Session.project),
            selectinload(Session.research),
            selectinload(Session.assignment).selectinload(PCAssignment.computer),
            selectinload(Session.lab_entry).selectinload(LabEntry.lab),
            selectinload(Session.software_used).selectinload(SessionSoftware.software),
            selectinload(Session.metrics),
            selectinload(Session.application_usage),
        )
        .order_by(Session.start_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
