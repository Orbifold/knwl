# Dependency Injection in knwl

The knwl framework provides a powerful dependency injection (DI) mechanism that automatically manages service instantiation and injection based on your `config.py` configuration. This system allows you to write cleaner, more modular code by automatically providing services to your functions.

## Overview

The DI system is built on top of the existing `config.py` and `services.py` infrastructure. It provides several decorators that can be applied to functions to automatically inject services and configuration values as parameters.

## Core Decorators

### `@service(service_name, variant=None, param_name=None, override=None)`

Injects a service instance into a function parameter. Creates a new instance each time.

```python
from knwl import service

@service('llm', variant='ollama')
def generate_text(prompt: str, llm=None):
    return llm.generate(prompt)

# Usage
result = generate_text("Explain quantum computing")
```

### `@singleton_service(service_name, variant=None, param_name=None, override=None)`

Injects a singleton service instance. The same instance is reused across all calls.

```python
from knwl import singleton_service

@singleton_service('graph', variant='nx')
def add_node(node_data: dict, graph=None):
    graph.add_node(node_data['id'], **node_data)

@singleton_service('graph', variant='nx') 
def get_neighbors(node_id: str, graph=None):
    return list(graph.neighbors(node_id))

# Both functions use the same graph instance
add_node({'id': 'node1', 'type': 'entity'})
neighbors = get_neighbors('node1')
```

### `@inject_config(*config_keys)`

Injects configuration values from `config.py` into function parameters.

```python
from knwl import inject_config

@inject_config('api.host', 'api.port', 'logging.level')
def start_server(host=None, port=None, level=None):
    print(f"Starting server on {host}:{port} with logging {level}")
    # Server logic here

# Automatically uses values from config.py
start_server()
```

### `@inject_services(**service_specs)`

Injects multiple services with flexible specifications.

```python
from knwl import inject_services

@inject_services(
    llm='llm',                                    # Simple service name
    storage=('vector', 'chroma'),                 # Service with variant
    graph={'service': 'graph', 'variant': 'nx', 'singleton': True}  # Full spec
)
def process_document(doc_text: str, llm=None, storage=None, graph=None):
    # Extract entities
    entities = llm.extract_entities(doc_text)
    
    # Store embeddings
    embedding = llm.embed(doc_text)
    storage.store('doc1', embedding, doc_text)
    
    # Add to graph
    for entity in entities:
        graph.add_node(entity['name'], **entity.get('properties', {}))
    
    return len(entities)
```

### `@auto_inject`

Automatically injects services based on parameter names that match service names.

```python
from knwl import auto_inject

@auto_inject
def analyze_content(text: str, llm=None, vector=None, graph=None):
    """
    Parameters 'llm', 'vector', and 'graph' are automatically injected
    if they exist in the configuration and parameter defaults to None.
    """
    results = {}
    
    if llm:
        results['entities'] = llm.extract_entities(text)
        results['sentiment'] = llm.analyze_sentiment(text)
    
    if vector:
        embedding = llm.embed(text) if llm else None
        if embedding:
            results['similar'] = vector.search(embedding, limit=5)
    
    if graph:
        results['graph_stats'] = {
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges()
        }
    
    return results
```

## Advanced Usage

### Custom Parameter Names

You can specify custom parameter names for injected services:

```python
@service('llm', variant='ollama', param_name='language_model')
@service('vector', variant='chroma', param_name='vector_store')
def semantic_search(query: str, language_model=None, vector_store=None):
    query_embedding = language_model.embed(query)
    return vector_store.search(query_embedding)
```

### ServiceProvider for Manual Control

For advanced scenarios, use `ServiceProvider` to manually manage services:

```python
from knwl import ServiceProvider

# Create services manually
provider = ServiceProvider()
llm = provider.create_service('llm', variant='openai')
graph = provider.get_service('graph', variant='nx')  # Singleton

# Use context manager for scoped operations
with ServiceProvider() as provider:
    custom_config = {
        'llm': {
            'custom': {
                'class': 'knwl.llm.ollama.OllamaClient',
                'model': 'llama3:70b',
                'temperature': 0.1
            }
        }
    }
    
    custom_llm = provider.create_service('llm', variant='custom', override=custom_config)
    result = custom_llm.generate("Complex reasoning task")
```

### Configuration Overrides

You can provide configuration overrides for services:

