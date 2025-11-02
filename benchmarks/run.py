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
    "ollama": ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b"],
    "openai": ["gpt-5-mini"],
}
 

strategy = "local"  # Augmentation strategy: local, global, hybrid, naive, self, none

facts = {
    "married": "John is married to Anna.",
    "family": "Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.",
    "work": "John has been working for the past ten years on AI and robotics. He knows a lot about the subject.",
}


async def run():
    benchmark = Benchmark(models=models, facts=facts, strategy=strategy)
    await benchmark.ingest()


asyncio.run(run())
