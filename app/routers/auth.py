from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth import authenticate_user, create_access_token, get_password_hash, decode_token, get_user_by_student_id
from app.models.user import User
from app.schemas.user import UserCreate
from sqlalchemy import select

router = APIRouter(tags=["auth"])


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    student_id = payload.get("sub")
    if not student_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = await get_user_by_student_id(db, student_id)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_role(*roles):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker


@router.post("/login")
async def login(
    request: Request,
    student_id: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, student_id, password)
    if not user:
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
            status_code=401,
        )
    token = create_access_token({"sub": user.student_id, "role": user.role})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=28800)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.post("/api/users", dependencies=[Depends(require_role("admin"))])
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_student_id(db, user_data.student_id)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        student_id=user_data.student_id,
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        department=user_data.department,
    )
    db.add(user)
    await db.flush()
    return {"id": user.id, "student_id": user.student_id, "role": user.role}
