# ============================================================================================
# This benchmark script uses diverse models and providers to evaluate performance and output.
# ============================================================================================
import sys
import typer
import json
from typing import Optional

sys.path.append("..")
from benchmarks.benchmark import Benchmark
import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.padding import Padding
from knwl.cli.cli_utils import get_version

console = Console()

# ============================================================================================
# Configuration
# ============================================================================================
models = {
    # "ollama": ["qwen2.5:7b"],
    "ollama": [
        "qwen2.5:7b",
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
        "glm-4.7-flash:latest",
    ],
    # "openai": ["gpt-5-mini", "gpt-5-nano-2025-08-07", "gpt-4.1-2025-04-14"],
    "anthropic": ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
}

strategies = ["local", "global", "hybrid", "naive", "self", "none"]
default_strategy = (
    "local"  # Augmentation strategy: local, global, hybrid, naive, self, none
)

# ============================================================================================
# Using different facts of different nature can help to detect model strengths and weaknesses.
# ============================================================================================
facts = {
    "biograph": """Hilbert, the first of two children and only son of Otto, a county judge, and Maria Therese Hilbert (née Erdtmann), the daughter of a merchant, was born in the Province of Prussia, Kingdom of Prussia, either in Königsberg, now Kaliningrad, (according to Hilbert's own statement) or in Wehlau (known since 1946 as Znamensk) near Königsberg where his father worked at the time of his birth. His paternal grandfather was David Hilbert, a judge and Geheimrat. His mother Maria had an interest in philosophy, astronomy and prime numbers, while his father Otto taught him Prussian virtues. After his father became a city judge, the family moved to Königsberg. David's sister, Elise, was born when he was six. He began his schooling aged eight, two years later than the usual starting age.
In late 1872, Hilbert entered the Friedrichskolleg Gymnasium (Collegium fridericianum, the same school that Immanuel Kant had attended 140 years before); but, after an unhappy period, he transferred to (late 1879) and graduated from (early 1880) the more science-oriented Wilhelm Gymnasium. Upon graduation, in autumn 1880, Hilbert enrolled at the University of Königsberg, the Albertina. In early 1882, Hermann Minkowski (two years younger than Hilbert and also a native of Königsberg but had gone to Berlin for three semesters), returned to Königsberg and entered the university. Hilbert developed a lifelong friendship with the shy, gifted Minkowski.""",
    "biomed": """Aspirin, also known as acetylsalicylic acid (ASA), is a medication used to reduce pain, fever, or inflammation. Specific inflammatory conditions which aspirin is used to treat include Kawasaki disease, pericarditis, and rheumatic fever. It has an antiplatelet effect and is often used in the prevention of heart attacks, strokes, and blood clots in people at high risk. Aspirin is also used as a component of some drug cocktails to treat tuberculosis. 
    Common side effects of aspirin include upset stomach, heartburn, and drowsiness. More serious side effects include stomach ulcers, gastrointestinal bleeding, and allergic reactions. Aspirin should not be used in children or teenagers with influenza or chickenpox due to the risk of Reye syndrome. Aspirin works by inhibiting the production of certain natural substances that cause inflammation and pain in the body. It is classified as a nonsteroidal anti-inflammatory drug (NSAID) and is related to other NSAIDs such as ibuprofen and naproxen.""",
}


def collect():
    try:
        console.print("The following models are predefined for benchmarking:")
        console.print("")
        for provider in models:
            console.print(f"- [bold blue]{provider}[/]: {', '.join(models[provider])}")
        console.print("")
        use_predefined = typer.confirm(
            "Use the predefined models and facts? (y/n)", default=True
        )
        console.print("")
        if use_predefined:
            specs = {"models": models, "facts": facts, "strategy": default_strategy}
        else:
            console.print("")

            specs = {}
            specs["models"] = {}
            while True:
                provider = typer.prompt("Enter model provider (or 'done' to finish)")
                if provider.lower() == "done":
                    break
                model_list = []
                while True:
                    model = typer.prompt(
                        f"Enter model name for provider '{provider}' (or 'done' to finish)"
                    )
                    if model.lower() == "done":
                        break
                    model_list.append(model)
                specs["models"][provider] = model_list
            specs["facts"] = {}
            while True:
                fact_key = typer.prompt("Enter fact key (or 'done' to finish)")
                if fact_key.lower() == "done":
                    break
                fact_value = typer.prompt(f"Enter fact value for key '{fact_key}'")
                specs["facts"][fact_key] = fact_value
            console.print("")
        console.print("Available augmentation strategies:")
        for i, opt in enumerate(strategies, start=1):
            typer.echo(f"{i}. {opt}")
        selected_strategy = typer.prompt("Select a strategy", type=int, default=1)
        if selected_strategy < 1 or selected_strategy > len(strategies):
            console.print("[red]That one does not exist. Exiting.[/]")
            return
        selected = strategies[selected_strategy - 1]
        specs["strategy"] = selected
    except Exception as e:
        console.print(f"[red]Error collecting benchmark specifications: {e}[/]")
    # console.print(json.dumps(specs, indent=2))
    if len(specs["models"]) == 0:
        console.print("[red]No models specified. Exiting.[/]")
        return
    if len(specs["facts"]) == 0:
        console.print("[red]No facts specified. Exiting.[/]")
        return
    if specs["strategy"] not in strategies:
        console.print("[red]Invalid strategy specified. Exiting.[/]")
        return
    console.print("\n[bold]Benchmark Specifications:[/]")
    console.print(json.dumps(specs, indent=2))
    console.print("")
    if typer.confirm("Is this correct? (y/n)", default=True, show_default=True):
        return specs
    else:
        console.print("[red]Benchmark cancelled by user. Exiting.[/]")
        return


def main():

    console.print(
        Panel(
            Padding(
                "Knwl Benchmarking Utility\n" f"Version: {get_version()}",
                (1, 2),
            ),
            title="Benchmarking",
        )
    )
    specs = collect()
    benchmark = Benchmark(
        models=specs["models"], facts=specs["facts"], strategy=specs["strategy"]
    )
    asyncio.run(benchmark.run())


if __name__ == "__main__":
    main()
