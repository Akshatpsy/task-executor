import time as time_module
from src.db import check_idempotency, record_idempotency, get_connection

def extract(): return "extracted data"
def clean(): return "cleaned data"
def transform(): return "transformed data"
def load(): return "loaded"
def notify(): return "notification sent"

TASK_REGISTRY = {
    "extract": extract,
    "clean": clean,
    "transform": transform,
    "load": load,
    "notify": notify,
}

def always_fails():
    raise Exception("This task is designed to fail")

TASK_REGISTRY["fail_test"] = always_fails

def slow_task():
    time_module.sleep(60)
    return "finished slow task"

TASK_REGISTRY["crash_test"] = slow_task

def idempotent_test():
    key = "idempotent_test_key"
    if check_idempotency(key):
        return "already done, skipped side effect"
    with get_connection() as conn:
        conn.execute("UPDATE side_effect_counter SET count = count + 1 WHERE id = 1")
    record_idempotency(key)
    time_module.sleep(20)  # deliberate window to kill worker AFTER side effect committed
    return "side effect executed"

TASK_REGISTRY["idempotent_test"] = idempotent_test