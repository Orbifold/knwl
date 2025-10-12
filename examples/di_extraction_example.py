"""
Example of refactoring existing knwl modules to use dependency injection.

This demonstrates how to modernize the BasicGraphExtraction class to use DI.
"""

from knwl.extraction.graph_extraction_base import GraphExtractionBase
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlGraph import KnwlGraph
from knwl.prompts import prompts
from knwl.utils import parse_llm_record, split_string_by_multi_markers
from knwl.di import service, singleton_service, inject_config, inject_services


class ModernGraphExtraction(GraphExtractionBase):
    """
    Example of BasicGraphExtraction refactored to use dependency injection.
    This shows the before/after comparison of using DI vs manual service management.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuration is still handled normally in __init__
        config = kwargs.get("override", None)
        llm_variant = self.get_param(
            ["graph_extraction", "basic", "llm"], 
            args, kwargs, default="ollama", override=config
        )
        
        # Store the variant for DI to use
        self.llm_variant = llm_variant
        self.config_override = config

    @service('llm')  # This will use the default LLM variant
    def get_extraction_prompt_simple(self, text, entity_types=None, llm=None):
        """Simple version using default LLM configuration."""
        if self.extraction_mode == "fast":
            return prompts.extraction.fast_graph_extraction(text, entity_types)
        elif self.extraction_mode == "full":
            return prompts.extraction.full_graph_extraction(text, entity_types)
        else:
            raise ValueError(f"Unknown extraction mode: {self.extraction_mode}")

    def get_extraction_prompt_with_variant(self, text, entity_types=None):
        """Version that respects the configured LLM variant from __init__."""
        # Use the variant specified in configuration
        llm = self.get_llm(self.llm_variant, override=self.config_override)
        
        if self.extraction_mode == "fast":
            return prompts.extraction.fast_graph_extraction(text, entity_types)
        elif self.extraction_mode == "full":
            return prompts.extraction.full_graph_extraction(text, entity_types)
        else:
            raise ValueError(f"Unknown extraction mode: {self.extraction_mode}")

    @inject_services(
        llm_service='llm',
        storage=('json', 'basic'),
        graph={'service': 'graph', 'variant': 'nx', 'singleton': True}
    )
    async def extract_records_modern(self, text: str, entities: list[str] = None, 
                                   llm_service=None, storage=None, graph=None) -> list[list] | None:
        """
        Modern version using dependency injection for multiple services.
        This shows how DI can inject multiple services at once.
        """
        if not text or text.strip() == "":
            return None
            
        # Use injected LLM service
        extraction_prompt = self.get_extraction_prompt_simple(text, entity_types=entities)
        found = await llm_service.ask(question=extraction_prompt, key=text, category="graph-extraction")
        
        if not found or found.answer.strip() == "":
            return None
            
        records = self.answer_to_records(found.answer)
        
        # Optionally store the extraction for caching
        if storage and records:
            storage.store(f"extraction_{hash(text)}", {
                'text': text,
                'entities': entities,
                'records': records
            })
        
        # Optionally add to knowledge graph
        if graph and records:
            for record in records:
                # Assuming record format: [entity1, relation, entity2]
                if len(record) >= 3:
                    graph.add_edge(record[0], record[2], relation=record[1])
        
        return records

    # Original method using manual service management (for comparison)
    async def extract_records_original(self, text: str, entities: list[str] = None) -> list[list] | None:
        """Original version for comparison - manually manages LLM service."""
        if not text or text.strip() == "":
            return None
            
        # Manual service creation (old way)
        llm = self.get_llm(self.llm_variant, override=self.config_override)
        
        extraction_prompt = self.get_extraction_prompt_with_variant(text, entity_types=entities)
        found = await llm.ask(question=extraction_prompt, key=text, category="graph-extraction")
        
        if not found or found.answer.strip() == "":
            return None
            
        return self.answer_to_records(found.answer)


# Example of a service factory using DI
@service('llm')
@singleton_service('graph', variant='nx')
def create_extraction_pipeline(extraction_mode: str = "full", llm=None, graph=None):
    """
    Factory function that creates a configured extraction pipeline.
    Uses DI to automatically get the required services.
    """
    
    class ExtractionPipeline:
        def __init__(self, llm_service, graph_service, mode):
            self.llm = llm_service
            self.graph = graph_service
            self.mode = mode
        
        async def process_document(self, text: str, entities: list[str] = None):
            """Process a document and add results to the knowledge graph."""
            # Create extraction prompt based on mode
            if self.mode == "fast":
                prompt = prompts.extraction.fast_graph_extraction(text, entities)
            else:
                prompt = prompts.extraction.full_graph_extraction(text, entities)
            
            # Extract using LLM
            result = await self.llm.ask(question=prompt, key=text, category="graph-extraction")
            
            if not result or not result.answer.strip():
                return None
            
            # Parse results and add to graph
            records = parse_llm_record(result.answer)
            added_edges = 0
            
            for record in records:
                if len(record) >= 3:
                    self.graph.add_edge(record[0], record[2], relation=record[1])
                    added_edges += 1
            
            return {
                'records_extracted': len(records),
                'edges_added': added_edges,
                'graph_nodes': self.graph.number_of_nodes(),
                'graph_edges': self.graph.number_of_edges()
            }
    
    return ExtractionPipeline(llm, graph, extraction_mode)


# Example of configuration-driven extraction
@inject_config('graph_extraction.default', 'graph_extraction.basic.mode')
@inject_services(
    llm='llm',
    graph=('graph', 'nx'),
    storage=('vector', 'chroma')
)
async def smart_extraction(text: str, entities: list[str] = None,
                          default=None, mode=None, llm=None, graph=None, storage=None):
    """
    Smart extraction that uses configuration to determine behavior.
    This shows how to combine config injection with service injection.
    """
    
    # Use configuration to determine extraction mode
    extraction_mode = mode or "full"
    
    print(f"Using extraction mode: {extraction_mode}")
    print(f"Default extraction service: {default}")
    
    # Generate appropriate prompt
    if extraction_mode == "fast":
        prompt = prompts.extraction.fast_graph_extraction(text, entities)
    else:
        prompt = prompts.extraction.full_graph_extraction(text, entities)
    
    # Extract using injected LLM
    result = await llm.ask(question=prompt, key=text, category="graph-extraction")
    
    if not result or not result.answer.strip():
        return None
    
    # Parse and process results
    records = parse_llm_record(result.answer)
    
    # Store embeddings for semantic search
    if storage:
        embedding = await llm.embed(text)  # Assuming LLM can create embeddings
        storage.store(f"doc_{hash(text)}", embedding, text)
    
    # Add to knowledge graph
    if graph:
        for record in records:
            if len(record) >= 3:
                graph.add_edge(record[0], record[2], relation=record[1])
    
    return {
        'mode': extraction_mode,
        'records': records,
        'graph_updated': graph is not None,
        'vector_stored': storage is not None
    }


# Example usage functions
async def demonstrate_di_extraction():
    """Demonstrate the DI-enabled extraction system."""
    
    sample_text = """
    John Smith works as a software engineer at Microsoft. 
    He graduated from Stanford University with a degree in Computer Science.
    Microsoft is headquartered in Redmond, Washington.
    """
    
    print("=== DI-Enabled Graph Extraction Demo ===\n")
    
    # 1. Using the factory pattern
    print("1. Creating extraction pipeline with DI factory:")
    pipeline = create_extraction_pipeline(extraction_mode="full")
    result1 = await pipeline.process_document(sample_text)
    print(f"Pipeline result: {result1}\n")
    
    # 2. Using smart extraction with config + service injection
    print("2. Smart extraction with config and service injection:")
    result2 = await smart_extraction(sample_text, entities=['Person', 'Organization', 'Location'])
    print(f"Smart extraction result: {result2}\n")
    
    # 3. Using modern graph extraction class
    print("3. Modern graph extraction class:")
    extractor = ModernGraphExtraction(mode="full")
    records = await extractor.extract_records_modern(sample_text)
    print(f"Extracted records: {records}\n")


# Comparison showing migration benefits
class ComparisonDemo:
    """Demonstrates the benefits of migrating to DI."""
    
    # Old way - manual service management
    def old_way_process(self, text: str, llm_variant: str = "ollama"):
        """Old way: Manual service creation and management."""
        from knwl.services import services
        
        # Manually create services
        llm = services.get_service('llm', variant_name=llm_variant)
        graph = services.get_service('graph', variant_name='nx')
        storage = services.get_service('json', variant_name='basic')
        
        # Manual cleanup and error handling
        try:
            result = self._process_with_services(text, llm, graph, storage)
            return result
        except Exception as e:
            # Manual error management
            print(f"Error processing: {e}")
            return None
    
    # New way - dependency injection
    @inject_services(
        llm='llm',
        graph=('graph', 'nx'),
        storage=('json', 'basic')
    )
    def new_way_process(self, text: str, llm=None, graph=None, storage=None):
        """New way: Services automatically injected."""
        # Services automatically available, with error handling built-in
        return self._process_with_services(text, llm, graph, storage)
    
    def _process_with_services(self, text, llm, graph, storage):
        """Common processing logic."""
        # Simulate processing
        return {
            'text_length': len(text),
            'llm_available': llm is not None,
            'graph_available': graph is not None,
            'storage_available': storage is not None
        }


if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_di_extraction())