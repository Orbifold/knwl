import os
from knwl.api.knwl_api.taskiq_broker import TaskLog, TaskLogRepository
from knwl.utils import get_full_path


def get_db_repository() -> TaskLogRepository:
    """
    Initializes and returns a TaskLogRepository instance.

    Returns:
        TaskLogRepository: An instance of the task log repository
    """
    db_path = get_full_path("$/user/default/broker.db")
    if not os.path.exists(db_path):
        return None
    return TaskLogRepository(db_path=db_path)


async def get_all_jobs(amount: int) -> list[TaskLog]:
    """
    Get all log items.

    Args:
        amount: Number of items to fetch
    Returns:
        List of fetched items as TaskLog instances
    """
    db = get_db_repository()
    if db is None:
        return []
    return await db.get_recent_logs(limit=amount)


async def get_jobs_by_id(id: str) -> list[TaskLog]:
    """
    Get log items by Id.

    Args:
        id: Unique identifier for the item to fetch
    Returns:
        List of fetched items as TaskLog instances
    """
    db = get_db_repository()
    if db is None:
        return []
    # Assuming get_by_id returns a single TaskLog or None, we wrap it in a list for consistency
    items = await db.get_task_logs(id)
    return items if items else []


async def get_active_jobs() -> list[TaskLog]:
    """
    Get all active jobs.

    Returns:
        List of active jobs as TaskLog instances
    """
    db = get_db_repository()
    if db is None:
        return []
    return await db.get_started_tasks()
