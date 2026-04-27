from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.routes import auth, courses, dashboard, learnflow, planner, tasks, users


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(title="LearnFlow LMS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(tasks.router)
app.include_router(planner.router)
app.include_router(dashboard.router)
app.include_router(learnflow.router)


@app.get("/")
async def root() -> dict:
    return {"message": "LMS backend is running"}
