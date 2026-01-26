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
from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

# Use Redis in production, InMemory for development
REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL:
    # Production: Redis broker with result backend
    broker = ListQueueBroker(url=REDIS_URL).with_result_backend(
        RedisAsyncResultBackend(redis_url=REDIS_URL, result_ex_time=3600)
    )
else:
    # Development: In-memory broker (includes result backend by default)
    broker = InMemoryBroker()

# Optional: Scheduler for periodic tasks
scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])
