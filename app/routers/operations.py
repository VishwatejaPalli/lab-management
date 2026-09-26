from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user, require_role
from app.models.user import User
from app.services.operations_service import (
    check_in_student,
    check_out_student,
    assign_pc,
    release_assignment,
    get_assignment_mismatches,
)

router = APIRouter(prefix="/ops", tags=["operations"])


class CheckInRequest(BaseModel):
    student_id: Optional[int] = None
    lab_id: int
    method: str = "manual"
    assignment_id: Optional[int] = None


class CheckOutRequest(BaseModel):
    student_id: Optional[int] = None
    method: str = "manual"


class AssignPCRequest(BaseModel):
    student_id: int
    pc_id: int


@router.post("/checkin")
async def checkin(
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_student_id = payload.student_id if current_user.role in ["admin", "faculty"] and payload.student_id else current_user.id
    try:
        entry = await check_in_student(
            db,
            student_id=target_student_id,
            lab_id=payload.lab_id,
            method=payload.method,
            assignment_id=payload.assignment_id,
        )
        return {
            "id": entry.id,
            "student_id": entry.student_id,
            "lab_id": entry.lab_id,
            "entry_time": entry.entry_time,
            "status": entry.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/checkout")
async def checkout(
    payload: CheckOutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_student_id = payload.student_id if current_user.role in ["admin", "faculty"] and payload.student_id else current_user.id
    try:
        entry = await check_out_student(db, student_id=target_student_id, method=payload.method)
        return {
            "id": entry.id,
            "student_id": entry.student_id,
            "lab_id": entry.lab_id,
            "entry_time": entry.entry_time,
            "exit_time": entry.exit_time,
            "status": entry.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assign", dependencies=[Depends(require_role("admin", "faculty"))])
async def assign(
    payload: AssignPCRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        assignment = await assign_pc(db, student_id=payload.student_id, pc_id=payload.pc_id)
        return {
            "id": assignment.id,
            "student_id": assignment.student_id,
            "pc_id": assignment.pc_id,
            "assigned_at": assignment.assigned_at,
            "status": assignment.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/release/{assignment_id}", dependencies=[Depends(require_role("admin", "faculty"))])
async def release(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        assignment = await release_assignment(db, assignment_id=assignment_id)
        return {
            "id": assignment.id,
            "released_at": assignment.released_at,
            "status": assignment.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mismatches", dependencies=[Depends(require_role("admin", "faculty"))])
async def mismatches(
    db: AsyncSession = Depends(get_db),
):
    rows = await get_assignment_mismatches(db)
    return [
        {
            "session_id": s.id,
            "student": s.student.student_id,
            "expected_pc": s.assignment.computer.hostname if s.assignment and s.assignment.computer else None,
            "actual_pc": s.computer.hostname if s.computer else None,
        }
        for s in rows
    ]
