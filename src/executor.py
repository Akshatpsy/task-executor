from datetime import datetime, timezone
from src.scheduler import topological_sort
from src.db import insert_task, update_task_status

def run_dag(tasks: dict):
    order = topological_sort(tasks)

    for task_id in order:
        task = tasks[task_id]
        insert_task(task)
        start = datetime.now(timezone.utc)
        update_task_status(task_id, "running", start_time=start)

        try:
            result = task.run()
            end = datetime.now(timezone.utc)
            update_task_status(task_id, "success", end_time=end, output=str(result))
        except Exception as e:
            end = datetime.now(timezone.utc)
            update_task_status(task_id, "failed", end_time=end, error=str(e))

    return order