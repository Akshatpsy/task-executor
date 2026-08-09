import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def check_step_11():
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM side_effect_counter;")
            counter_rows = cur.fetchall()
            cur.execute("SELECT idempotency_key FROM idempotency_log;")
            idempotency_rows = cur.fetchall()

            print("--- STEP 11 IMMEDIATE CHECK ---")
            print("side_effect_counter:", counter_rows)
            print("idempotency_log:", idempotency_rows)

if __name__ == "__main__":
    check_step_11()
