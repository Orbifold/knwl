# ============================================================================================
# Use VSCode Interactive Python for best experience but you can also run this script directly.
# See https://code.visualstudio.com/docs/python/jupyter-support-py
# ============================================================================================
# %%
"""
=============================================================================================
TaskIQ Examples - Async Task Queue for Python

TaskIQ is a distributed task queue built for async Python applications. Unlike Celery, it's
designed from the ground up for async/await patterns, making it ideal for modern Python apps.

Knwl uses TaskIQ inside the FastAPI backend for background knowledge processing tasks.
You can use TaskIQ to offload long-running tasks like document ingestion, ML inference, and
report generation to background workers.

Key Benefits:
- Async-first: Native async/await support throughout
- Multiple brokers: Redis, RabbitMQ, NATS, or in-memory for development
- Type-safe: Full type hints and IDE support
- Dependency injection: Built-in DI system for clean task dependencies
- Middleware: Extensible middleware system for logging, retries, etc.
- Lightweight: Minimal dependencies, fast startup

Installation:
    pip install taskiq
    # Or with specific broker:
    pip install taskiq-redis
    pip install taskiq-aio-pika  # RabbitMQ

=============================================================================================
"""

# %%
"""
=============================================================================================
EXAMPLE 1: Basic Setup with InMemoryBroker (Development)
=============================================================================================
The InMemoryBroker is perfect for development and testing - no external services needed.
"""

import asyncio
from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

# Create an in-memory broker for development
broker = InMemoryBroker()


# Define a simple task
@broker.task
async def add_numbers(a: int, b: int) -> int:
    """Simple task that adds two numbers."""
    return a + b


@broker.task
async def process_data(data: list[str]) -> dict:
    """Process a list of strings and return statistics."""
    return {
        "count": len(data),
        "total_chars": sum(len(s) for s in data),
        "items": data,
    }


# %%
# Run basic tasks
async def example_basic_tasks():
    """Demonstrate basic task execution."""
    # Start the broker (required for InMemoryBroker)
    await broker.startup()

    # Execute task and wait for result
    result = await add_numbers.kiq(5, 3)
    print(f"Task ID: {result.task_id}")

    # Wait for the result
    task_result = await result.wait_result(timeout=5.0)
    print(f"5 + 3 = {task_result.return_value}")

    # Another example
    result = await process_data.kiq(["hello", "taskiq", "world"])
    task_result = await result.wait_result(timeout=5.0)
    print(f"Processed data: {task_result.return_value}")

    await broker.shutdown()


# Uncomment to run:
# asyncio.run(example_basic_tasks())

# %%
"""
=============================================================================================
EXAMPLE 2: Task with Retries and Error Handling
=============================================================================================
TaskIQ supports automatic retries with configurable backoff strategies.
"""

import random
from taskiq import SimpleRetryMiddleware


# Add retry middleware to broker
broker_with_retry = InMemoryBroker().with_middlewares(
    SimpleRetryMiddleware(default_retry_count=3),
)


@broker_with_retry.task(retry_on_error=True)
async def flaky_operation(success_rate: float = 0.5) -> str:
    """Simulates an operation that might fail randomly."""
    if random.random() > success_rate:
        raise Exception("Random failure occurred!")
    return "Operation succeeded!"


@broker_with_retry.task(retry_on_error=True, max_retries=5)
async def fetch_external_data(url: str) -> dict:
    """Simulates fetching data from an external API with retries."""
    # In real code, you'd use aiohttp or httpx here
    await asyncio.sleep(0.1)  # Simulate network delay

    # Simulate occasional failures
    if random.random() < 0.3:
        raise ConnectionError(f"Failed to connect to {url}")

    return {"url": url, "data": "sample response", "status": 200}


# %%
"""
=============================================================================================
EXAMPLE 3: Task Dependencies with Dependency Injection
=============================================================================================
TaskIQ has a built-in dependency injection system similar to FastAPI's Depends.
"""

from taskiq import TaskiqDepends, Context


# Define a dependency
async def get_database_connection() -> dict:
    """Simulated database connection dependency."""
    # In real code, this would return an actual DB connection
    return {"connected": True, "db_name": "knwl_db"}


async def get_current_user() -> str:
    """Get the current user from context."""
    return "system_user"


@broker.task
async def save_to_database(
    data: dict,
    db: dict = TaskiqDepends(get_database_connection),
    user: str = TaskiqDepends(get_current_user),
) -> dict:
    """Task that uses injected dependencies."""
    return {
        "saved": True,
        "data": data,
        "db_info": db,
        "saved_by": user,
    }


# Using TaskiqState for shared state across tasks
@broker.task
async def task_with_context(
    message: str,
    context: Context = TaskiqDepends(),
) -> dict:
    """Access task context including task_id and other metadata."""
    return {
        "message": message,
        "task_id": context.message.task_id,
        "task_name": context.message.task_name,
    }


