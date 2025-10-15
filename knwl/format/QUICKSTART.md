# Knwl Formatting System - Quick Reference

## Installation

```bash
# Rich is now included in dependencies
uv pip install -e .
```

## 30-Second Start

```python
from knwl.models import KnwlNode
from knwl.format import print_knwl

node = KnwlNode(name="AI", type="Concept")
print_knwl(node)  # Beautiful terminal output!
```

## Common Tasks

### Print to Terminal

```python
from knwl.format import print_knwl

print_knwl(my_model)                    # Full display
print_knwl(my_model, compact=True)      # Compact display
print_knwl(my_list_of_models)           # Format lists
```

### Export to HTML

```python
from knwl.format import render_knwl

# Save to file
render_knwl(my_model, format_type="html", 
           output_file="output.html", full_page=True)

# Get HTML string
from knwl.format import format_knwl
html = format_knwl(my_model, format_type="html")
```

### Export to Markdown

```python
from knwl.format import render_knwl

render_knwl(my_model, format_type="markdown",
           output_file="output.md", add_frontmatter=True)
```

## Adding a Formatter for Your Model

### Step 1: Define Your Model

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    title: str
    count: int
```

### Step 2: Create Terminal Formatter

```python
from knwl.format import register_formatter
from knwl.format.formatter_base import ModelFormatter

@register_formatter(MyModel, "terminal")
class MyModelTerminalFormatter(ModelFormatter):
    def format(self, model: MyModel, formatter, **options):
        # Use formatter helpers
        table = formatter.create_table()
        table.add_column("Field", style="bold yellow")
        table.add_column("Value")
        table.add_row("Title", model.title)
        table.add_row("Count", str(model.count))
        
        return formatter.create_panel(
            table,
            title="My Custom Model"
        )
```

### Step 3: Use It!

```python
from knwl.format import print_knwl

obj = MyModel(title="Test", count=42)
print_knwl(obj)  # Your custom formatter is used!
```

## Formatter Helpers (Terminal)

```python
# Inside your ModelFormatter.format() method:

# Create a panel
formatter.create_panel(content, title="Title", subtitle="Subtitle")

# Create a table
table = formatter.create_table(title="Table Title", columns=["A", "B"])
table.add_row("value1", "value2")

# Create a tree
tree = formatter.create_tree("Root")
tree.add("Child")

# Use theme colors
formatter.theme.PRIMARY       # "cyan"
formatter.theme.SUCCESS       # "green"
formatter.theme.TITLE_STYLE   # "bold cyan"
```

## Format Options

### Terminal Options

```python
print_knwl(graph, 
    compact=True,           # Compact display
    show_nodes=True,        # Show nodes in graphs
    show_edges=True,        # Show edges in graphs
    max_items=10,           # Max items in lists
    show_content=True,      # Show content in documents
    max_content_length=200  # Max content preview length
)
```

### HTML Options

```python
render_knwl(obj, format_type="html",
    output_file="out.html",  # Save to file
    full_page=True,          # Wrap in HTML document
    title="Page Title"       # Document title
)
```

### Markdown Options

```python
render_knwl(obj, format_type="markdown",
    output_file="out.md",    # Save to file
    add_frontmatter=True,    # Add YAML frontmatter
    title="Document Title",  # Frontmatter title
    level=2                  # Heading level
)
```

## Supported Models

All these work out of the box:

- `KnwlNode` - Knowledge nodes
- `KnwlEdge` - Knowledge edges  
- `KnwlGraph` - Knowledge graphs
- `KnwlDocument` - Documents
- `KnwlChunk` - Text chunks
- `KnwlEntity` - Entities
- `KnwlExtraction` - Extraction results
- `KnwlContext` - Context data
- `KnwlResponse` - Query responses

## Examples

```bash
# Run comprehensive demo
python examples/formatting_demo.py

# Run validation tests
python test_formatting.py
```

## Troubleshooting

### Import Errors

```python
# If you get import errors, make sure rich is installed:
uv pip install rich
```

### Formatter Not Found

```python
# Check if formatter is registered:
from knwl.format import get_registry

registry = get_registry()
has_fmt = registry.has_formatter(MyModel, "terminal")
print(f"Formatter registered: {has_fmt}")
```

### Custom Formatter Not Working

```python
# Make sure you're using the decorator:
@register_formatter(MyModel, "terminal")  # ← Don't forget this!
class MyFormatter(ModelFormatter):
    ...

# And import the module where formatter is defined
import my_formatters  # This triggers registration
```

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           User Code                         │
│  print_knwl(node) / format_knwl(node)      │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        FormatterRegistry                    │
│  Maps models → formatters per format type  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      FormatterBase (Terminal/HTML/MD)      │
│  Handles format-specific rendering          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      ModelFormatter (Model-specific)       │
│  Knows how to format each model type       │
└─────────────────────────────────────────────┘
```

## Best Practices

1. **Keep formatters simple** - Focus on presentation, not logic
2. **Use theme constants** - Don't hardcode colors
3. **Support compact mode** - Allow condensed display
4. **Handle empty data** - Gracefully show "No items"
5. **Limit output size** - Use max_items for large lists
6. **Test all formats** - Verify terminal, HTML, and markdown work

## Next Steps

- Read the [full documentation](README.md)
- Explore [examples](../examples/formatting_demo.py)
- Check out [model formatters](terminal/model_formatters.py) for inspiration
- Create your own custom formatters!
