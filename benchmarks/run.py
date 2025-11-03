# ============================================================================================
# This benchmark script uses diverse models and providers to evaluate performance and output.
# ============================================================================================
import sys

sys.path.append("..")
from benchmarks.benchmark_utils import Benchmark


import asyncio


# ============================================================================================
# Configuration
# ============================================================================================
models = {
    # "ollama": ["qwen2.5:7b"],
    # "ollama": [
    #     "qwen2.5:7b",
    #     "qwen2.5:14b",
    #     "qwen2.5:32b",
    #     "gemma3:4b",
    #     "gemma3:12b",
    #     "gemma3:27b",
    #     "llama3.1",
    #     "qwen3:8b",
    #     "qwen3:14b",
    #     "gpt-oss:20b",
    #     "mistral",
    # ],
    # "openai": ["gpt-5-mini", "gpt-5-nano-2025-08-07", "gpt-4.1-2025-04-14"],
    "anthropic": ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
}


strategy = "local"  # Augmentation strategy: local, global, hybrid, naive, self, none

facts = {
    "married": "John is married to Anna.",
    "family": "Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.",
    "work": "John has been working for the past ten years on AI and robotics. He knows a lot about the subject.",
    "geo": "John lives in San Francisco, California. It is a beautiful city with a lot of tech companies.",
}


async def run():
    benchmark = Benchmark(models=models, facts=facts, strategy=strategy)
    await benchmark.ingest()


asyncio.run(run())
