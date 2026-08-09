import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def run_step_3_and_4():
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            # Clear previous idempotency log for clean test run
            cur.execute("DELETE FROM idempotency_log WHERE idempotency_key = 'idempotent_test_key';")
            cur.execute("UPDATE side_effect_counter SET count = 0 WHERE id = 1;")
            cur.execute("DELETE FROM tasks WHERE id IN ('fail_test', 'idempotent_test');")
            
            # Step 3
            cur.execute("""
                INSERT INTO tasks (id, dependencies, status, idempotency_key, max_retries)
                VALUES ('fail_test', '{}', 'pending', 'fail_test', 3)
                ON CONFLICT (id) DO NOTHING;
            """)
            cur.execute("""
                INSERT INTO tasks (id, dependencies, status, idempotency_key, max_retries)
                VALUES ('idempotent_test', '{}', 'pending', 'idempotent_test', 3)
                ON CONFLICT (id) DO NOTHING;
            """)
            conn.commit()

            # Step 4: Baseline state
            cur.execute("SELECT * FROM side_effect_counter;")
            counter_rows = cur.fetchall()
            cur.execute("SELECT id, status FROM tasks WHERE id = 'idempotent_test';")
            task_rows = cur.fetchall()

            print("--- STEP 4 BASELINE STATE ---")
            print("side_effect_counter:", counter_rows)
            print("tasks status:", task_rows)

if __name__ == "__main__":
    run_step_3_and_4()
