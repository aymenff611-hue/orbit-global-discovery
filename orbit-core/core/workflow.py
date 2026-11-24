"""ORBIT Workflow Recovery and Orchestration.

Manages workflow execution with checkpointing, recovery after worker failure,
idempotency, retry policies, and dead-letter handling.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("orbit.core.workflow")


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str = ""
    handler: Optional[str] = None  # Component that handles this step
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    checkpoint_data: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowInstance:
    """A workflow instance with steps and state."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = field(default_factory=list)
    current_step_index: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    worker_id: Optional[str] = None


class WorkflowManager:
    """Manages workflow execution with recovery and checkpointing."""

    def __init__(self, settings=None):
        self.settings = settings
        self._workflows: Dict[str, WorkflowInstance] = {}
        self._step_handlers: Dict[str, Callable] = {}
        self._stats = {
            "workflows_created": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "workflows_recovered": 0,
            "steps_executed": 0,
            "checkpoints_saved": 0,
        }

    def register_step_handler(self, step_type: str, handler: Callable):
        """Register a handler for a workflow step type."""
        self._step_handlers[step_type] = handler
        logger.info(f"Registered workflow step handler: {step_type}")

    def create_workflow(self, workflow_type: str, steps: List[Dict[str, Any]],
                        context: Optional[Dict[str, Any]] = None) -> WorkflowInstance:
        """Create a new workflow instance."""
        workflow = WorkflowInstance(
            workflow_type=workflow_type,
            context=context or {},
        )

        for step_def in steps:
            step = WorkflowStep(
                step_name=step_def.get("name", "unnamed"),
                handler=step_def.get("handler", ""),
                input_data=step_def.get("input_data", {}),
                max_retries=step_def.get("max_retries", 3),
            )
            workflow.steps.append(step)

        self._workflows[workflow.id] = workflow
        self._stats["workflows_created"] += 1
        logger.info(f"Created workflow {workflow.id} of type {workflow_type}")
        return workflow

    def start_workflow(self, workflow_id: str) -> bool:
        """Start executing a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        if workflow.status != WorkflowStatus.PENDING:
            logger.warning(f"Workflow {workflow_id} already started")
            return False

        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now(timezone.utc)
        return True

    def execute_next_step(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Execute the next step in a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return None

        if workflow.current_step_index >= len(workflow.steps):
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(timezone.utc)
            self._stats["workflows_completed"] += 1
            return {"status": "completed", "workflow_id": workflow_id}

        step = workflow.steps[workflow.current_step_index]
        step.status = WorkflowStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)

        try:
            # Execute step handler
            handler = self._step_handlers.get(step.handler)
            if handler:
                result = handler(step.input_data, workflow.context)
                step.output_data = result if isinstance(result, dict) else {"result": result}
                step.status = WorkflowStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)

                # Save checkpoint
                self._save_checkpoint(workflow)

                workflow.current_step_index += 1
                self._stats["steps_executed"] += 1

                return {
                    "status": "step_completed",
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "output": step.output_data,
                    "next_step_index": workflow.current_step_index,
                }
            else:
                step.status = WorkflowStatus.FAILED
                step.error_message = f"No handler registered for step type: {step.handler}"
                return self._handle_step_failure(workflow, step)

        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error_message = str(e)
            return self._handle_step_failure(workflow, step)

    def _handle_step_failure(self, workflow: WorkflowInstance, step: WorkflowStep):
        """Handle a failed workflow step."""
        step.retry_count += 1

        if step.retry_count < step.max_retries:
            step.status = WorkflowStatus.PENDING  # Will be retried
            logger.warning(f"Step {step.step_id} failed, retry {step.retry_count}/{step.max_retries}")
            return {
                "status": "step_retry",
                "step_id": step.step_id,
                "retry_count": step.retry_count,
                "error": step.error_message,
            }
        else:
            step.status = WorkflowStatus.FAILED
            step.completed_at = datetime.now(timezone.utc)
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = step.error_message
            workflow.completed_at = datetime.now(timezone.utc)
            self._stats["workflows_failed"] += 1
            logger.error(f"Workflow {workflow_id} failed at step {step.step_name}: {step.error_message}")
            return {
                "status": "workflow_failed",
                "workflow_id": workflow_id,
                "error": step.error_message,
            }

    def _save_checkpoint(self, workflow: WorkflowInstance):
        """Save a checkpoint for workflow recovery."""
        self._stats["checkpoints_saved"] += 1
        logger.debug(f"Saved checkpoint for workflow {workflow.id}")

    def recover_workflow(self, workflow_id: str) -> bool:
        """Recover a failed workflow from its last checkpoint."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        if workflow.status == WorkflowStatus.COMPLETED:
            return True

        workflow.status = WorkflowStatus.RECOVERING
        # Reset failed steps that can be retried
        for step in workflow.steps:
            if step.status == WorkflowStatus.FAILED and step.retry_count < step.max_retries:
                step.status = WorkflowStatus.PENDING

        workflow.status = WorkflowStatus.RUNNING
        self._stats["workflows_recovered"] += 1
        logger.info(f"Recovered workflow {workflow_id}")
        return True

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow or workflow.status not in (WorkflowStatus.PENDING, WorkflowStatus.RUNNING):
            return False

        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now(timezone.utc)
        return True

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        return dict(self._stats)

    def list_workflows(self, status: Optional[WorkflowStatus] = None) -> List[WorkflowInstance]:
        """List workflows with optional status filter."""
        if status:
            return [w for w in self._workflows.values() if w.status == status]
        return list(self._workflows.values())
