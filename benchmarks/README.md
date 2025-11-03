# Overview

What model works best for a particular dataset? Is bigger always better? How much time does it take to ingest some facts? This benchmark suite is designed to help answer these questions:

- it's a standalone script using Knwl to ingest a set of sentences/facts
- it measures ingestion time and the amount of returned nodes and edges
- LLM output are captured in `knwl_data` and can be re-used or analyzed
- it loops over local (Ollama) and cloud (OpenAI, Anthropic...) LLM providers and different models within each provider
- it's easy to customize and to run.

This benchmark is a stepping stone since:

- it does not consider parsing/OCR time for documents (only ingestion time)
- it does not consider complex content (math, tables, code...)
- it does not consider knowledge graph quality (only quantity of nodes/edges)
- it does not consider multiple languages (only English).

## Some Insights

The following is not in stone but might help to rethink some assumptions about LLMs and their performance on knowledge ingestion tasks:

- bigger models take more time
- smaller models are qualitatively as able as bigger models for knowledge ingestion
- local models (Ollama) are great for privacy but performances are worse than cloud models (unless you have a very powerful GPU setup)
- extracting knowledge is expensive: 3 nodes and 2 edges can take up to 20 seconds with some models
- reasoning models perform worse than non-reasoning models for knowledge ingestion tasks
- bigger models do sometimes extract more nodes/edges but not always: sometimes smaller models do better
- for local development and testing you can use 7b models (gemma3, qwen2.5) which are fast and qualitatively good enough
- worst models (latency and errors) are: gpt-oss, llama3.1 
- best local model is qwen2.5 across all sizes (7b, 14b, 32b)

## Usage

- customize the `models` and `strategies` variables in `benchmarks/run.py` to select which models and strategies to benchmark
- run `uv run run.py` inside the `benchmarks` directory 
- results are printed in the console and saved in a CSV file in the `benchmarks/results` directory.

Note that the results are time stamped and every run will create a new CSV file. The fact that the LLM calls are cached means that subsequent runs with the same configuration will be much faster.


Sample output from November 2025 can be found in the `benchmarks/November2025.csv` file.