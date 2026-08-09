# pyrefly: ignore [missing-import]
import psycopg
import os
import time
from dotenv import load_dotenv

load_dotenv()

def main():
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    print("Checking 'fail_test' progression...")
    
    start_time = time.time()
    seen_states = []
    
    try:
        while time.time() - start_time < 30:
            with conn.cursor() as cur:
                cur.execute("SELECT id, status, retry_count, max_retries, error FROM tasks WHERE id = 'fail_test'")
                row = cur.fetchone()
                if row:
                    task_id, status, retry_count, max_retries, error = row
                    state = (status, retry_count, max_retries, error)
                    # Print if state changes
                    if not seen_states or seen_states[-1] != state:
                        seen_states.append(state)
                        err_str = str(error)[:40] + "..." if error else "None"
                        print(f"[{time.strftime('%H:%M:%S')}] Status: {status:<12} | Retry Count: {retry_count}/{max_retries} | Error: {err_str}")
                    
                    if status == 'dead_letter':
                        print("Reached 'dead_letter' status. Stopping check.")
                        break
                else:
                    print("Task 'fail_test' not found!")
                    break
            time.sleep(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
