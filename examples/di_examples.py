"""
Example usage of the dependency injection system for knwl.
Best used in Jupyter notebooks or Python scripts (VS Code Interactive Python).
"""

# %%
from knwl.di import (
    service,
    singleton_service,
    inject_config,
    inject_services,
    auto_inject,
    ServiceProvider,
)
from knwl.models.KnwlDocument import KnwlDocument
from typing import List


# ============================================================================================
# %%
# Example: Simple service injection
@service("llm")
async def generate_summary(text: str, llm=None) -> str:
    """Generate a summary using the injected LLM service."""
    if llm is None:
        raise ValueError("LLM service not injected")

    prompt = f"Summarize the following text in one sentence:\n\n{text}"
    a = await llm.ask(prompt)
    print("Model used:", llm.model)
    print(a.answer)


await generate_summary(
    "Quantum computing is a fascinating field that explores the use of quantum-mechanical phenomena to perform computation. It has the potential to solve certain problems much faster than classical computers."
)


# ============================================================================================
# %%
# Example: You don't need to use DI if you don't want to
async def quantum_topology() -> str:
    """Generate a summary without using DI."""
    from knwl.llm.ollama import OllamaClient

    llm = OllamaClient(model="gemma3:4b", temperature=0.8)

    a = await llm.ask("What is quantum topology?")
    print("Model used:", llm._model)
    print(a.answer)


await quantum_topology()

# ============================================================================================
# %%
# Example:  config injection with override

config1 = {"number": {"large": {"value": 1000}, "small": {"value": 10}}}


@inject_config("number.large.value", override=config1)
def get_number_from_config(value: int, name: str) -> List[dict]:
    print(f"{name}: {value}")


# Using the function with injected config values
get_number_from_config(name="large")
get_number_from_config(name="small")
# given values override injection
get_number_from_config(name="small", value=42)

# ============================================================================================
# %%
# Example: Singleton service injection (same instance reused)
@singleton_service("graph", variant="nx")
def add_knowledge_node(entity: str, properties: dict, graph=None):
    """Add a node to the knowledge graph."""
    if graph is None:
        raise ValueError("Graph service not injected")

    graph.add_node(entity, **properties)
    return entity


@singleton_service("graph", variant="nx")
def get_node_neighbors(entity: str, graph=None) -> List[str]:
    """Get neighbors of a node in the knowledge graph."""
    if graph is None:
        raise ValueError("Graph service not injected")

    return list(graph.neighbors(entity))


# Example 4: Configuration injection
@inject_config("api.host", "api.port", "logging.level")
def start_api_server(host=None, port=None, level=None):
    """Start the API server with injected configuration."""
    print(f"Starting server on {host}:{port} with logging level {level}")
    # Server startup logic here


# Example 5: Complex multi-service injection
@inject_services(
    llm="llm",
    chunker=("chunking", "tiktoken"),
    storage={"service": "vector", "variant": "chroma", "singleton": True},
    graph={"service": "graph", "variant": "nx", "singleton": True},
)
def process_document(
    document: KnwlDocument, llm=None, chunker=None, storage=None, graph=None
):
    """Process a document using multiple injected services."""
    if not all([llm, chunker, storage, graph]):
        raise ValueError("Required services not injected")

    # Chunk the document
    chunks = chunker.chunk_document(document)

    # Extract entities from chunks
    entities = []
    for chunk in chunks:
        chunk_entities = llm.extract_entities(chunk.text)
        entities.extend(chunk_entities)

    # Store embeddings in vector store
    for chunk in chunks:
        embedding = llm.embed(chunk.text)
        storage.store(chunk.id, embedding, chunk.text)

    # Add entities to knowledge graph
    for entity in entities:
        graph.add_node(entity["name"], **entity.get("properties", {}))

    return {"chunks": len(chunks), "entities": len(entities), "processed": True}


