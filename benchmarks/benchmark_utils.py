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
        provider: str,
        model: str,
        strategy: AugmentationStrategy = "local",
        namespace: str = "benchmark",
    ):

        self.model = model.replace(":", "_")
        self.provider = provider
        self.strategy = strategy
        self.namespace = namespace
        self.knwl = Knwl(namespace=self.namespace, llm=self.provider, model=self.model)

        self.file_path = os.path.join(self.ensure_results_dir(), "ingest.csv")

    def ensure_results_dir(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        dir_path = os.path.join(current_dir, "results", self.provider, self.model)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    async def ingest(self, facts: dict[str, str]) -> None:
        # Initialize CSV file with headers if it doesn't exist
        file_exists = os.path.exists(self.file_path)
        if file_exists:
            os.remove(self.file_path)
        with open(self.file_path, "a", newline="") as csvfile:

            fieldnames = [
                "key",
                "failed",
                "node_count",
                "edge_count",
                "latency",
                "error",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for key, text in facts.items():
                input = KnwlInput(text=text, name=key)
                node_count = 0
                edge_count = 0
                latency = 0.0
                failed = False
                try:
                    start_time = time.perf_counter()
                    result: KnwlGraph = await self.knwl.ingest(input)
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
                    error = ""
                except Exception as e:
                    latency = round(end_time - start_time, 2)
                    node_count = 0
                    edge_count = 0
                    failed = True
                    error = str(e)
                    print(error)

                # Write row to CSV
                writer.writerow(
                    {
                        "key": key,
                        "failed": failed,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "latency": latency,
                        "error": error,
                    }
                )
