# pyrefly: ignore [missing-import]
import pytest
from src.task import Task
from src.scheduler import topological_sort

def test_simple_chain():
    tasks = {
        "A": Task(id="A", dependencies=[]),
        "B": Task(id="B", dependencies=["A"]),
        "C": Task(id="C", dependencies=["B"]),
    }
    order = topological_sort(tasks)
    assert order.index("A") < order.index("B") < order.index("C")

def test_cycle_raises():
    tasks = {
        "A": Task(id="A", dependencies=["C"]),
        "B": Task(id="B", dependencies=["A"]),
        "C": Task(id="C", dependencies=["B"]),
    }
    with pytest.raises(ValueError, match="Cycle detected"):
        topological_sort(tasks)

def test_unknown_dependency_raises():
    tasks = {
        "A": Task(id="A", dependencies=["ghost"]),
    }
    with pytest.raises(ValueError, match="unknown task"):
        topological_sort(tasks)