# Changelog

## v1.8.3

- **feature**: Knwl CLI now has backup/restore for the config. Use `knwl config backup` and `knwl config restore` commands.
- **feature**: Knwl CLI exports the knowledge graph in DOT format. Use `knwl graph export --format dot > graph.dot` command. To render the DOT file to an image, you can use Graphviz: `dot -Kneato -Tpng graph.dot -o graph.png`.
- **feature**: `think` parameter added to LLM ask methods to enable/disable "thinking" mode for supported LLMs.
- **feature**: Benchmarking has been rewritten and extended. More user-friendly and added a summary output with key metrics.
- **feature**: HuggingFace LLM implementation added. You can now use Knwl with transformers models from HuggingFace, no setup required.
- **feature**: Wikipedia collector added to Knwl. You can now collect knowledge from Wikipedia articles.
- **other**: benchmarking tells that gpt-oss:20b is the best Ollama model, so this is now the default.
- **other**: default LLM changed to OpenAI's gpt-5-mini. Also based on the benchmarks, this is now the default LLM in Knwl.

## v1.8.2

- **feature**: CLI command to view log entries
- **refactor**: NetworkXGraphStorage has been refectored to improve code clarity and maintainability.
- **feature**: Added export_graph method to Knwl class to export the knowledge graph in various formats (json, csv, ttl, cypher).

## v1.8.1

- **feature**: S3 storage backend implemented for Knwl.
- **other**: CLAUDE.md added.

## v1.8.0

- **feature**: the new CLI allows you to use Knwl from the command line. Run `knwl --help` for more information. Lots of functionality is available, see the `journal/CLI.md` for more details.
- **feature**: the CLI reflects the underlying Knwl API and various methods have been added to support this.

## v1.7.2

- **fix**: return_chunks default value
- **feature**: `Knwl.get_prompt` method wired to the `list_resources` method of the `knwl_api` MCP service.
- **feature**: convenient `merge_into_active_config` method in the config to merge a config snippet into the active configuration.
- **docs**: various typos corrected in the documentation.

## v1.7.1

- **fix**: DI details
- **other**: improved examples
- **test**: namespace can be an absolute path
- **feature**: Knwl.get_edges_between_nodes
- **feature**: Knwl.delete_node_by_id
- **feature**: Knwl.get_node_by_id
- **fix**: toml is not available after packaging.
- **docs**: Readme and quickstart reworked.
- **test**: LLM tests marked.
- **docs**: More readme.
- **perf**: Benchmarks.
- **perf**: A new take on benchmarking.
- **feature**: Multi-model param.
- **feature**: Anthropic added.
- **feature**: Knwl quick API.
