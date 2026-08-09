from collections import deque
from src.task import Task

def topological_sort(tasks: dict[str, Task]) -> list[str]:
    in_degree = {tid: 0 for tid in tasks}
    dependents = {tid: [] for tid in tasks}

    for tid, task in tasks.items():
        for dep in task.dependencies:
            if dep not in tasks:
                raise ValueError(f"Task {tid} depends on unknown task {dep}")
            in_degree[tid] += 1
            dependents[dep].append(tid)

    queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
    order = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for dependent in dependents[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(tasks):
        remaining = set(tasks) - set(order)
        raise ValueError(f"Cycle detected among tasks: {remaining}")

    return order