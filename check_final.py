import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def check_final():
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM side_effect_counter;")
            counter_rows = cur.fetchall()
            cur.execute("SELECT id, status, output, error FROM tasks WHERE id = 'idempotent_test';")
            task_rows = cur.fetchall()
            cur.execute("SELECT * FROM idempotency_log;")
            idempotency_rows = cur.fetchall()

            print("--- STEP 14 FINAL CHECK ---")
            print("side_effect_counter:", counter_rows)
            print("tasks (idempotent_test):", task_rows)
            print("idempotency_log:", idempotency_rows)

if __name__ == "__main__":
    check_final()
