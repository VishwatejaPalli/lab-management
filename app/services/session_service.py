from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.models.session_software import SessionSoftware
from app.models.computer import Computer
from app.models.user import User
from app.models.activity_type import ActivityType
from app.models.course import Course
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.research import Research


async def start_session(
    db: AsyncSession,
    student_id: int,
    computer_id: int,
    activity_type_id: int,
    course_id: Optional[int] = None,
    experiment_id: Optional[int] = None,
    project_id: Optional[int] = None,
    research_id: Optional[int] = None,
) -> Session:
    # Check if student already has an active session
    existing = await db.execute(
        select(Session).where(
            and_(Session.student_id == student_id, Session.end_time.is_(None))
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("You already have an active session. Stop it first.")

    # Check if computer is available
    computer = await db.get(Computer, computer_id)
    if not computer:
        raise ValueError("Computer not found.")
    if computer.status == "in_use":
        raise ValueError(f"{computer.hostname} is currently in use.")
    if computer.status == "offline":
        raise ValueError(f"{computer.hostname} is offline.")

    # Create session
    session = Session(
        student_id=student_id,
        computer_id=computer_id,
        activity_type_id=activity_type_id,
        course_id=course_id,
        experiment_id=experiment_id,
        project_id=project_id,
        research_id=research_id,
    )
    db.add(session)

    # Mark computer as in_use
    computer.status = "in_use"
    await db.flush()
    return session


async def stop_session(
    db: AsyncSession,
    session_id: int,
    software_ids: List[int],
    notes: Optional[str] = None,
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

    # Record software used
    for sw_id in software_ids:
        db.add(SessionSoftware(session_id=session_id, software_id=sw_id))

    # Free the computer
    computer = await db.get(Computer, session.computer_id)
    if computer:
        computer.status = "available"

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
            selectinload(Session.software_used).selectinload(SessionSoftware.software),
        )
        .where(Session.student_id == student_id)
        .order_by(Session.start_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """Get admin dashboard statistics."""
    # Total computers
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

    # Today's usage
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_hours = (await db.execute(
        select(func.coalesce(func.sum(Session.duration_minutes), 0))
        .where(Session.start_time >= today_start)
    )).scalar() or 0

    # Active sessions
    active_sessions_count = (await db.execute(
        select(func.count(Session.id)).where(Session.end_time.is_(None))
    )).scalar() or 0

    # Total sessions today
    total_sessions_today = (await db.execute(
        select(func.count(Session.id)).where(Session.start_time >= today_start)
    )).scalar() or 0

    return {
        "total_pcs": total_pcs,
        "active_pcs": active_pcs,
        "available_pcs": available_pcs,
        "offline_pcs": offline_pcs,
        "today_usage_hours": round(today_hours / 60, 1),
        "active_sessions": active_sessions_count,
        "total_sessions_today": total_sessions_today,
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
            selectinload(Session.software_used).selectinload(SessionSoftware.software),
        )
        .order_by(Session.start_time.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
