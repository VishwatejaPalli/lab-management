from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.session_service import (
    get_dashboard_stats,
    get_student_sessions,
    get_active_session,
    get_all_sessions,
)
from app.services.operations_service import (
    get_live_pc_states,
    get_assignment_mismatches,
    get_lab_occupancy,
    get_utilization_summary,
    get_active_assignment_for_student,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        stats = await get_dashboard_stats(db)
        recent_sessions = await get_all_sessions(db, limit=20)
        pc_states = await get_live_pc_states(db)
        occupancy = await get_lab_occupancy(db)
        utilization = await get_utilization_summary(db)
        mismatches = await get_assignment_mismatches(db, limit=20)
        return request.app.state.templates.TemplateResponse(
            "dashboard/admin.html",
            {
                "request": request,
                "user": current_user,
                "stats": stats,
                "sessions": recent_sessions,
                "pc_states": pc_states,
                "occupancy": occupancy,
                "utilization": utilization,
                "mismatches": mismatches,
            },
        )
    elif current_user.role == "faculty":
        stats = await get_dashboard_stats(db)
        recent_sessions = await get_all_sessions(db, limit=20)
        pc_states = await get_live_pc_states(db)
        occupancy = await get_lab_occupancy(db)
        utilization = await get_utilization_summary(db)
        mismatches = await get_assignment_mismatches(db, limit=20)
        return request.app.state.templates.TemplateResponse(
            "dashboard/faculty.html",
            {
                "request": request,
                "user": current_user,
                "stats": stats,
                "sessions": recent_sessions,
                "pc_states": pc_states,
                "occupancy": occupancy,
                "utilization": utilization,
                "mismatches": mismatches,
            },
        )
    else:
        active = await get_active_session(db, current_user.id)
        sessions = await get_student_sessions(db, current_user.id)
        assignment = await get_active_assignment_for_student(db, current_user.id)
        return request.app.state.templates.TemplateResponse(
            "dashboard/student.html",
            {
                "request": request,
                "user": current_user,
                "active_session": active,
                "sessions": sessions,
                "assignment": assignment,
            },
        )
