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
    # "ollama": ["qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b"],
    "openai": ["gpt-5-mini"],
}

namespace = "benchmark"

strategy = "local"  # Augmentation strategy: local, global, hybrid, naive, self, none

facts = {
    "married": "John is married to Anna.",
    "family": "Anna loves John and how he takes care of the family. The have a beautiful daughter named Helena, she is three years old.",
    "work": "John has been working for the past ten years on AI and robotics. He knows a lot about the subject.",
}


async def run():
    for provider, model_list in models.items():
        for model in model_list:
            print(
                f"Running benchmark for provider '{provider}' with model '{model}'..."
            )
            benchmark = Benchmark(
                provider=provider,
                model=model,
                strategy=strategy,
                namespace=namespace,
            )
            await benchmark.ingest(facts)
            print(
                f"Completed benchmark for provider '{provider}' with model '{model}'.\n"
            )


asyncio.run(run())
