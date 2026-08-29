from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import os

from app.routers import auth, sessions, dashboard, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(title="Lab Management System", version="1.0.0", lifespan=lifespan)

# Static files
base_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))
app.state.templates = templates

# Routers
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(dashboard.router)


@app.exception_handler(303)
async def redirect_handler(request: Request, exc):
    return RedirectResponse(url=exc.headers.get("Location", "/login"), status_code=303)
