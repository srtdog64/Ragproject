"""
Background Task Manager for async operations
Handles long-running tasks like document ingestion
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    """Information about a background task"""
    id: str
    type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    total: int = 0
    current_item: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "total": self.total,
            "current_item": self.current_item,
            "progress_percentage": (self.progress / self.total * 100) if self.total > 0 else 0,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata
        }

class TaskManager:
    """Manages background tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        
    async def create_task(
        self, 
        task_type: str,
        task_func: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Create and start a new background task
        
        Args:
            task_type: Type of task (e.g., "ingest", "reindex")
            task_func: Async function to run
            *args, **kwargs: Arguments for the task function
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        # Create task info
        task_info = TaskInfo(
            id=task_id,
            type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        async with self._lock:
            self.tasks[task_id] = task_info
        
        # Create asyncio task
        async_task = asyncio.create_task(
            self._run_task(task_id, task_func, *args, **kwargs)
        )
        
        async with self._lock:
            self.running_tasks[task_id] = async_task
        
        logger.info(f"Created background task {task_id} of type {task_type}")
        return task_id
    
    async def _run_task(
        self,
        task_id: str,
        task_func: Callable,
        *args,
        **kwargs
    ):
        """Run a task and update its status"""
        task_info = self.tasks[task_id]
        
        try:
            # Update status to running
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.now()
            
            logger.info(f"Starting task {task_id}")
            
            # Run the actual task
            # Pass task_info so the task can update progress
            result = await task_func(task_info, *args, **kwargs)
            
            # Update status to completed
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now()
            task_info.result = result
            task_info.progress = task_info.total  # Ensure progress is 100%
            
            logger.info(f"Task {task_id} completed successfully")
            
        except asyncio.CancelledError:
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now()
            logger.info(f"Task {task_id} was cancelled")
            raise
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.now()
            task_info.error = str(e)
            logger.error(f"Task {task_id} failed: {e}")
            
        finally:
            # Remove from running tasks
            async with self._lock:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
    
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information"""
        return self.tasks.get(task_id)
    
    async def get_all_tasks(self) -> List[TaskInfo]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    async def get_active_tasks(self) -> List[TaskInfo]:
        """Get currently running tasks"""
        return [
            task for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        async with self._lock:
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                logger.info(f"Cancelled task {task_id}")
                return True
        return False
    
    async def cleanup_old_tasks(self, days: int = 7):
        """Remove completed tasks older than specified days"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        async with self._lock:
            to_remove = []
            for task_id, task_info in self.tasks.items():
                if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    and task_info.completed_at
                    and task_info.completed_at < cutoff):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
                logger.info(f"Cleaned up old task {task_id}")
            
            return len(to_remove)

# Global task manager instance
_task_manager: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    """Get the global task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