# %%
"""
=============================================================================================
EXAMPLE 4: Scheduled Tasks (Cron-like)
=============================================================================================
TaskIQ supports scheduled tasks using labels and a scheduler.
"""

# Create a scheduler with the broker
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


# Define a scheduled task using labels
@broker.task(schedule=[{"cron": "*/5 * * * *"}])  # Every 5 minutes
async def periodic_cleanup() -> str:
    """Task that runs every 5 minutes."""
    return f"Cleanup completed at {asyncio.get_event_loop().time()}"


@broker.task(schedule=[{"cron": "0 0 * * *"}])  # Daily at midnight
async def daily_report() -> dict:
    """Generate daily report at midnight."""
    return {
        "report_type": "daily",
        "generated": True,
    }


# For development, you can also schedule tasks programmatically
@broker.task
async def generate_report(report_type: str) -> dict:
    """Generate a report of specified type."""
    await asyncio.sleep(0.5)  # Simulate work
    return {
        "report_type": report_type,
        "status": "completed",
        "rows": 1000,
    }


# %%
"""
=============================================================================================
EXAMPLE 5: Task Priorities and Labels
=============================================================================================
Use labels to categorize tasks and control execution behavior.
"""


@broker.task(
    task_name="high_priority_task", labels={"priority": "high", "queue": "critical"}
)
async def critical_operation(operation_id: str) -> dict:
    """High-priority task that should be processed first."""
    return {"operation_id": operation_id, "priority": "high", "completed": True}


@broker.task(labels={"priority": "low", "queue": "background"})
async def background_indexing(documents: list[str]) -> int:
    """Low-priority background task for indexing documents."""
    await asyncio.sleep(1)  # Simulate indexing work
    return len(documents)


@broker.task(labels={"category": "ml", "gpu_required": "true"})
async def run_ml_inference(model_name: str, input_data: list) -> dict:
    """ML inference task that requires GPU resources."""
    return {
        "model": model_name,
        "predictions": [0.9, 0.1],  # Simulated predictions
        "input_count": len(input_data),
    }


# %%
"""
=============================================================================================
EXAMPLE 6: Custom Middleware for Logging and Metrics
=============================================================================================
Middleware allows you to intercept task execution for logging, metrics, etc.
"""

from taskiq import TaskiqMiddleware, TaskiqMessage, TaskiqResult
import time


class LoggingMiddleware(TaskiqMiddleware):
    """Middleware that logs task execution details."""

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        """Called before task execution."""
        print(f"[LOG] Starting task: {message.task_name} (ID: {message.task_id})")
        # Store start time in labels for duration calculation
        message.labels["_start_time"] = str(time.time())
        return message

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult) -> None:
        """Called after task execution."""
        start_time = float(message.labels.get("_start_time", time.time()))
        duration = time.time() - start_time

        status = "SUCCESS" if not result.is_err else "FAILED"
        print(f"[LOG] Task {message.task_name} {status} in {duration:.3f}s")

        if result.is_err:
            print(f"[LOG] Error: {result.error}")


class MetricsMiddleware(TaskiqMiddleware):
    """Middleware that collects task metrics."""

    def __init__(self):
        self.task_counts: dict[str, int] = {}
        self.task_durations: dict[str, list[float]] = {}

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult) -> None:
        """Collect metrics after task execution."""
        task_name = message.task_name

        # Count executions (track success vs failure)
        status = "success" if not result.is_err else "failure"
        key = f"{task_name}:{status}"
        self.task_counts[key] = self.task_counts.get(key, 0) + 1

        # Track duration if available
        if "_start_time" in message.labels:
            duration = time.time() - float(message.labels["_start_time"])
            if task_name not in self.task_durations:
                self.task_durations[task_name] = []
            self.task_durations[task_name].append(duration)

    def get_stats(self) -> dict:
        """Get collected metrics."""
        return {
            "counts": self.task_counts,
            "avg_durations": {
                name: sum(durations) / len(durations)
                for name, durations in self.task_durations.items()
                if durations
            },
        }


# Create broker with custom middleware
metrics = MetricsMiddleware()
broker_with_logging = InMemoryBroker().with_middlewares(
    LoggingMiddleware(),
    metrics,
)


@broker_with_logging.task
async def tracked_task(x: int) -> int:
    """Task that will be logged and tracked."""
    await asyncio.sleep(0.1)
    return x * 2


# %%
"""
=============================================================================================
EXAMPLE 7: Task Chains and Workflows
=============================================================================================
Build complex workflows by chaining tasks together.
"""


