from datetime import datetime
from knwl.knwl import Knwl
from knwl.models import KnwlGraph
from knwl.models.KnwlIngestion import KnwlIngestion
from knwl.models.KnwlInput import KnwlInput
from knwl.models.KnwlParams import AugmentationStrategy
from rich.console import Console
from rich.spinner import Spinner
from rich.panel import Panel
from rich.padding import Padding
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

import time
import os
import csv

# Disable tokenizers parallelism to avoid fork warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

console = Console()


class Benchmark:

    def __init__(
        self,
        models: dict[str, list[str]] = {},
        facts: dict[str, str] = {},
        strategy: AugmentationStrategy = "local",
        metric_weights: dict[str, float] = None,
    ):

        self.models = models
        self.facts = facts
        self.strategy = strategy
        self.namespace = os.path.join(os.path.dirname(__file__), "knwl_data")
        self.results = []
        # Default weights: nodes and edges are more important than speed
        self.metric_weights = metric_weights or {
            "nodes": 0.4,
            "edges": 0.4,
            "latency": 0.2,
        }
        self.benchmark_raw_file = os.path.join(
            self.ensure_results_dir(),
            f"benchmark_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if os.path.exists(self.benchmark_raw_file):
            os.remove(self.benchmark_raw_file)
        self.benchmark_summary_file = os.path.join(
            self.ensure_results_dir(),
            f"benchmark_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if os.path.exists(self.benchmark_summary_file):
            os.remove(self.benchmark_summary_file)

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
        await self.report()

    def calculate_metric(
        self, node_count: int, edge_count: int, latency: float, failed: bool
    ) -> float:
        """
        Calculate a weighted metric for graph extraction quality.

        Higher scores indicate better extraction:
        - More nodes and edges contribute positively
        - Lower latency contributes positively
        - Failed extractions receive a score of 0

        Args:
            node_count: Number of extracted nodes
            edge_count: Number of extracted edges
            latency: Time taken in seconds
            failed: Whether the extraction failed

        Returns:
            Weighted metric score (0 if failed, otherwise positive float)
        """
        if failed:
            return 0.0

        # Node and edge contributions (more is better)
        node_score = self.metric_weights["nodes"] * node_count
        edge_score = self.metric_weights["edges"] * edge_count

        # Latency contribution (lower latency is better, normalized to 0-100 scale)
        # Using inverse with smoothing to avoid division by zero
        latency_score = self.metric_weights["latency"] * (100 / (latency + 1))

        metric = node_score + edge_score + latency_score
        return round(metric, 2)

    async def report(self) -> None:
        """
        Generates a report from the benchmark results.
        """
        console.print(Padding("[bold]Benchmark Report:[/]", (1, 0, 1, 0)))

        console.print("[italic]Metric: higher is better[/italic]\n")
        console.print("[italic]Latency: lower is better[/italic]\n")

        data = {}
        for r in self.results:
            metric = self.calculate_metric(
                r["node_count"], r["edge_count"], r["latency"], r["failed"]
            )
            item = {
                "model": f"{r['provider']}/{r['model']}",
                "failed": r["failed"],
                "node_count": r["node_count"],
                "edge_count": r["edge_count"],
                "latency": r["latency"],
                "metric": metric,
                "error": r["error"],
            }
            if r["key"] not in data:
                data[r["key"]] = [item]
            else:
                data[r["key"]].append(item)
        # sort by metric descending
        data_sorted = {
            k: sorted(v, key=lambda x: x["metric"], reverse=True)
            for k, v in data.items()
        }
        for key, items in data_sorted.items():
            # print as table
            stats_table = Table(
                title=key.upper(), show_header=True, box=box.ROUNDED, padding=(0, 1)
            )
            stats_table.add_column("Name", style="bold cyan")
            stats_table.add_column("Metric", style="white")
            stats_table.add_column("Nodes", style="white")
            stats_table.add_column("Edges", style="white")
            stats_table.add_column("Latency", style="white")
            stats_table.add_column("Failed", style="red")
            for item in items:
                stats_table.add_row(
                    item["model"],
                    str(item["metric"]),
                    str(item["node_count"]),
                    str(item["edge_count"]),
                    str(item["latency"]),
                    "Yes" if item["failed"] else "No",
                )
            console.print(stats_table)
            console.print("")

        console.print(
            Padding(
                f"Raw data: {self.benchmark_raw_file}\nSummary data: {self.benchmark_summary_file}",
                (1, 0, 1, 0),
            )
        )
        # save the summary to CSV
        fieldnames = [
            "key",
            "model",
            "failed",
            "node_count",
            "edge_count",
            "latency",
            "metric",
            "error",
        ]
        # ============================================================================================
        # Summary CSV
        # ============================================================================================
        with open(self.benchmark_summary_file, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for key, items in data_sorted.items():
                for item in items:
                    row = {
                        "key": key,
                        "model": item["model"],
                        "failed": item["failed"],
                        "node_count": item["node_count"],
                        "edge_count": item["edge_count"],
                        "latency": item["latency"],
                        "metric": item["metric"],
                        "error": item["error"],
                    }
                    writer.writerow(row)

        # ============================================================================================
        # Markdown Report
        # ============================================================================================
        md_report_file = self.benchmark_summary_file.replace(".csv", ".md")
        with open(md_report_file, "w") as mdfile:
            mdfile.write(f"# Knwl Benchmark Report\n\n")

            mdfile.write(f"## Summary\n\n")
            mdfile.write(f"With the given metric, models and set of facts, below are the best models for graph extraction:\n\n")
            # take the best model per key
            best_models = {k: v[0] for k, v in data_sorted.items()}
            mdfile.write("| Fast | Best Model | Metric |\n")
            mdfile.write("|-----|------------|--------|\n")
            for key, item in best_models.items():
                mdfile.write(
                    f"| {key} | {item['model']} | {item['metric']} |\n"
                )
            mdfile.write("\n")
            
            
            mdfile.write(f"## Detailed Results\n\n")
            for key, items in data_sorted.items():
                mdfile.write(f"**{key.upper()}**\n\n")
                mdfile.write("| Model | Metric | Nodes | Edges | Latency | Failed |\n")
                mdfile.write("|------|--------|-------|-------|---------|--------|\n")
                for item in items:
                    mdfile.write(
                        f"| {item['model']} | {item['metric']} | {item['node_count']} | {item['edge_count']} | {item['latency']} | {'Yes' if item['failed'] else 'No'} |\n"
                    )
                mdfile.write("\n")

            # mdfile.write("## Raw Data\n\n")

            # # create md table from raw data
            # mdfile.write("| Key | Model | Failed | Nodes | Edges | Latency | Error |\n")
            # mdfile.write("|-----|-------|--------|-------|-------|---------|-------|\n")
            # for r in self.results:
            #     mdfile.write(
            #         f"| {r['key']} | {r['provider']}/{r['model']} | {'Yes' if r['failed'] else 'No'} | {r['node_count']} | {r['edge_count']} | {r['latency']} | {r['error']} |\n"
            #     )

            mdfile.write(
                f"Generated by the [Knwl.ai](https://knwl.ai) Benchmarking Utility on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

        console.print(Padding(f"Markdown report: {md_report_file}", (1, 0, 1, 0)))

    async def ingest(self) -> None:
        """
        Asynchronously run an ingestion benchmark over configured models and facts and persist metrics to CSV.
        This coroutine iterates over self.models (mapping of provider -> list of models) and self.facts (mapping of key -> text),
        instantiates a Knwl client for each provider/model pair, and attempts to ingest each fact while measuring latency
        and collecting simple graph metrics.
        Side effects:
        - Opens self.benchmark_raw_file in append mode and writes CSV rows with the following fieldnames:
            ["key", "provider", "model", "failed", "node_count", "edge_count", "latency", "error"].
            (Note: the header is written each time the method runs, which may cause duplicate headers in the file.)
        - Appends a result dict to self.results for every (provider, model, key) attempt.
        - Prints progress and per-item errors to the configured console and uses a Progress spinner for UX.
        Per-item behavior:
        - Creates a Knwl instance with namespace, llm=provider, model=model and builds a KnwlInput from the fact text.
        - Starts a timer, awaits knwl.ingest(input), stops the timer and records latency.
        - On success:
                - If result is None -> node_count and edge_count are set to 0.
                - Otherwise -> node_count = len(result.nodes), edge_count = len(result.edges).
                - failed is False and error is set to a blank string.
        - On exception:
                - failed is True, node_count/edge_count/latency are set to zero, error is the exception string, and the error is printed.
        - Each attempt writes one CSV row and removes the progress task.

        """

        console.print(Padding("[bold]Starting Ingestion Benchmark...[/]", (1, 0, 1, 0)))
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
        # ============================================================================================
        # Raw CSV
        # ============================================================================================
        with open(self.benchmark_raw_file, "a", newline="") as csvfile:

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for provider, model_list in self.models.items():
                for model in model_list:
                    knwl = Knwl(
                        namespace=self.namespace,
                        llm=provider,
                        model=model,
                        enable_logging=False,
                    )
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                    ) as progress:

                        for key, text in self.facts.items():
                            task = progress.add_task(
                                f"{provider}/{model}/{key}", total=None
                            )

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
                                console.print(f"[red]{error}[/]")
                            console.print("")
                            # if failed:
                            #     console.print(f"[red]{key}: {error}[/]")
                            # else:
                            #     console.print(f"{key}: {node_count}, {edge_count}, {latency}")
                            result = {
                                "key": key,
                                "provider": provider,
                                "model": model,
                                "failed": failed,
                                "node_count": node_count,
                                "edge_count": edge_count,
                                "latency": latency,
                                "error": error,
                            }
                            # Write row to CSV
                            writer.writerow(result)
                            self.results.append(result)
                            progress.remove_task(task)
