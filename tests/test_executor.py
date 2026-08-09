from unittest.mock import patch
import pytest
from src.task import Task
from src.executor import execute_tasks, TaskExecutionError

@patch("src.executor.save_tasks")
@patch("src.executor.update_task_status")
def test_execute_tasks_success(mock_update, mock_save):
    # Setup simple workflow: A -> B
    history = []
    
    def run_a():
        history.append("A")
        
    def run_b():
        history.append("B")
        
    task_a = Task("A", "Task A", execute_fn=run_a)
    task_b = Task("B", "Task B", dependencies=["A"], execute_fn=run_b)
    
    summary = execute_tasks([task_b, task_a])
    
    assert summary == {"A": "COMPLETED", "B": "COMPLETED"}
    assert history == ["A", "B"]
    
    # Assert DB saving and updates occurred
    mock_save.assert_called_once()
    # A: RUNNING, COMPLETED
    # B: RUNNING, COMPLETED
    assert mock_update.call_count == 4

@patch("src.executor.save_tasks")
@patch("src.executor.update_task_status")
def test_execute_tasks_with_failure(mock_update, mock_save):
    # Setup workflow where A fails, B depends on A, C is independent and should run
    history = []
    
    def run_a():
        history.append("A_fail")
        raise RuntimeError("A failed")
        
    def run_b():
        history.append("B")
        
    def run_c():
        history.append("C")
        
    task_a = Task("A", "Task A", execute_fn=run_a)
    task_b = Task("B", "Task B", dependencies=["A"], execute_fn=run_b)
    task_c = Task("C", "Task C", execute_fn=run_c)
    
    with pytest.raises(TaskExecutionError):
        execute_tasks([task_a, task_b, task_c])
        
    # Task A fails, B is skipped (marked FAILED), C succeeds
    assert task_a.status == "FAILED"
    assert task_b.status == "FAILED"
    assert task_c.status == "COMPLETED"
    
    assert "A_fail" in history
    assert "C" in history
    assert "B" not in history
