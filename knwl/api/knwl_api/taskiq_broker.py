"""
How It Works Now
Development (no Redis):

# Just run the API - uses InMemoryBroker automatically
uvicorn knwl_api.main:app --reload
Production (with Redis):


# Set Redis URL
export REDIS_URL=redis://localhost:6379

# Start the API
uvicorn knwl_api.main:app

# Start a TaskIQ worker (separate process)
taskiq worker knwl_api.taskiq_broker:broker
"""

import os
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional
from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

from taskiq import TaskiqMiddleware, TaskiqMessage, TaskiqResult
import time
from pydantic import BaseModel

from knwl.utils import get_full_path


class TaskLog(BaseModel):
    """Pydantic model for task execution logs."""

    model_config = {"frozen": True}

    id: int
    task_id: str
    task_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


class TaskLogRepository:
    """Repository for managing task execution logs in SQLite."""

    def __init__(self, db_path: str = "task_logs.db"):
        """Initialize the repository with a database path."""
        self.db_path = db_path
        self._initialized = False

    async def initialize(self):
        """Initialize the database schema if it doesn't exist."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    duration REAL,
                    status TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Create index for faster lookups
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_task_id ON task_logs(task_id)
            """
            )
            await db.commit()

        self._initialized = True

    async def log_task_start(self, task_id: str, task_name: str, start_time: float):
        """Log the start of a task execution."""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO task_logs (task_id, task_name, start_time)
                VALUES (?, ?, ?)
            """,
                (task_id, task_name, start_time),
            )
            await db.commit()

    async def log_task_completion(
        self,
        task_id: str,
        end_time: float,
        duration: float,
        status: str,
        error: Optional[str] = None,
    ):
        """Log the completion of a task execution."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE task_logs
                SET end_time = ?, duration = ?, status = ?, error = ?
                WHERE task_id = ?
            """,
                (end_time, duration, status, error, task_id),
            )
            await db.commit()

    async def get_task_logs(self, task_id: str) -> list[TaskLog]:
        """Retrieve all task log by task_id."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM task_logs WHERE task_id = ?", (task_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [TaskLog(**dict(row)) for row in rows]

    async def get_recent_logs(self, limit: int = 100) -> list[TaskLog]:
        """Retrieve recent task logs."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM task_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [TaskLog(**dict(row)) for row in rows]

    async def get_started_tasks(self) -> list[TaskLog]:
        """Retrieve tasks that have started but not completed."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM task_logs WHERE end_time IS NULL ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [TaskLog(**dict(row)) for row in rows]

    async def clear_completed(self):
        """Clear completed task logs."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM task_logs WHERE status = 'SUCCESS'")
            await db.commit()


class LoggingMiddleware(TaskiqMiddleware):
    """Middleware that logs task execution details to SQLite."""

    def __init__(self, repository: TaskLogRepository):
        """Initialize the middleware with a task log repository."""
        self.repository = repository

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        """Called before task execution."""
        start_time = time.time()
        message.labels["_start_time"] = str(start_time)

        # Log task start to database
        await self.repository.log_task_start(
            task_id=message.task_id, task_name=message.task_name, start_time=start_time
        )

        return message

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult) -> None:
        """Called after task execution."""
        start_time = float(message.labels.get("_start_time", time.time()))
        end_time = time.time()
        duration = end_time - start_time
        status = "SUCCESS" if not result.is_err else "FAILED"
        error = str(result.error) if result.is_err else None

        # Log task completion to database
        await self.repository.log_task_completion(
            task_id=message.task_id,
            end_time=end_time,
            duration=duration,
            status=status,
            error=error,
        )

        if result.is_err:
            print(f"[LOG] Error: {result.error}")


# ============================================================================================
# Use Redis in production, InMemory for development
REDIS_URL = os.getenv("REDIS_URL", None)
DB_PATH = get_full_path("$/user/default/broker.db")

if REDIS_URL:
    # Production: Redis broker with result backend
    broker = ListQueueBroker(url=REDIS_URL).with_result_backend(
        RedisAsyncResultBackend(redis_url=REDIS_URL, result_ex_time=3600)
    )
else:
    # Development: In-memory broker (includes result backend by default)
    broker = InMemoryBroker()

# Initialize task log repository and add logging middleware
task_log_repository = TaskLogRepository(db_path=DB_PATH)
broker.add_middlewares(LoggingMiddleware(repository=task_log_repository))

# Optional: Scheduler for periodic tasks
# scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])

# ============================================================================================
