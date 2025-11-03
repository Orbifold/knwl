from datetime import datetime
from knwl.knwl import Knwl
from knwl.models import KnwlGraph
from knwl.models.KnwlIngestion import KnwlIngestion
from knwl.models.KnwlInput import KnwlInput
from knwl.models.KnwlParams import AugmentationStrategy
import time
import os
import csv


class Benchmark:

    def __init__(
        self,
        models: dict[str, list[str]] = {},
        facts: dict[str, str] = {},
        strategy: AugmentationStrategy = "local",
    ):

        self.models = models
        self.facts = facts
        self.strategy = strategy
        self.namespace = os.path.join(os.path.dirname(__file__), "knwl_data")

        self.ingest_file_path = os.path.join(
            self.ensure_results_dir(),
            f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if os.path.exists(self.ingest_file_path):
            os.remove(self.ingest_file_path)

    def ensure_results_dir(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        dir_path = os.path.join(
            current_dir,
            "results",
        )
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    async def run(self) -> None:
        await self.ingest()
        await self.ask()

    async def ask(self) -> None:
        pass

    async def ingest(self) -> None:
        fieldnames = [
            "key",
            "provider",
            "model",
            "failed",
            "node_count",
            "edge_count",
            "latency",
            "error",
        ]
        with open(self.ingest_file_path, "a", newline="") as csvfile:

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for provider, model_list in self.models.items():
                for model in model_list:
                    knwl = Knwl(namespace=self.namespace, llm=provider, model=model)
                    print(f"\n\n============ {provider}/{model} =================")

                    for key, text in self.facts.items():
                        input = KnwlInput(text=text, name=key)
                        node_count = 0
                        edge_count = 0
                        latency = 0.0
                        failed = False
                        try:
                            start_time = time.perf_counter()
                            result: KnwlGraph = await knwl.ingest(input)
                            end_time = time.perf_counter()
                            if result is None:
                                latency = end_time - start_time
                                node_count = 0
                                edge_count = 0
                            else:
                                latency = round(end_time - start_time, 2)
                                node_count = len(result.nodes)
                                edge_count = len(result.edges)
                            failed = False
                            error = " "
                        except Exception as e:
                            latency = 0.0
                            node_count = 0
                            edge_count = 0
                            failed = True
                            error = str(e)
                            print(error)
                        if failed:
                            print(f"{key}: {error}")
                        else:
                            print(f"{key}: {node_count}, {edge_count}, {latency}")
                        # Write row to CSV
                        writer.writerow(
                            {
                                "key": key,
                                "provider": provider,
                                "model": model,
                                "failed": failed,
                                "node_count": node_count,
                                "edge_count": edge_count,
                                "latency": latency,
                                "error": error,
                            }
                        )
