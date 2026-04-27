from pydantic import BaseModel


class UserCourseProgress(BaseModel):
    course_id: str
    title: str
    completion_percentage: float
    total_tasks: int
    completed_tasks: int


class UserDashboardResponse(BaseModel):
    total_courses: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overall_completion_percentage: float
    course_progress: list[UserCourseProgress]


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_courses: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
