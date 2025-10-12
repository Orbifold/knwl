# knwl Dependency Injection System

A comprehensive dependency injection framework for the knwl project that provides decorators for automatic service and configuration injection.

## Quick Start

```python
from knwl import service, singleton_service, inject_config

# Simple service injection
@service('llm', variant='ollama')
def generate_text(prompt: str, llm=None):
    return llm.generate(prompt)

# Singleton service (reuses same instance)
@singleton_service('graph', variant='nx')
def add_node(node_data: dict, graph=None):
    graph.add_node(node_data['id'], **node_data)

# Configuration injection
@inject_config('api.host', 'api.port')
def start_server(host=None, port=None):
    print(f"Starting server on {host}:{port}")
```

## Features

- **Service Injection**: Automatically inject configured services
- **Singleton Support**: Share service instances across function calls
- **Configuration Injection**: Inject values directly from config.py
- **Multi-Service Injection**: Inject multiple services with one decorator
- **Auto-Injection**: Automatically detect and inject based on parameter names
- **Error Handling**: Clear error messages and graceful failure handling
- **Testing Support**: Easy to mock and override services for testing

## Available Decorators

- `@service(name, variant, param_name, override)` - Inject a service instance
- `@singleton_service(name, variant, param_name, override)` - Inject a singleton service
- `@inject_config(*keys)` - Inject configuration values
- `@inject_services(**specs)` - Inject multiple services with flexible specs
- `@auto_inject` - Auto-detect and inject services based on parameter names

## Files Created

- `/knwl/di.py` - Core dependency injection framework
- `/examples/di_examples.py` - Comprehensive usage examples
- `/examples/di_extraction_example.py` - Real-world knwl integration examples
- `/tests/test_di.py` - Complete test suite
- `/docs/dependency_injection.md` - Detailed documentation

## Integration

The DI system is fully integrated with the existing knwl architecture:

- Works with existing `config.py` configuration
- Uses the existing `services.py` service management
- Follows the established `FrameworkBase` patterns
- Maintains backward compatibility

## Testing

All functionality is tested with a comprehensive test suite:

```bash
cd /Users/swa/Desktop/AI/knwl
python -m pytest tests/test_di.py -v
```

All 16 tests pass, covering:
- Basic and advanced service injection
- Configuration injection
- Error handling
- Parameter override behavior
- Complex service specifications

## Benefits

1. **Cleaner Code**: Eliminates manual service creation boilerplate
2. **Better Testing**: Easy to mock and override dependencies
3. **Configuration-Driven**: Services automatically configured from config.py
4. **Flexible**: Multiple decoration patterns for different use cases
5. **Maintainable**: Clear separation of concerns and dependency management
6. **Performance**: Singleton support for expensive-to-create services

The dependency injection system is ready for use and provides a modern, declarative approach to service management in the knwl framework.