@broker.task
async def extract_text(document_id: str) -> str:
    """Step 1: Extract text from document."""
    await asyncio.sleep(0.1)
    return f"Extracted text from {document_id}"


@broker.task
async def analyze_sentiment(text: str) -> dict:
    """Step 2: Analyze sentiment of text."""
    await asyncio.sleep(0.1)
    return {"text": text[:50], "sentiment": "positive", "score": 0.85}


@broker.task
async def store_results(analysis: dict, document_id: str) -> dict:
    """Step 3: Store analysis results."""
    await asyncio.sleep(0.1)
    return {"stored": True, "document_id": document_id, "analysis": analysis}


async def document_processing_pipeline(document_id: str) -> dict:
    """
    Complete document processing pipeline.
    Chains multiple tasks together in sequence.
    """
    # Step 1: Extract
    extract_handle = await extract_text.kiq(document_id)
    extract_result = await extract_handle.wait_result(timeout=10.0)

    if extract_result.is_err:
        return {"error": "Extraction failed", "document_id": document_id}

    # Step 2: Analyze
    analyze_handle = await analyze_sentiment.kiq(extract_result.return_value)
    analyze_result = await analyze_handle.wait_result(timeout=10.0)

    if analyze_result.is_err:
        return {"error": "Analysis failed", "document_id": document_id}

    # Step 3: Store
    store_handle = await store_results.kiq(analyze_result.return_value, document_id)
    store_result = await store_handle.wait_result(timeout=10.0)

    return store_result.return_value


# %%
"""
=============================================================================================
EXAMPLE 8: Parallel Task Execution
=============================================================================================
Execute multiple tasks in parallel and gather results.
"""


@broker.task
async def fetch_user_data(user_id: int) -> dict:
    """Fetch user data (simulated)."""
    await asyncio.sleep(0.2)
    return {"user_id": user_id, "name": f"User_{user_id}", "active": True}


@broker.task
async def fetch_user_orders(user_id: int) -> list:
    """Fetch user orders (simulated)."""
    await asyncio.sleep(0.3)
    return [{"order_id": i, "user_id": user_id} for i in range(3)]


@broker.task
async def fetch_user_preferences(user_id: int) -> dict:
    """Fetch user preferences (simulated)."""
    await asyncio.sleep(0.1)
    return {"user_id": user_id, "theme": "dark", "notifications": True}


async def get_complete_user_profile(user_id: int) -> dict:
    """
    Fetch complete user profile by running multiple tasks in parallel.
    This is much faster than running them sequentially.
    """
    # Kick off all tasks in parallel
    user_handle = await fetch_user_data.kiq(user_id)
    orders_handle = await fetch_user_orders.kiq(user_id)
    prefs_handle = await fetch_user_preferences.kiq(user_id)

    # Wait for all results
    user_result, orders_result, prefs_result = await asyncio.gather(
        user_handle.wait_result(timeout=5.0),
        orders_handle.wait_result(timeout=5.0),
        prefs_handle.wait_result(timeout=5.0),
    )

    return {
        "user": user_result.return_value,
        "orders": orders_result.return_value,
        "preferences": prefs_result.return_value,
    }


# %%
"""
=============================================================================================
EXAMPLE 9: Integration with Knwl - Async Knowledge Processing
=============================================================================================
Using TaskIQ with Knwl for background knowledge graph operations.
"""

# Note: These tasks would integrate with the Knwl framework
# This shows the pattern for async knowledge processing

knowledge_broker = InMemoryBroker()


@knowledge_broker.task(labels={"category": "ingestion"})
async def ingest_document(document_path: str, source_type: str = "text") -> dict:
    """
    Background task to ingest a document into the knowledge graph.
    In production, this would call Knwl's ingestion methods.
    """
    # Simulated - in real code:
    # from knwl import Knwl
    # knwl = Knwl()
    # await knwl.add_fact(content, source_type)

    await asyncio.sleep(0.5)  # Simulate processing
    return {
        "document": document_path,
        "source_type": source_type,
        "nodes_created": 5,
        "edges_created": 8,
        "status": "ingested",
    }


@knowledge_broker.task(labels={"category": "query"})
async def query_knowledge_graph(question: str, strategy: str = "local") -> dict:
    """
    Background task to query the knowledge graph.
    Useful for long-running complex queries.
    """
    # Simulated - in real code:
    # from knwl import Knwl
    # knwl = Knwl()
    # answer = await knwl.ask(question)

    await asyncio.sleep(0.3)
    return {
        "question": question,
        "strategy": strategy,
        "answer": f"Answer to: {question}",
        "sources": ["doc1", "doc2"],
        "confidence": 0.92,
    }


