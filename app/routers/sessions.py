from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.routers.auth import get_current_user, require_role
from app.models.user import User
from app.models.computer import Computer
from app.models.software import Software
from app.models.course import Course
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.research import Research
from app.models.activity_type import ActivityType
from app.services.session_service import start_session, stop_session, get_active_session
from app.services.operations_service import get_active_assignment_for_student
from typing import Optional

router = APIRouter(prefix="/session", tags=["sessions"])


async def _load_start_form_data(db: AsyncSession, current_user: User):
    all_computers = (await db.execute(select(Computer).order_by(Computer.hostname))).scalars().all()
    assignment = await get_active_assignment_for_student(db, current_user.id)

    if assignment:
        computers = [assignment.computer] if assignment.computer else []
    else:
        computers = (await db.execute(select(Computer).where(Computer.status == "available").order_by(Computer.hostname))).scalars().all()

    activity_types = (await db.execute(select(ActivityType))).scalars().all()
    courses = (await db.execute(select(Course).order_by(Course.code))).scalars().all()
    experiments = (await db.execute(select(Experiment).order_by(Experiment.course_id, Experiment.number))).scalars().all()
    projects = (await db.execute(select(Project).order_by(Project.title))).scalars().all()
    research_list = (await db.execute(select(Research).order_by(Research.title))).scalars().all()

    return {
        "assignment": assignment,
        "computers": list(computers),
        "all_computers": list(all_computers),
        "activity_types": list(activity_types),
        "courses": list(courses),
        "experiments": list(experiments),
        "projects": list(projects),
        "research_list": list(research_list),
    }


@router.get("/start", dependencies=[Depends(require_role("student"))])
async def session_start_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    active = await get_active_session(db, current_user.id)
    if active:
        return RedirectResponse(url="/session/active", status_code=303)

    data = await _load_start_form_data(db, current_user)
    return request.app.state.templates.TemplateResponse(
        "session/start.html",
        {
            "request": request,
            "user": current_user,
            **data,
        },
    )


@router.post("/start", dependencies=[Depends(require_role("student"))])
async def session_start_action(
    request: Request,
    computer_id: int = Form(...),
    activity_type_id: int = Form(...),
    course_id: Optional[int] = Form(None),
    experiment_id: Optional[int] = Form(None),
    project_id: Optional[int] = Form(None),
    research_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await start_session(
            db,
            student_id=current_user.id,
            computer_id=computer_id,
            activity_type_id=activity_type_id,
            course_id=course_id if course_id and course_id > 0 else None,
            experiment_id=experiment_id if experiment_id and experiment_id > 0 else None,
            project_id=project_id if project_id and project_id > 0 else None,
            research_id=research_id if research_id and research_id > 0 else None,
            started_by_agent=False,
        )
        return RedirectResponse(url="/session/active", status_code=303)
    except ValueError as e:
        data = await _load_start_form_data(db, current_user)
        return request.app.state.templates.TemplateResponse(
            "session/start.html",
            {
                "request": request,
                "user": current_user,
                "error": str(e),
                **data,
            },
            status_code=400,
        )


@router.get("/active", dependencies=[Depends(require_role("student"))])
async def session_active_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    active = await get_active_session(db, current_user.id)
    if not active:
        return RedirectResponse(url="/session/start", status_code=303)

    software_list = (await db.execute(select(Software).order_by(Software.name))).scalars().all()

    return request.app.state.templates.TemplateResponse(
        "session/active.html",
        {
            "request": request,
            "user": current_user,
            "session": active,
            "software_list": list(software_list),
        },
    )


@router.post("/stop", dependencies=[Depends(require_role("student"))])
async def session_stop_action(
    request: Request,
    session_id: int = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_data = await request.form()
    software_ids = [int(x) for x in form_data.getlist("software_ids") if x]

    try:
        await stop_session(db, session_id=session_id, software_ids=software_ids, notes=notes)
        return RedirectResponse(url="/dashboard", status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", dependencies=[Depends(require_role("student"))])
async def session_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.session_service import get_student_sessions

    sessions = await get_student_sessions(db, current_user.id)
    return request.app.state.templates.TemplateResponse(
        "session/history.html",
        {"request": request, "user": current_user, "sessions": sessions},
    )
