from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    dependencies: list[str] = field(default_factory=list)
    run: Callable[[], Any] = None       # the actual work
    idempotency_key: str = None         # defaults to task id if not set
    max_retries: int = 0                # Phase 3 will use this; keep the field now

    def __post_init__(self):
        if self.idempotency_key is None:
            self.idempotency_key = self.id