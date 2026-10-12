from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List
import os

DATABASE_URL = "sqlite:///./action_list.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    category = Column(String, index=True, default="General")
    completed = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="JARVIS Action List")

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TaskCreate(BaseModel):
    title: str
    category: str = "General"
    notes: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    completed: Optional[bool] = None
    notes: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    category: str
    completed: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("static/index.html")

@app.get("/api/tasks", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db), category: Optional[str] = None, completed: Optional[bool] = None):
    query = db.query(Task)
    if category:
        query = query.filter(Task.category == category)
    if completed is not None:
        query = query.filter(Task.completed == completed)
    return query.order_by(Task.completed.asc(), Task.created_at.desc()).all()

@app.post("/api/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.patch("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, update: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"ok": True}

@app.on_event("startup")
def seed():
    db = SessionLocal()
    if db.query(Task).count() == 0:
        samples = [
            Task(title="Follow up on 3 hot Mutual of Omaha IUL leads", category="Insurance"),
            Task(title="Confirm skimmer basket replacements for 2 clients", category="Pool Care"),
            Task(title="Review today's fibre door-to-door route", category="Fibre"),
            Task(title="End-of-day reconciliation across desks", category="Admin"),
        ]
        db.add_all(samples)
        db.commit()
    db.close()
