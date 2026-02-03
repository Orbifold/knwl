from typing import List

from fastapi import APIRouter, HTTPException, status

from knwl.api.knwl_api.taskiq_broker import TaskLog
from knwl.api.knwl_api.routes.broker import service

router = APIRouter()


@router.get(
    "/jobs",
    response_model=List[TaskLog],
    summary="Get recent jobs",
    description="Returns a list of recent task logs from the broker.",
    responses={
        200: {"description": "Successfully retrieved jobs"},
        500: {"description": "Internal server error"},
    },
)
async def get_jobs(amount: int = 100) -> List[TaskLog]:
    """Get a list of recent task logs."""
    try:
        return await service.get_all_jobs(amount=amount)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}",
        )


@router.get(
    "/jobs/{task_id}",
    response_model=List[TaskLog],
    summary="Get jobs by task id",
    description="Returns a list of task log entries for the given task id.",
    responses={
        200: {"description": "Successfully retrieved jobs"},
        404: {"description": "Jobs not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_jobs_by_id(task_id: str) -> List[TaskLog]:
    """Get task logs for a specific task id."""
    try:
        items = await service.get_jobs_by_id(id=task_id)
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No job logs found for id {task_id}",
            )
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve jobs: {str(e)}",
        )


@router.get(
    "/jobs/active",
    response_model=List[TaskLog],
    summary="Get active jobs",
    description="Returns task logs that have started but not completed.",
    responses={
        200: {"description": "Successfully retrieved active jobs"},
        500: {"description": "Internal server error"},
    },
)
async def get_active_jobs() -> List[TaskLog]:
    """Get tasks that started but have not completed."""
    try:
        return await service.get_active_jobs()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active jobs: {str(e)}",
        )

