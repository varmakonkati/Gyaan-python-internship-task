from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./test.db"

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)


engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.post("/tasks/", response_model=Task)
async def create_task(task: Task, db: Session = Depends(get_db)):
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, updated_task: Task, db: Session = Depends(get_db)):
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if existing_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in updated_task.dict(exclude={"id"}).items():
        setattr(existing_task, field, value)

    db.commit()
    db.refresh(existing_task)
    return existing_task

@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task successfully deleted"}

@app.get("/tasks/", response_model=list[Task])
async def read_all_tasks(completed: bool = None, db: Session = Depends(get_db)):
    if completed is not None:
        tasks = db.query(Task).filter(Task.completed == completed).all()
    else:
        tasks = db.query(Task).all()

    return tasks
