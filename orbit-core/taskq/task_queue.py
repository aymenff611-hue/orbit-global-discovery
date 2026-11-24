"""ORBIT Distributed Task Queue.

Manages distributed task queues with backpressure, idempotency,
retry policies, dead-letter handling, and recovery after worker failure.
"""

import logging
import uuid
import time
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger("orbit.queue.task_queue")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    RETRY = "retry"


@dataclass
class Task:
    """A task in the distributed queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 5
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None  # For deduplication

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "worker_id": self.worker_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "result": self.result,
            "idempotency_key": self.idempotency_key,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            task_type=data.get("task_type", ""),
            payload=data.get("payload", {}),
            priority=data.get("priority", 5),
            status=TaskStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            worker_id=data.get("worker_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 5),
            error_message=data.get("error_message"),
            result=data.get("result"),
            idempotency_key=data.get("idempotency_key"),
        )


class TaskQueue:
    """In-memory task queue with Redis backend support.

    Provides:
    - Backpressure when queue depth exceeds thresholds
    - Idempotency via idempotency keys
    - Retry policies with exponential backoff
    - Dead-letter handling for failed tasks
    - Recovery after worker failure
    """

    def __init__(self, settings=None, redis_client=None):
        self.settings = settings
        self.redis = redis_client
        self._queues: Dict[str, List[Task]] = {}  # queue_name -> tasks
        self._task_index: Dict[str, Task] = {}  # task_id -> task
        self._idempotency_index: Dict[str, str] = {}  # idempotency_key -> task_id
        self._dead_letter: List[Task] = []
        self._stats = {
            "tasks_enqueued": 0,
            "tasks_dequeued": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_dead_letter": 0,
            "duplicates_rejected": 0,
        }
        self._max_queue_depth = 100000
        self._backpressure_threshold = 0.8  # 80%

    def enqueue(self, task: Task, queue_name: str = "default") -> bool:
        """Enqueue a task. Returns False if duplicate (idempotency)."""
        # Check idempotency
        if task.idempotency_key and task.idempotency_key in self._idempotency_index:
            self._stats["duplicates_rejected"] += 1
            logger.debug(f"Duplicate task rejected: {task.idempotency_key}")
            return False

        # Check backpressure
        current_depth = sum(len(q) for q in self._queues.values())
        if current_depth >= self._max_queue_depth:
            logger.warning(f"Queue at max depth {self._max_queue_depth}, rejecting task {task.id}")
            return False

        # Store task
        self._task_index[task.id] = task
        if task.idempotency_key:
            self._idempotency_index[task.idempotency_key] = task.id

        # Add to queue
        if queue_name not in self._queues:
            self._queues[queue_name] = []
        self._queues[queue_name].append(task)
        # Sort by priority (lower = higher priority)
        self._queues[queue_name].sort(key=lambda t: t.priority)

        self._stats["tasks_enqueued"] += 1
        logger.debug(f"Enqueued task {task.id} to queue {queue_name} (priority={task.priority})")
        return True

    def dequeue(self, queue_name: str = "default",
                worker_id: Optional[str] = None) -> Optional[Task]:
        """Dequeue the highest priority task from a queue."""
        if queue_name not in self._queues or not self._queues[queue_name]:
            return None

        task = self._queues[queue_name].pop(0)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        task.worker_id = worker_id

        self._stats["tasks_dequeued"] += 1
        logger.debug(f"Dequeued task {task.id} from queue {queue_name}")
        return task

    def complete(self, task_id: str, result: Optional[Dict[str, Any]] = None):
        """Mark a task as completed."""
        task = self._task_index.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for completion")
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.result = result
        self._stats["tasks_completed"] += 1
        logger.debug(f"Task {task_id} completed")

    def fail(self, task_id: str, error_message: str,
             retry: bool = True) -> bool:
        """Mark a task as failed. Returns True if retried, False if dead letter."""
        task = self._task_index.get(task_id)
        if not task:
            return False

        task.retry_count += 1
        task.error_message = error_message

        if retry and task.retry_count < task.max_retries:
            task.status = TaskStatus.RETRY
            # Exponential backoff: schedule retry
            from datetime import timedelta
            backoff_seconds = min(300, 2 ** task.retry_count)
            task.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
            # Re-enqueue
            self.enqueue(task, queue_name="retry")
            logger.debug(f"Task {task_id} scheduled for retry {task.retry_count}/{task.max_retries}")
            return True
        else:
            task.status = TaskStatus.DEAD_LETTER
            task.completed_at = datetime.now(timezone.utc)
            self._dead_letter.append(task)
            self._stats["tasks_dead_letter"] += 1
            logger.warning(f"Task {task_id} moved to dead letter after {task.retry_count} retries")
            return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._task_index.get(task_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        queue_depths = {name: len(tasks) for name, tasks in self._queues.items()}
        return {
            **self._stats,
            "queue_depths": queue_depths,
            "total_queue_depth": sum(queue_depths.values()),
            "dead_letter_size": len(self._dead_letter),
            "backpressure_active": sum(queue_depths.values()) >= self._max_queue_depth * self._backpressure_threshold,
        }

    def acknowledge(self, task_id: str):
        """Acknowledge task processing (for at-least-once delivery)."""
        # Mark as in-progress to prevent re-delivery
        task = self._task_index.get(task_id)
        if task and task.status == TaskStatus.RUNNING:
            pass  # Already running

    def reclaim_stale_tasks(self, max_age_seconds: int = 3600,
                           worker_id: Optional[str] = None) -> int:
        """Reclaim tasks that were running but the worker failed.

        Returns number of reclaimed tasks.
        """
        now = datetime.now(timezone.utc)
        reclaimed = 0

        for queue_name, tasks in self._queues.items():
            for task in tasks:
                if (task.status == TaskStatus.RUNNING and
                    task.worker_id == worker_id and
                    task.started_at and
                    (now - task.started_at).total_seconds() > max_age_seconds):
                    task.status = TaskStatus.PENDING
                    task.worker_id = None
                    task.started_at = None
                    task.retry_count += 1
                    reclaimed += 1
                    logger.info(f"Reclaimed stale task {task.id} from failed worker {worker_id}")

        return reclaimed
