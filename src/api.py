from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
from src.db import get_all_tasks, cancel_task, insert_task, get_connection
from src.task import Task
from src.task_registry import TASK_REGISTRY

app = FastAPI(title="Distributed Task Executor")

class TaskSubmission(BaseModel):
    id: str
    dependencies: list[str] = []

class DAGSubmission(BaseModel):
    tasks: list[TaskSubmission]

@app.post("/dags")
def submit_dag(dag: DAGSubmission):
    for t in dag.tasks:
        if t.id not in TASK_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type '{t.id}'. Available: {list(TASK_REGISTRY.keys())}",
            )
    for t in dag.tasks:
        task = Task(id=t.id, dependencies=t.dependencies)
        insert_task(task)
    return {"status": "submitted", "task_count": len(dag.tasks)}

@app.get("/tasks")
def list_tasks():
    return get_all_tasks()

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, status, dependencies, retry_count, start_time, end_time, output, error FROM tasks WHERE id = %s",
            (task_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": row[0], "status": row[1], "dependencies": row[2],
        "retry_count": row[3],
        "start_time": row[4].isoformat() if row[4] else None,
        "end_time": row[5].isoformat() if row[5] else None,
        "output": row[6], "error": row[7],
    }

@app.post("/tasks/{task_id}/cancel")
def cancel(task_id: str):
    cancel_task(task_id)
    return {"status": "cancel requested", "task_id": task_id}

@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            tasks = get_all_tasks()
            await websocket.send_json(tasks)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass

app.mount("/", StaticFiles(directory="static", html=True), name="static")
