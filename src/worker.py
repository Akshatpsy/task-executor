import pika
import os
import sys
import json
import threading
import uuid
from dotenv import load_dotenv
from datetime import datetime, timezone
from src.db import get_connection, update_task_status, handle_task_failure, update_heartbeat
from src.task_registry import TASK_REGISTRY

load_dotenv()
WORKER_ID = str(uuid.uuid4())[:8]

def log(event, **fields):
    print(json.dumps({"event": event, "worker_id": WORKER_ID, "timestamp": datetime.now(timezone.utc).isoformat(), **fields}), file=sys.stderr, flush=True)

def heartbeat_loop(task_id, stop_event):
    while not stop_event.is_set():
        try:
            update_heartbeat(task_id, WORKER_ID)
        except Exception as e:
            log("heartbeat_error", task_id=task_id, error=str(e))
        stop_event.wait(5)

def execute_task(task_id):
    # Check if task was cancelled before executing
    with get_connection() as conn:
        row = conn.execute("SELECT status FROM tasks WHERE id = %s", (task_id,)).fetchone()
        if row and row[0] == "cancelled":
            log("task_skipped_cancelled", task_id=task_id)
            return

    update_task_status(task_id, "running", start_time=datetime.now(timezone.utc))
    update_heartbeat(task_id, WORKER_ID)

    stop_event = threading.Event()
    hb_thread = threading.Thread(target=heartbeat_loop, args=(task_id, stop_event), daemon=True)
    hb_thread.start()

    try:
        fn = TASK_REGISTRY[task_id]
        result = fn()
        update_task_status(task_id, "success", end_time=datetime.now(timezone.utc), output=str(result))
        log("task_completed", task_id=task_id, result=str(result))
    except Exception as e:
        handle_task_failure(task_id, str(e))
        log("task_failed", task_id=task_id, error=str(e))
    finally:
        stop_event.set()

def callback(ch, method, properties, body):
    task_id = body.decode()
    log("task_received", task_id=task_id)
    execute_task(task_id)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    
def run_worker():
    print(f"Worker PID: {os.getpid()}", flush=True)
    log("worker_started", pid=os.getpid())
    connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
    channel = connection.channel()
    channel.queue_declare(queue="task_queue", durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="task_queue", on_message_callback=callback)

    print(f"Worker {WORKER_ID} started. Waiting for tasks.", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    run_worker()