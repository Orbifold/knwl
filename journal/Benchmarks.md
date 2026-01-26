What model works best for a particular dataset? Is bigger always better? How much time does it take to ingest some facts?

The benchmark suite in the `benchmarks` directory is designed to help answer these questions:

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

- bigger models take more time, sometimes a lot more time
- smaller models are qualitatively as able as bigger models for knowledge ingestion
- local models (Ollama) are great for privacy but performances are worse than cloud models (unless you have a very powerful GPU setup)
- extracting knowledge is expensive: 3 nodes and 2 edges can take up to 20 seconds with some models
- reasoning models perform worse than non-reasoning models for knowledge ingestion tasks
- bigger models do sometimes extract more nodes/edges but not always: sometimes smaller models do better
- for local development and testing you can use 7b models (gemma3, qwen2.5) which are fast and qualitatively good enough
- worst models (latency and errors) are: gpt-oss, llama3.1
- best local model is qwen2.5 across all sizes (7b, 14b, 32b) with GLM 4.7 Flash being a close second.



## Metric

In order to pick out the model that works best for your data you need to define what "best" means for you. That is, you need to define a metric that combines ingestion time, number of nodes and number of edges in a way that reflects your priorities. There is predefine metric with weights:

`score = (w1 * nodes + w2 * edges) / (w3 * time)`

Where w1, w2, and w3 are weights (sum equal to one) that you can set based on what matters most to you (e.g., if time is more critical, increase w3).

## Usage

You can run the benchmark via the CLI utility:

```bash
uv run knwl-benchmark
```
or simply:

```bash
knwl-benchmark
```
if you installed Knwl via pipx.

It will guide you through some steps to configure and run the benchmark:

- select the provider(s) to benchmark (Ollama, OpenAI, Anthropic...)
- select the facts you wish to ingest
- which strategiy to use.

You can accept the defaults or customize as needed.

Note that the results are time stamped and every run will create a new CSV file. The fact that the **LLM calls are cached** means that subsequent runs with the same configuration will be much faster.