```python
@service('llm', override={'temperature': 0.8, 'max_tokens': 1000})
def creative_writing(prompt: str, llm=None):
    return llm.generate(prompt)
```

## Integration with Existing Code

The DI system integrates seamlessly with your existing knwl codebase. You can gradually adopt it:

### Before (Manual Service Management)
```python
from knwl.services import services

def process_text(text: str, llm_variant: str = None):
    llm = services.get_service('llm', variant_name=llm_variant)
    chunker = services.get_service('chunking', variant_name='tiktoken')
    
    chunks = chunker.chunk_text(text)
    results = []
    for chunk in chunks:
        result = llm.process(chunk)
        results.append(result)
    
    return results
```

### After (Dependency Injection)
```python
from knwl import inject_services

@inject_services(
    llm='llm',
    chunker=('chunking', 'tiktoken')
)
def process_text(text: str, llm=None, chunker=None):
    chunks = chunker.chunk_text(text)
    results = []
    for chunk in chunks:
        result = llm.process(chunk)
        results.append(result)
    
    return results
```

## Configuration Requirements

The DI system works with your existing `config.py`. Make sure your services are properly configured:

```python
# config.py
default_config = {
    "llm": {
        "default": "ollama",
        "ollama": {
            "class": "knwl.llm.ollama.OllamaClient",
            "model": "qwen2.5:14b",
            "temperature": 0.1
        },
        "openai": {
            "class": "knwl.llm.openai.OpenAIClient", 
            "model": "gpt-4o-mini",
            "temperature": 0.1
        }
    },
    "vector": {
        "default": "chroma",
        "chroma": {
            "class": "knwl.storage.chroma_storage.ChromaStorage",
            "path": "$test/vector",
            "collection": "default"
        }
    }
    # ... other services
}
```

## Error Handling

The DI system provides clear error messages for common issues:

```python
@service('nonexistent_service')
def bad_function(text: str, service=None):
    return service.process(text)

# Raises: ValueError: Service variant 'default' for nonexistent_service not found in configuration.
```

## Testing with DI

The DI system works well with testing by allowing you to override injected services:

```python
import pytest
from unittest.mock import Mock

@service('llm')
def process_with_llm(text: str, llm=None):
    return llm.generate(text)

def test_process_with_llm():
    mock_llm = Mock()
    mock_llm.generate.return_value = "mocked result"
    
    # Override the injected service
    result = process_with_llm("test text", llm=mock_llm)
    
    assert result == "mocked result"
    mock_llm.generate.assert_called_once_with("test text")
```

## Best Practices

### 1. Use Singletons for Stateful Services
Use `@singleton_service` for services that maintain state (like graphs, databases):

```python
@singleton_service('graph', variant='nx')
def add_relationship(source: str, target: str, relation: str, graph=None):
    graph.add_edge(source, target, relation=relation)
```

### 2. Use Regular Services for Stateless Operations
Use `@service` for stateless services that can be recreated:

```python
@service('llm', variant='ollama')
def generate_summary(text: str, llm=None):
    return llm.summarize(text)
```

### 3. Combine Multiple Decorators
You can stack decorators for complex scenarios:

```python
@inject_config('processing.batch_size')
@singleton_service('graph', variant='nx')
@service('llm', variant='ollama')
def batch_process(documents: list, batch_size=None, graph=None, llm=None):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        for doc in batch:
            entities = llm.extract_entities(doc.text)
            for entity in entities:
                graph.add_node(entity['name'])
```

### 4. Graceful Degradation
Always check if services were injected successfully:

```python
@service('optional_service')
def flexible_function(data: str, optional_service=None):
    if optional_service:
        return optional_service.advanced_processing(data)
    else:
        # Fallback to basic processing
        return data.upper()
```

## Performance Considerations

- **Singletons**: Use for expensive-to-create services (database connections, large models)
- **Regular Services**: Use for lightweight, stateless services
- **Caching**: The underlying service system handles caching automatically
- **Lazy Loading**: Services are only created when actually called

## Migration Guide

To migrate existing code to use DI:

1. Identify functions that manually create/retrieve services
2. Add appropriate DI decorators
3. Remove manual service creation code
4. Update function signatures to include injected parameters
5. Test that functionality remains the same

The DI system is designed to be non-breaking and can be adopted incrementally throughout your codebase.