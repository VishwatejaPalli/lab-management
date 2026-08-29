from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(tags=["pages"])


@router.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login")
async def login_page(request: Request):
    # If already logged in, redirect to dashboard
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=303)
    return request.app.state.templates.TemplateResponse(
        "login.html", {"request": request}
    )
