from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SessionStart(BaseModel):
    computer_id: int
    activity_type_id: int
    course_id: Optional[int] = None
    experiment_id: Optional[int] = None
    project_id: Optional[int] = None
    research_id: Optional[int] = None


class SessionStop(BaseModel):
    software_ids: List[int] = []
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    student_name: str
    student_id_str: str
    computer_hostname: str
    activity_type: str
    course_name: Optional[str] = None
    experiment_title: Optional[str] = None
    project_title: Optional[str] = None
    research_title: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    software_used: List[str] = []
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ComputerResponse(BaseModel):
    id: int
    hostname: str
    lab: str
    status: str

    class Config:
        from_attributes = True


class SoftwareResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class CourseResponse(BaseModel):
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class ExperimentResponse(BaseModel):
    id: int
    number: int
    title: str
    course_id: int

    class Config:
        from_attributes = True


class ActivityTypeResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    title: str
    course_id: Optional[int] = None

    class Config:
        from_attributes = True


class ResearchResponse(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True