@knowledge_broker.task(labels={"category": "maintenance"})
async def consolidate_graph() -> dict:
    """
    Background task to consolidate and optimize the knowledge graph.
    Should run periodically to merge duplicate nodes and clean up.
    """
    await asyncio.sleep(1.0)  # Simulate consolidation
    return {
        "nodes_merged": 12,
        "edges_updated": 25,
        "orphans_removed": 3,
        "status": "consolidated",
    }


@knowledge_broker.task(labels={"category": "export"})
async def export_graph(format: str = "graphml", output_path: str = None) -> dict:
    """Export the knowledge graph to a file."""
    await asyncio.sleep(0.5)
    return {
        "format": format,
        "output_path": output_path or f"graph.{format}",
        "nodes_exported": 150,
        "edges_exported": 300,
    }


# %%
"""
=============================================================================================
EXAMPLE 10: Production Setup with Redis Broker
=============================================================================================
For production, use Redis or RabbitMQ as the message broker.
"""

# Uncomment and install taskiq-redis for production use:
# pip install taskiq-redis

"""
from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

# Redis broker with result backend
redis_broker = ListQueueBroker(
    url="redis://localhost:6379",
    queue_name="knwl_tasks",
).with_result_backend(
    RedisAsyncResultBackend(
        redis_url="redis://localhost:6379",
        result_ex_time=3600,  # Results expire after 1 hour
    )
)

@redis_broker.task
async def production_task(data: dict) -> dict:
    '''Task that runs in production with Redis.'''
    return {"processed": data}

# To run workers:
# taskiq worker your_module:redis_broker
"""


# %%
"""
=============================================================================================
EXAMPLE 11: Complete Working Example
=============================================================================================
A complete example that you can run to see TaskIQ in action.
"""


async def main():
    """Complete working example demonstrating TaskIQ features."""
    print("=" * 60)
    print("TaskIQ Complete Example")
    print("=" * 60)

    # Setup broker with middleware
    example_broker = InMemoryBroker().with_middlewares(LoggingMiddleware())

    @example_broker.task
    async def greet(name: str) -> str:
        return f"Hello, {name}!"

    @example_broker.task
    async def compute_sum(numbers: list[int]) -> int:
        await asyncio.sleep(0.1)  # Simulate work
        return sum(numbers)

    @example_broker.task
    async def process_batch(items: list[str]) -> dict:
        await asyncio.sleep(0.2)
        return {
            "processed": len(items),
            "items": [item.upper() for item in items],
        }

    # Start the broker
    await example_broker.startup()

    try:
        # Example 1: Simple task
        print("\n1. Simple greeting task:")
        result = await greet.kiq("TaskIQ User")
        task_result = await result.wait_result(timeout=5.0)
        print(f"   Result: {task_result.return_value}")

        # Example 2: Task with list input
        print("\n2. Compute sum task:")
        result = await compute_sum.kiq([1, 2, 3, 4, 5])
        task_result = await result.wait_result(timeout=5.0)
        print(f"   Sum: {task_result.return_value}")

        # Example 3: Batch processing
        print("\n3. Batch processing task:")
        result = await process_batch.kiq(["apple", "banana", "cherry"])
        task_result = await result.wait_result(timeout=5.0)
        print(f"   Processed: {task_result.return_value}")

        # Example 4: Parallel execution
        print("\n4. Parallel task execution:")
        handles = [compute_sum.kiq([i * 10 for i in range(5)]) for _ in range(3)]
        handles = await asyncio.gather(*handles)
        results = await asyncio.gather(*[h.wait_result(timeout=5.0) for h in handles])
        print(f"   Parallel results: {[r.return_value for r in results]}")

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    finally:
        await example_broker.shutdown()


# Run the complete example
if __name__ == "__main__":
    asyncio.run(main())

# Or in Jupyter/IPython:
# await main()

# %%
"""
=============================================================================================
Summary: When to Use TaskIQ
=============================================================================================

TaskIQ is ideal for:

1. ASYNC APPLICATIONS
   - FastAPI, Starlette, aiohttp backends
   - Any asyncio-based application
   - Avoids the complexity of Celery's sync-to-async bridges

2. BACKGROUND PROCESSING
   - Document ingestion and processing
   - ML model inference
   - Report generation
   - Email/notification sending

3. SCHEDULED TASKS
   - Periodic cleanup jobs
   - Daily/weekly reports
   - Cache invalidation
   - Data synchronization

4. DISTRIBUTED WORKLOADS
   - Spread work across multiple workers
   - Handle high-throughput scenarios
   - Scale horizontally with Redis/RabbitMQ

5. DEVELOPMENT & TESTING
   - InMemoryBroker for local development
   - Easy to test without external dependencies
   - Same code works in dev and production

Key Differences from Celery:
- Native async/await (no sync_to_async needed)
- Lighter weight, faster startup
- Built-in dependency injection
- Type hints throughout
- Modern Python patterns

=============================================================================================
"""