# Example 6: Auto-injection based on parameter names
@auto_inject
def analyze_text(text: str, llm=None, vector=None, graph=None) -> dict:
    """
    Automatically inject services based on parameter names.
    Services 'llm', 'vector', and 'graph' will be auto-injected.
    """
    analysis = {}

    if llm:
        analysis["sentiment"] = llm.analyze_sentiment(text)
        analysis["entities"] = llm.extract_entities(text)

    if vector:
        embedding = llm.embed(text) if llm else None
        if embedding:
            similar_docs = vector.search(embedding, limit=5)
            analysis["similar_documents"] = similar_docs

    if graph:
        analysis["node_count"] = graph.number_of_nodes()
        analysis["edge_count"] = graph.number_of_edges()

    return analysis


# %%
# Example 7: Using ServiceProvider for scoped operations
def batch_process_with_custom_config():
    """Example of using ServiceProvider for configuration overrides."""

    # Custom configuration for this batch
    custom_config = {
        "llm": {
            "custom": {
                "class": "knwl.llm.ollama.OllamaClient",
                "model": "gemma3:4b",  # Different model for this batch
                "temperature": 0.2,
                "context_window": 16384,
            }
        }
    }

    with ServiceProvider() as provider:
        # Create services with custom configuration
        custom_llm = provider.create_service(
            "llm", variant="custom", override=custom_config
        )

        # Process some data with the custom LLM
        result = custom_llm.ask("Explain quantum computing")
        print(f"Custom LLM result: {result}")


# Example 8: Service factory function
@service("llm")
def create_text_processor(model_variant: str = None, llm=None):
    """Factory function that uses injected service to create processors."""

    class TextProcessor:
        def __init__(self, llm_service):
            self.llm = llm_service

        def process(self, text: str) -> dict:
            return {
                "summary": self.llm.summarize(text),
                "entities": self.llm.extract_entities(text),
                "sentiment": self.llm.analyze_sentiment(text),
            }

    return TextProcessor(llm)


# Example 9: Conditional service injection
@service("llm", variant="ollama")
def smart_processing(text: str, use_gpu: bool = False, llm=None):
    """Example showing how to handle conditional logic with DI."""

    if use_gpu and hasattr(llm, "enable_gpu"):
        llm.enable_gpu()

    # Override service configuration if needed
    if use_gpu:
        # Create a new instance with GPU-specific settings
        gpu_override = {
            "llm": {
                "gpu-variant": {
                    "class": "knwl.llm.ollama.OllamaClient",
                    "model": "llama3:70b",  # Larger model for GPU
                    "gpu_layers": 50,
                }
            }
        }
        gpu_llm = ServiceProvider.create_service(
            "llm", variant="gpu-variant", override=gpu_override
        )
        return gpu_llm.generate(text)

    return llm.generate(text)


# Example usage functions
def demonstrate_di_system():
    """Demonstrate the dependency injection system."""

    print("=== Dependency Injection Examples ===\n")

    # Example 1: Simple service injection
    print("1. Simple LLM service injection:")
    try:
        summary = generate_summary(
            "This is a long text that needs to be summarized into a shorter version."
        )
        print(f"Summary: {summary}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Example 2: Configuration injection
    print("2. Configuration injection:")
    try:
        start_api_server()
        print()
    except Exception as e:
        print(f"Error: {e}\n")

    # Example 3: Auto-injection
    print("3. Auto-injection based on parameter names:")
    try:
        analysis = analyze_text("The weather is beautiful today and I feel great!")
        print(f"Analysis: {analysis}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Example 4: Singleton behavior
    print("4. Singleton service behavior:")
    try:
        add_knowledge_node(
            "Python", {"type": "programming_language", "paradigm": "multi"}
        )
        add_knowledge_node("Machine Learning", {"type": "field", "domain": "AI"})
        neighbors = get_node_neighbors("Python")
        print(f"Python neighbors: {neighbors}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Example 5: Service factory
    print("5. Service factory pattern:")
    try:
        processor = create_text_processor()
        result = processor.process("Natural language processing is fascinating!")
        print(f"Processing result: {result}\n")
    except Exception as e:
        print(f"Error: {e}\n")


if __name__ == "__main__":
    demonstrate_di_system()
# %%
