from src.task import Task
from src.db import insert_task

tasks = {
    "extract": Task(id="extract", dependencies=[]),
    "clean": Task(id="clean", dependencies=["extract"]),
    "transform": Task(id="transform", dependencies=["clean"]),
    "load": Task(id="load", dependencies=["transform"]),
    "notify": Task(id="notify", dependencies=["load"]),
}

if __name__ == "__main__":
    for task in tasks.values():
        insert_task(task)
    print("Tasks inserted into Postgres. Start the scheduler and workers to execute.")