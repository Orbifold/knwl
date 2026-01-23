# Changelog

## v1.8.2
- **feature**: CLI command to view log entries

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
