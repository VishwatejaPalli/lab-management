from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pc_assignment import PCAssignment
from app.models.lab_entry import LabEntry
from app.models.computer import Computer
from app.models.session import Session
from app.models.lab import Lab


async def get_active_assignment_for_student(db: AsyncSession, student_id: int) -> Optional[PCAssignment]:
    result = await db.execute(
        select(PCAssignment)
        .options(selectinload(PCAssignment.computer))
        .where(and_(PCAssignment.student_id == student_id, PCAssignment.released_at.is_(None)))
        .order_by(PCAssignment.assigned_at.desc())
    )
    return result.scalar_one_or_none()


async def get_active_assignment_for_pc(db: AsyncSession, pc_id: int) -> Optional[PCAssignment]:
    result = await db.execute(
        select(PCAssignment).where(and_(PCAssignment.pc_id == pc_id, PCAssignment.released_at.is_(None)))
    )
    return result.scalar_one_or_none()


async def validate_pc_assignment(db: AsyncSession, student_id: int, computer_id: int) -> PCAssignment:
    assignment = await get_active_assignment_for_student(db, student_id)
    if not assignment:
        raise ValueError("No active PC assignment found. Please check in and get assigned first.")
    if assignment.pc_id != computer_id:
        raise ValueError(
            f"PC mismatch. Assigned: {assignment.computer.hostname if assignment.computer else assignment.pc_id}, selected: {computer_id}."
        )
    return assignment


async def get_open_lab_entry_for_student(db: AsyncSession, student_id: int) -> Optional[LabEntry]:
    result = await db.execute(
        select(LabEntry)
        .options(selectinload(LabEntry.lab))
        .where(and_(LabEntry.student_id == student_id, LabEntry.exit_time.is_(None)))
        .order_by(LabEntry.entry_time.desc())
    )
    return result.scalar_one_or_none()


async def check_in_student(
    db: AsyncSession,
    student_id: int,
    lab_id: int,
    method: str = "manual",
    assignment_id: Optional[int] = None,
) -> LabEntry:
    existing = await get_open_lab_entry_for_student(db, student_id)
    if existing:
        raise ValueError("Student is already checked in.")

    lab = await db.get(Lab, lab_id)
    if not lab:
        raise ValueError("Lab not found.")

    entry = LabEntry(
        student_id=student_id,
        lab_id=lab_id,
        assignment_id=assignment_id,
        method=method,
        status="in_lab",
    )
    db.add(entry)
    await db.flush()
    return entry


async def check_out_student(db: AsyncSession, student_id: int, method: str = "manual") -> LabEntry:
    entry = await get_open_lab_entry_for_student(db, student_id)
    if not entry:
        raise ValueError("No open lab entry found for student.")

    entry.exit_time = datetime.now(timezone.utc)
    entry.status = "exited"
    entry.method = method
    await db.flush()
    return entry


async def assign_pc(db: AsyncSession, student_id: int, pc_id: int) -> PCAssignment:
    existing = await get_active_assignment_for_student(db, student_id)
    if existing:
        raise ValueError("Student already has an active PC assignment.")

    taken = await get_active_assignment_for_pc(db, pc_id)
    if taken:
        raise ValueError("Selected PC is already assigned.")

    computer = await db.get(Computer, pc_id)
    if not computer:
        raise ValueError("Computer not found.")
    if computer.status == "offline":
        raise ValueError("Cannot assign an offline computer.")

    assignment = PCAssignment(student_id=student_id, pc_id=pc_id, status="active")
    db.add(assignment)
    await db.flush()
    return assignment


async def release_assignment(db: AsyncSession, assignment_id: int) -> PCAssignment:
    assignment = await db.get(PCAssignment, assignment_id)
    if not assignment:
        raise ValueError("Assignment not found.")
    if assignment.released_at:
        raise ValueError("Assignment already released.")

    assignment.released_at = datetime.now(timezone.utc)
    assignment.status = "released"
    await db.flush()
    return assignment


async def get_assignment_mismatches(db: AsyncSession, limit: int = 50) -> List[Session]:
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.student),
            selectinload(Session.computer),
            selectinload(Session.assignment).selectinload(PCAssignment.computer),
        )
        .where(
            and_(
                Session.end_time.is_(None),
                or_(Session.assignment_id.is_(None), Session.assignment_id.is_not(None) & (Session.assignment_id != PCAssignment.id)),
            )
        )
        .join(PCAssignment, Session.assignment_id == PCAssignment.id, isouter=True)
        .limit(limit)
    )
    sessions = list(result.scalars().unique().all())
    return [s for s in sessions if (s.assignment is None or s.assignment.pc_id != s.computer_id)]


async def get_live_pc_states(db: AsyncSession) -> List[Computer]:
    result = await db.execute(
        select(Computer)
        .options(
            selectinload(Computer.agent),
            selectinload(Computer.lab_ref),
            selectinload(Computer.pc_assignments),
        )
        .order_by(Computer.hostname)
    )
    return list(result.scalars().all())


async def get_lab_occupancy(db: AsyncSession) -> List[dict]:
    result = await db.execute(
        select(
            Lab.id,
            Lab.name,
            Lab.capacity,
            func.count(LabEntry.id).label("present_count"),
        )
        .join(LabEntry, and_(LabEntry.lab_id == Lab.id, LabEntry.exit_time.is_(None)), isouter=True)
        .group_by(Lab.id, Lab.name, Lab.capacity)
        .order_by(Lab.name)
    )
    rows = result.all()
    return [
        {
            "lab_id": row.id,
            "lab_name": row.name,
            "capacity": row.capacity,
            "present_count": row.present_count,
            "occupancy_percent": round((row.present_count / row.capacity) * 100, 1) if row.capacity else 0.0,
        }
        for row in rows
    ]


async def get_utilization_summary(db: AsyncSession) -> dict:
    active_assignments = (
        await db.execute(select(func.count(PCAssignment.id)).where(PCAssignment.released_at.is_(None)))
    ).scalar() or 0
    open_entries = (
        await db.execute(select(func.count(LabEntry.id)).where(LabEntry.exit_time.is_(None)))
    ).scalar() or 0
    total_labs = (await db.execute(select(func.count(Lab.id)))).scalar() or 0

    return {
        "active_assignments": active_assignments,
        "open_entries": open_entries,
        "total_labs": total_labs,
    }
