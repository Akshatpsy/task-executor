import time
import datetime
import pika
import os
from dotenv import load_dotenv
from src.db import get_connection, reassign_stalled_tasks

load_dotenv()
POLL_INTERVAL = 2

def get_ready_tasks(conn):
    result = conn.execute("""
        SELECT id, dependencies FROM tasks WHERE status = 'pending'
    """).fetchall()

    ready = []
    for task_id, deps in result:
        if not deps:
            ready.append(task_id)
            continue
        dep_status = conn.execute(
            "SELECT status FROM tasks WHERE id = ANY(%s)", (deps,)
        ).fetchall()
        if all(s[0] == 'success' for s in dep_status):
            ready.append(task_id)
    return ready

def mark_queued(conn, task_id):
    conn.execute("UPDATE tasks SET status = 'queued' WHERE id = %s", (task_id,))

def run_scheduler():
    connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
    channel = connection.channel()
    channel.queue_declare(queue="task_queue", durable=True)

    print("Scheduler started. Polling every", POLL_INTERVAL, "seconds.")
    while True:
        reassign_stalled_tasks()
        with get_connection() as conn:
            ready = get_ready_tasks(conn)
            for task_id in ready:
                channel.basic_publish(
                    exchange="",
                    routing_key="task_queue",
                    body=task_id,
                    properties=pika.BasicProperties(delivery_mode=2),
                )
                mark_queued(conn, task_id)
                print(f"[{datetime.datetime.now().isoformat()}] Queued task: {task_id}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_scheduler()