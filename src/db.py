import os
import psycopg
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

def get_connection():
    return psycopg.connect(os.environ["DATABASE_URL"])

def insert_task(task):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks (id, dependencies, status, idempotency_key)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                status = 'pending',
                dependencies = EXCLUDED.dependencies,
                start_time = NULL,
                end_time = NULL,
                output = NULL,
                error = NULL,
                retry_count = 0,
                worker_id = NULL,
                heartbeat_at = NULL
            """,
            (task.id, task.dependencies, "pending", task.idempotency_key),
        )
        
def update_task_status(task_id, status, start_time=None, end_time=None, output=None, error=None):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = %s,
                start_time = COALESCE(%s, start_time),
                end_time = COALESCE(%s, end_time),
                output = COALESCE(%s, output),
                error = COALESCE(%s, error)
            WHERE id = %s
            """,
            (status, start_time, end_time, output, error, task_id),
        )

def handle_task_failure(task_id, error_message):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT retry_count, max_retries FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()
        retry_count, max_retries = row
        if retry_count < max_retries:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    error = %s,
                    start_time = NULL,
                    end_time = NULL
                WHERE id = %s
                """,
                (error_message, task_id),
            )
        else:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'dead_letter',
                    error = %s,
                    end_time = %s
                WHERE id = %s
                """,
                (error_message, datetime.now(timezone.utc), task_id),
            )

def update_heartbeat(task_id, worker_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET heartbeat_at = %s, worker_id = %s WHERE id = %s",
            (datetime.now(timezone.utc), worker_id, task_id),
        )

def reassign_stalled_tasks(stale_seconds=15):
    with get_connection() as conn:
        stalled = conn.execute(
            """
            SELECT id FROM tasks
            WHERE status = 'running'
              AND heartbeat_at < %s
            """,
            (datetime.now(timezone.utc) - timedelta(seconds=stale_seconds),),
        ).fetchall()
        for (task_id,) in stalled:
            conn.execute(
                "UPDATE tasks SET status = 'pending', retry_count = retry_count + 1 WHERE id = %s",
                (task_id,),
            )
            print(f"Reassigned stalled task: {task_id}")

def check_idempotency(key):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM idempotency_log WHERE idempotency_key = %s", (key,)
        ).fetchone()
        return row is not None

def record_idempotency(key):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO idempotency_log (idempotency_key) VALUES (%s) ON CONFLICT DO NOTHING",
            (key,),
        )

def get_all_tasks():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, status, dependencies, retry_count, start_time, end_time, error FROM tasks ORDER BY id"
        ).fetchall()
        return [
            {
                "id": r[0], "status": r[1], "dependencies": r[2],
                "retry_count": r[3],
                "start_time": r[4].isoformat() if r[4] else None,
                "end_time": r[5].isoformat() if r[5] else None,
                "error": r[6],
            }
            for r in rows
        ]

def cancel_task(task_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'cancelled' WHERE id = %s AND status IN ('pending', 'queued')",
            (task_id,),
        )