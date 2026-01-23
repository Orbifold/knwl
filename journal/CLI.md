You can install Knwl CLI via [pipx](https://github.com/pypa/pipx):

```
git clone https://github.com/Orbifold/knwl.git
cd knwl
python -m pip install --upgrade pipx
python -m pipx install .
```

It keeps the CLI isolated from system Python packages and uses its own virtual environment.

## CLI Overview

The Knwl CLI provides several command groups to interact with the Knwl knowledge base. The main command groups are:

- `info`: Get information about your Knwl installation and configuration.
- `config`: View and manage Knwl configuration settings.
- `graph`: Inspect and query the knowledge graph stored in Knwl.
- `ask`: Ask questions to the knowledge base using natural language.
- `extract`: Extract knowledge from text without ingesting it into the database.
- `add` / `ingest`: Ingest knowledge from text into the knowledge graph.

## Info and Configuration Commands

You can get help and list the available commands by running:

```bash
knwl --help
```

or simply `knwl`.

Via the `info` command, you can get information about your Knwl installation:

```bash
knwl info
```

This will not display configuration details but if you type:

```bash
knwl config tree
```

or more compactly:

```bash
knwl config summary
```

you will get readable information about your Knwl configuration. The information returned is a readable version of the actual JSON configuration used by Knwl. If you really want to see the raw JSON configuration, you can type:

```bash
knwl config get all
```

You can fetch the configuration for specific sections too, e.g.,

```bash
knwl config get llm
```

or more specifically:

```bash
knwl config get llm ollama model
```

Note that this will not work as expected because of the way the configuration is structured:

```bash
knwl config get llm default model
```

You can set configuration values using the `set` command. For example:

```bash
knwl config set "llm.ollama.model" "custom_model:1b"
```

You can edit the config manually too, it sits in `~/.knwl/config.json` by default. Configuring Knwl via the CLI like above is (for now) limited to setting string values only and this will cause issues if the value needs to be a number or a boolean. You can work around this by editing the config file directly.

This will be saved to your user configuration file. If you want to reset the configuration to default values, you can use:

```bash
knwl config reset
```

## Graph Commands

The `graph` command group allows you to inspect the knowledge graph stored in Knwl. You can list all node and edges types with:

```bash
knwl graph types
```

You can use `knwl graph stats` as well and if you need only node or edge stats you can use `knwl graph types nodes` or `knwl graph types edges`.

To inspect a specific node type, use:

```bash
knwl graph type Person
```

which will return all nodes of type `Person`. You can replace `Person` with any other node type present in your graph.
There is also a count command:

```bash
knwl graph count nodes
```

which will return the total number of nodes in the graph. You can also count edges with:

```bash
knwl graph count edges
```
Like other commands, you can use the `--raw` or `-r` flag to get raw JSON output.

## Chat Commands

You can ask questions to the knowledge base using the `ask` command:

```bash
knwl ask "Who is Enrico Betti?"
```

If you don't want to use the knowledge graph you can ask the LLM directly with:

```bash
knwl simple "Who is John von Neumann?"
```

or by using the `--simple` flag with the `ask` command:

```bash
knwl ask "Who is John von Neumann?" --simple
```

To extract knowledge without ingesting it into the database, you can use the `extract` command:

```bash
knwl extract "Anna went to school in Johannesburg and married Ian soon thereafter."
```

but if you do want to ingest the knowledge into the graph database, you can use the `ingest` or `add` command:

```bash
knwl add "Anna went to school in Johannesburg and married Ian soon thereafter."
```

Using `extract` will return the extracted knowledge graph in a pretty-printed format. If you want the raw JSON output instead, you can use the `--raw` or `-r` flag:

```bash
knwl extract -r "Anna went to school in Johannesburg and married Ian soon thereafter."
```

and this will return the knowledge graph (and more, like chunking info) as raw JSON.

You can check the graph was augmented by listing the nodes of type `Person`:

```bash
knwl graph type Person
```

The knowledge is both a graph and a vector store, so 'finding' things can be done via semantic similarity or via property matching. To find nodes similar to given text, you can use:

```bash
knwl graph similar "George Washington"
```

This will return nodes that are semantically similar to "George Washington" along with their similarity scores (or distances). There is direct alias and you can also use:

```bash
knwl similar "George Washington"
```
To find nodes matching specific properties (name and description), you can use:

```bash
knwl graph find "George Washington"
```
or 

```bash
knwl find "George Washington"
```
This does not return similarity scores but only nodes that match the given text in their properties.
