You can install Knwl CLI via [pipx](https://github.com/pypa/pipx):

```
git clone https://github.com/Orbifold/knwl.git
cd knwl
python -m pip install --upgrade pipx
python -m pipx install .
```

It keeps the CLI isolated from system Python packages and uses its own virtual environment. If you had it installed before, you can upgrade it with:

```
python -m pipx install --force knwl
```

## CLI Overview

The Knwl CLI provides several command groups to interact with the Knwl knowledge base. The main command groups are:

- `info`: Get information about your Knwl installation and configuration.
- `config`: View and manage Knwl configuration settings.
- `graph`: Inspect and query the knowledge graph stored in Knwl.
- `ask`: Ask questions to the knowledge base using natural language.
- `extract`: Extract knowledge from text without ingesting it into the database.
- `add` / `ingest`: Ingest knowledge from text into the knowledge graph.
- `log`: View and manage Knwl log entries.

Most commands support a `--raw` or `-r` flag to return raw JSON output instead of pretty-printed tables, this allows you to easily pipe the output to other tools or scripts. For example, you write graph types stats to json like so:

```bash
knwl graph types --raw > graph_types.json
```

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

In case you want to backup your current configuration, you can use the `backup` command:

```bash
knwl config backup --path ./backups/
```
or simply

```bash
knwl config backup
```
to save to the default location.

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

To export the knowledge graph in various formats, you can use the `export` command:

```bash
knwl graph export --format json
```
with json being the default you can also use simply `knwl graph export`. To save to file use output redirection:

```bash
knwl graph export --format csv > knowledge_graph.txt
```

**Important**: the csv export is necessarily two files, one for nodes and one for edges, so the above command will only save both into a text file. You can find the two set delimited by `--- NODES ---` and `--- EDGES ---` headers.

The dot format can be exported with:

```bash
knwl graph export --format dot > graph.dot
```
You need [GraphViz](https://graphviz.org) installed to render the DOT file to an image, you can do this with:

```bash
dot -Kneato -Tpng graph.dot -o graph.png
```
On MacOS you can [install GraphViz via Homebrew](https://formulae.brew.sh/formula/graphviz) `brew install graphviz`.


The supported export formats are:

- `json`: Exports the graph as a JSON object containing nodes and edges.
- `csv`: Exports nodes and edges as CSV format (two separate sections).
- `ttl`: Exports the graph in Turtle (TTL) format for RDF data.
- `ntriples`: Exports the graph in N-Triples format for RDF data.
- `xml`: Exports the graph in RDF/XML format.
- `graphml`: Exports the graph in GraphML format.
- `dot`: Exports the graph in DOT format.
- `cypher`: Exports the graph as Cypher commands for use with Neo4j.

You can simply copy/paste the saved Cypher commands into a Neo4j browser to recreate the graph there. Similarly, the RDF formats can be imported into any RDF triple store (e.g. [Apache Jena](https://jena.apache.org), [qlever](https://github.com/ad-freiburg/qlever) and more).


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

## Log Commands

The `log` command group allows you to view and manage Knwl log entries. You can list log items with:

```bash
knwl log list
```

By default, this will return the 10 most recent log items in a pretty-printed table format. If you want to specify a different number of log items to list, you can use the `--amount` or `-a` option:

```bash
knwl log list --amount 20
```

You can also get the raw JSON output of the log items by using the `--raw` or `-r` flag:

```bash
knwl log list --raw
```

You can filter log items by severity level using the `--severity` or `-s` option:

```bash
knwl log list --severity ERROR
```
