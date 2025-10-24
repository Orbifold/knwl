import time
from collections import Counter
from typing import List

from knwl.chunking.tiktoken_chunking import TiktokenChunking
from knwl.config import get_config

from knwl.models.KnwlChunk import KnwlChunk
from knwl.models.KnwlGragContext import KnwlGragContext
from knwl.models.KnwlDegreeEdge import KnwlDegreeEdge
from knwl.models.KnwlDegreeNode import KnwlDegreeNode
from knwl.models.KnwlDocument import KnwlDocument
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlExtraction import KnwlExtraction
from knwl.models.KnwlGraph import KnwlGraph
from knwl.models.KnwlInput import KnwlInput
from knwl.models.KnwlNode import KnwlNode
from knwl.models.KnwlRagChunk import KnwlRagChunk
from knwl.models.KnwlGragEdge import KnwlGragEdge
from knwl.models.KnwlGragNode import KnwlGragNode
from knwl.models.KnwlGragReference import KnwlGragReference
from knwl.models.KnwlGragText import KnwlGragText
from knwl.models.KnwlResponse import KnwlResponse
from knwl.models.GragParams import GragParams
from knwl.prompts import prompts
from knwl.storage.json_storage import JsonStorage
from knwl.storage.vector_storage_base import VectorStorageBase
from knwl.utils import *
from knwl.logging import log
GRAPH_FIELD_SEP = prompts.constants.GRAPH_FIELD_SEP
DEFAULT_TUPLE_DELIMITER = prompts.constants.DEFAULT_TUPLE_DELIMITER
DEFAULT_RECORD_DELIMITER = prompts.constants.DEFAULT_RECORD_DELIMITER
DEFAULT_COMPLETION_DELIMITER = prompts.constants.DEFAULT_COMPLETION_DELIMITER
DEFAULT_ENTITY_TYPES = prompts.constants.DEFAULT_ENTITY_TYPES




class Knwl:
    """
        This class provides methods for managing and querying a knowledge graph.
        It includes functionalities for inserting sources, creating chunks, extracting entities, merging data into the knowledge graph, and querying the graph using various modes.
    """

    def get_chunker(self):
        method = get_config("chunking", "method", default="tiktoken")
        if method == "tiktoken":
            return TiktokenChunking()
        else:
            raise ValueError(f"Unknown chunking method '{method}'")

    def count_tokens(self, text: str) -> int:
        chunker = self.get_chunker()
        return chunker.count_tokens(text)

    def chunk(self, text: str, origin_id: str = None) -> List[KnwlChunk]:
        chunker = self.get_chunker()
        return chunker.chunk(text, origin_id)

    def __init__(self):
        self.document_storage = JsonStorage(namespace="documents")
        self.chunks_storage = JsonStorage(namespace="chunks")
        self.graph_storage = GraphStorage(namespace="graph")
        self.node_vectors = VectorStorageBase(namespace="nodes")
        self.edge_vectors = VectorStorageBase(namespace="edges")
        self.chunk_vectors = VectorStorageBase(namespace="chunks")

    async def input(self, text: str, name: str = None, description: str = None):
        """
        Processes the input text and inserts it into the database.

        Args:
            text (str): The input text to be processed.
            name (str, optional): An optional name associated with the input text. Defaults to None.
            description (str, optional): An optional description associated with the input text. Defaults to None.

        Returns:
            Coroutine: A coroutine that resolves to the result of the insert operation.
        See Also:
            - :meth:`insert`
            - :meth:`create_kg`

        """
        return await self.insert(KnwlInput(text=text, name=name, description=description))

    async def insert(self, sources: str | List[str] | KnwlInput | List[KnwlInput], basic_rag: bool = False) -> KnwlGraph | None:
        """
        Inserts sources into the knowledge graph and performs various processing steps.

        Args:
            sources (str | List[str]): A single source or a list of sources to be inserted.
            basic_rag (bool, optional): If True, the knowledge graph will not be updated. Defaults to False.

        Returns:
            KnwlGraph | None: The updated knowledge graph if successful, otherwise None.

        Raises:
            Exception: If any error occurs during the insertion process.

        The method performs the following steps:
        1. Saves the sources.
        2. Creates chunks from the new sources.
        3. Extracts entities from the chunks.
        4. Merges the extracted entities into the knowledge graph.
        5. Merges the updated graph into the vector storage.
        6. Saves the document, chunks, graph, node vectors, and edge vectors storage.

        Note:
            If `basic_rag` is True, the method will return None after creating chunks.
        """
        try:
            inputs = Knwl.convert_to_inputs(sources)

            # =================== Sources ========================================
            new_documents = await self.save_sources(inputs)
            if not len(new_documents):
                return None
            # ====================================================================

            # =================== Chunks =========================================
            new_chunks = await self.create_chunks(new_documents)
            # ====================================================================
            if len(new_chunks) == 0 or basic_rag:
                return None

            # =================== Entities =======================================

            extraction: KnwlExtraction = await extract_entities(new_chunks)
            if extraction is None or extraction.nodes is None or len(extraction.nodes) == 0:
                logger.warning("No new entities and relationships found")
                return None
            else:
                # augment the graph
                g = await self.merge_extraction_into_knowledge_graph(extraction)

                # augment the vector storage
                await self.merge_graph_into_vector_storage(g)

                return g
        finally:
            await self.document_storage.save()
            await self.chunks_storage.save()
            if not basic_rag:
                await self.graph_storage.save()
                await self.node_vectors.save()
                await self.edge_vectors.save()
            logger.info("Ingestion done")

    async def create_kg(self, text: str) -> KnwlBasicGraph | None:
        """
        Utility to return a knowledge graph from the given text.
        This does not store any data anywhere and it for testing purposes only.

        Args:
            text (str): The input text from which to create the knowledge graph.

        Returns:
            dict | None: A dictionary representing the knowledge graph if successful,
                         or None if the extraction fails.
        """
        chunks = {KnwlChunk.hash_keys(text): KnwlChunk.from_text(text)}
        extraction: KnwlExtraction = await extract_entities(chunks)
        return await self.extraction_to_graph(extraction)

    async def extraction_to_graph(self, extraction: KnwlExtraction) -> KnwlBasicGraph:
        graph = {"nodes": [], "edges": []}
        id_map = {}
        for name in extraction.nodes:
            nodes = extraction.nodes[name]
            if len(nodes) > 1:
                descriptions = " ".join([n.description for n in nodes])
                if self.count_tokens(descriptions) > config.max_tokens:
                    descriptions = await self.compactify_summary(name, descriptions)
                majority_entity_type = sorted(Counter([dp.type for dp in nodes]).items(), key=lambda x: x[1], reverse=True, )[0][0]
                graph["nodes"].append({"name": name, "type": majority_entity_type, "description": descriptions})
            else:
                node = nodes[0]
                graph["nodes"].append({"id": name, "name": name, "type": node.type, "description": node.description})
        for name in extraction.edges:
            edges = extraction.edges[name]
            match = re.match(r"\((.*?),(.*?)\)", name)
            if match:
                source_id, target_id = match.groups()
                source_id = str.strip(source_id)
                target_id = str.strip(target_id)
            else:
                raise ValueError(f"Invalid edge name '{name}'")
            if len(edges) > 1:
                descriptions = " ".join([e.description for e in edges])
                if self.count_tokens(descriptions) > config.max_tokens:
                    descriptions = await self.compactify_summary(name, descriptions)

                graph["edges"].append({"sourceId": source_id, "targetId": target_id, "description": descriptions})
            else:
                edge = edges[0]
                graph["edges"].append({"sourceId": source_id, "targetId": target_id, "description": edge.description})

        return KnwlBasicGraph.from_json_graph(graph)

    @staticmethod
    def convert_to_inputs(sources: str | List[str] | KnwlInput | List[KnwlInput]) -> List[KnwlInput]:
        """
        Converts a list of source strings into a list of KnwlInput objects.

        Args:
            sources (List[str]): A list of source strings to convert.

        Returns:
            List[KnwlInput]: A list of KnwlInput objects containing the source strings.
        """
        if sources is None:
            raise ValueError("No sources provided")
        if isinstance(sources, str):
            return [KnwlInput(text=sources)]
        elif isinstance(sources, KnwlInput):
            return [sources]
        elif isinstance(sources, list):
            if not len(sources):
                raise ValueError("No sources provided")
            if isinstance(sources[0], str):
                return [KnwlInput(text=s) for s in sources]
            elif isinstance(sources[0], KnwlInput):
                return sources
            else:
                raise ValueError(f"Unknown source type '{type(sources[0])}'")
        else:
            raise ValueError(f"Unknown source type '{type(sources)}'")

    async def create_chunks(self, sources: dict[str, KnwlDocument]) -> dict[str, KnwlChunk]:
        """
        Asynchronously creates and stores chunks from the given sources.

        Args:
            sources (dict[str, KnwlDocument]): A dictionary where keys are source identifiers and values are KnwlSource objects.

        Returns:
            dict: A dictionary of new chunks that were created and stored.

        Raises:
            Any exceptions raised during the process of chunk creation, filtering, or storage.

        The function performs the following steps:
        1. Iterates over the provided sources and creates chunks from the content of each source.
        2. Filters out chunks that are already present in the storage.
        3. Logs a warning if all chunks are already in the storage and returns.
        4. Logs the number of new chunks being inserted.
        5. Inserts the new chunks into the chunks storage.
        6. Updates the chunk vectors storage with the content of the new chunks.
        """
        given_chunks = {}
        for source_key, source in sources.items():
            chunks = {KnwlChunk.hash_keys(source.content): u for u in self.chunk(source.content, source_key)}
            given_chunks.update(chunks)
        new_chunk_keys = await self.chunks_storage.filter_new_ids(list(given_chunks.keys()))
        # the filtered out ones
        actual_chunks: dict[Any, KnwlChunk] = {k: v for k, v in given_chunks.items() if k in new_chunk_keys}

        if not len(actual_chunks):
            logger.warning("All chunks are already in the storage")
            return {}
        logger.info(f"[New Chunks] inserting {len(actual_chunks)} chunk(s)")

        await self.chunks_storage.upsert({k: v.model_dump(mode="json") for k, v in actual_chunks.items()})
        await self.chunk_vectors.upsert({k: {"content": v.content, "id": v.id} for k, v in actual_chunks.items()})
        return actual_chunks

    async def save_sources(self, inputs: List[KnwlInput]) -> dict[str, KnwlDocument]:
        """
        Saves the provided inputs if they are not already present in the storage.

        Args:
            inputs (List[str]): A list of source strings to be saved.

        Returns:
            dict[str, KnwlDocument]: A dictionary of new inputs that were saved,
            where the keys are the hashed source identifiers and the values are
            the corresponding KnwlSource objects.

        Raises:
            ValueError: If the inputs list is empty.

        Logs:
            - A warning if all inputs are already in the storage.
            - An info message indicating the number of new inputs being inserted.
        """
        if not len(inputs):
            raise ValueError("No sources provided")
        new_sources: dict[str, KnwlDocument] = {KnwlDocument.hash_keys(c.text, c.name, c.description): KnwlDocument.from_input(c) for c in inputs}
        new_keys = await self.document_storage.filter_new_ids(list(new_sources.keys()))
        new_sources = {k: v for k, v in new_sources.items() if k in new_keys}
        if not len(new_sources):
            logger.warning("All sources are already in the storage")
            return {}
        logger.info(f"[New Docs] inserting {len(new_sources)} source(s)")
        await self.document_storage.upsert({k: v.model_dump(mode="json") for k, v in new_sources.items() if k in new_keys})
        return new_sources

    async def merge_graph_into_vector_storage(self, g: KnwlGraph):
        """
        Merges nodes and edges into vector storage.

        This asynchronous method processes nodes and edges, creating a dictionary
        for each with hashed keys and specific content. The processed data is then
        upserted into the respective vector storage.

        Args:
            g (KnwlGraph): A KnwlGraph object containing nodes and edges data.

        Returns:
            None
        """

        nodes = {n.id: n.model_dump(mode="json") for n in g.nodes}
        await self.node_vectors.upsert(nodes)

        edges = {e.id: e.model_dump(mode="json") for e in g.edges}
        await self.edge_vectors.upsert(edges)

    async def merge_extraction_into_knowledge_graph(self, g: KnwlExtraction) -> KnwlGraph:
        """
        Asynchronously merges nodes and edges into the graph.

        This method takes in dictionaries of nodes and edges, processes them concurrently,
        and merges them into the graph. It returns the data of all entities and relationships
        that were merged.

        Args:
           g (KnwlExtraction): A KnwlExtraction object containing nodes and edges data.

        Returns:
            tuple: A tuple containing two lists:
                - all_entities_data: A list of data for all merged nodes.
                - all_relationships_data: A list of data for all merged edges.
        """

        nodes = await asyncio.gather(*[self.merge_nodes_into_graph(k, v) for k, v in g.nodes.items()])

        edges = await asyncio.gather(*[self.merge_edges_into_graph(v) for k, v in g.edges.items()])

        # if not len(all_entities_data):  #     logger.warning("Didn't extract any entities, maybe your LLM is not working")  #     return None  # if not len(all_relationships_data):  #     logger.warning(  #         "Didn't extract any relationships, maybe your LLM is not working"  #     )  #     return None  #
        return KnwlGraph(nodes=nodes, edges=edges)

    async def merge_nodes_into_graph(self, entity_name: str, nodes: list[KnwlNode], smart_merge: bool = True) -> KnwlNode:
        """
        Merges a list of nodes into the graph for a given entity.

        This method retrieves an existing node for the specified entity name from the graph storage.
        It then combines the entity types, descriptions, and originId IDs from the existing node and
        the provided nodes data. The combined data is used to update or insert the node back into
        the graph storage.

        Args:
            smart_merge: A boolean flag indicating whether to use smart merging.
            entity_name (str): The name of the entity to merge nodes for.
            nodes (list[dict]): A list of dictionaries containing node data to merge. Each dictionary
                                     should have keys 'entity_type', 'description', and 'source_id'.

        Returns:
            dict: The merged node data including 'entity_id', 'entity_type', 'description', and 'source_id'.
        """
        # count the most common entity type
        majority_entity_type = sorted(Counter([dp.type for dp in nodes]).items(), key=lambda x: x[1], reverse=True, )[0][0]
        entity_id = KnwlNode.hash_keys(entity_name, majority_entity_type)
        found_chunk_ids = []
        found_description = []

        found_node = await self.graph_storage.get_node_by_id(entity_id)
        if found_node is not None:
            found_chunk_ids.extend(found_node.chunkIds)
            found_description.append(found_node.description)

        unique_descriptions = unique_strings([dp.description for dp in nodes] + found_description)
        chunk_ids = unique_strings([dp.chunkIds for dp in nodes] + [found_chunk_ids])
        compactified_description = await Knwl.compactify_summary(entity_id, GRAPH_FIELD_SEP.join(unique_descriptions), smart_merge)
        node = KnwlNode(name=entity_name, type=majority_entity_type, description=compactified_description, chunkIds=chunk_ids)
        await self.graph_storage.upsert_node(entity_id, node.model_dump(mode="json"))
        return node

    async def merge_edges_into_graph(self, edges: List[KnwlEdge], smart_merge: bool = True) -> KnwlEdge | None:
        """
        Merges multiple edges into the graph between the specified originId and target nodes.

        If an edge already exists between the originId and target nodes, it updates the edge with the new data.
        Otherwise, it creates a new edge with the provided data.

        Args:
            smart_merge: A boolean flag indicating whether to use smart merging.
            edges (list[dict]): A list of dictionaries containing edge data. Each dictionary should have the keys:
                - "weight" (float): The weight of the edge.
                - "source_id" (str): The originId ID of the edge.
                - "description" (str): The description of the edge.
                - "keywords" (str): The keywords associated with the edge.

        Returns:
            dict: A dictionary containing the merged edge data with the keys:
                - "sourceId" (str): The originId node ID.
                - "targetId" (str): The target node ID.
                - "description" (str): The merged description of the edge.
                - "keywords" (str): The merged keywords of the edge.
        """
        if edges is None or len(edges) == 0:
            return None
        # all the edges have the same source and target
        source_id: str = edges[0].source_id
        target_id: str = edges[0].targetId
        found_weights = []
        found_chunk_ids = []
        found_description = []
        found_keywords = []

        if await self.graph_storage.edge_exists(source_id, target_id):
            found_edge = await self.graph_storage.get_edge(source_id, target_id)
            found_weights.append(found_edge.weight)
            found_chunk_ids.extend(found_edge.chunkIds)
            found_description.append(found_edge.description)
            found_keywords.extend(found_edge.keywords)
        # accumulate the weight of the relation between the two entities
        weight = sum([dp.weight for dp in edges] + found_weights)
        unique_descriptions = unique_strings([dp.description for dp in edges] + found_description)
        keywords = sorted(unique_strings([dp.keywords for dp in edges] + [found_keywords]))  # sorting is just for convenience
        chunk_ids = unique_strings([dp.chunkIds for dp in edges] + [found_chunk_ids])
        compactified_description = await Knwl.compactify_summary(str((source_id, target_id)), GRAPH_FIELD_SEP.join(unique_descriptions), smart_merge)
        for need_insert_id in [source_id, target_id]:
            if not (await self.graph_storage.node_exists(need_insert_id)):
                # logger.warning(f"Node {need_insert_id} referenced by an edge and not found, creating a new node")
                # await self.graph_storage.upsert_node(need_insert_id, node_data={"chunkIds": chunk_ids, "description": description, "type": '"UNKNOWN"'})
                raise ValueError(f"Node {need_insert_id} referenced by an edge and not found")

        edge = KnwlEdge(source_id=source_id, targetId=target_id, weight=weight, description=compactified_description, keywords=keywords, chunkIds=chunk_ids)
        await self.graph_storage.upsert_edge(source_id, target_id, edge)
        return edge

    @staticmethod
    async def compactify_summary(entity_or_relation_name: str, description: str, smart_merge: bool = True) -> str:
        """
        Given a concatenated description, summarize it if it exceeds the summary_max_tokens limit.
        The GRAPH_FIELD_SEP is used to delimit the concatenated description.

        Args:
            smart_merge:
            entity_or_relation_name (str): The name of the entity or relation.
            description (str): The description to be summarized.

        Returns:
            str: A summarized version of the description if it exceeds the summary_max_tokens limit,
                 otherwise the original description with GRAPH_FIELD_SEP replaced by a space.
        """
        if not smart_merge:
            # simple concatenation
            return description.replace(GRAPH_FIELD_SEP, " ")

        llm_max_tokens = config.max_tokens
        summary_max_tokens = config.summary_max

        tokens = encode(description)
        if len(tokens) < summary_max_tokens:  # No need for summary
            return description.replace(GRAPH_FIELD_SEP, " ")
        prompt_template = PROMPTS["summarize_entity_descriptions"]
        use_description = decode(tokens[:llm_max_tokens])
        descriptions = use_description.split(GRAPH_FIELD_SEP)
        context_base = {'entity_name': entity_or_relation_name, 'description_list': descriptions}
        use_prompt = prompt_template.format(**context_base)
        logger.debug(f"Trigger summary: {entity_or_relation_name}")
        # summary = await  llm.ask(use_prompt, max_tokens=summary_max_tokens)
        summary = await  llm.ask(use_prompt, core_input=" ".join(descriptions))
        return summary.answer

    async def get_references(self, chunk_ids: List[str]) -> List[KnwlGragReference]:
        if not len(chunk_ids):
            return []
        refs = []
        for i, c in enumerate(chunk_ids):
            chunk = await self.chunks_storage.get_by_id(c)
            origin_id = chunk["originId"]
            doc = await self.document_storage.get_by_id(origin_id)
            refs.append(KnwlGragReference(id=origin_id, index=str(i), description=doc["description"], name=doc["name"], timestamp=doc["timestamp"]))
        return refs

    async def query(self, query: str, param: GragParams = GragParams()) -> KnwlResponse:
        """
        Executes a query based on the specified mode in the QueryParam.

        Args:
            query (str): The query string to be executed.
            param (QueryParam, optional): The parameters for the query execution. Defaults to QueryParam().

        Returns:
            response: The response from the query execution.

        Raises:
            ValueError: If the mode specified in param is unknown.
        """
        try:
            start_time = time.time()

            if param.mode == "local":
                response = await self.query_local(query, param)
            elif param.mode == "global":
                response = await self.query_global(query, param)
            elif param.mode == "hybrid":
                response = await self.query_hybrid(query, param)
            elif param.mode == "naive":
                response = await self.query_naive(query, param)
            else:
                response = KnwlResponse(answer=f"Unknown mode {param.mode}")
            end_time = time.time()
            if isinstance(response, str):
                response = KnwlResponse(answer=response, question=query)
            return response
        except Exception as e:
            logger.error(f"Error during query: {e}")
            return KnwlResponse(answer=e.args[0])

    async def query_local(self, query: str, query_param: GragParams) -> KnwlResponse:
        """
        Executes a local query and returns the response.
        The local query takes the neighborhood of the hit nodes and uses the low-level keywords to find the most related text units.

        This method performs the following steps:
        1. Extracts keywords from the given query using a predefined prompt.
        2. Attempts to parse the extracted keywords from the result.
        3. If parsing fails, attempts to clean and re-parse the result.
        4. Retrieves context based on the extracted keywords and query parameters.
        5. Constructs a system prompt using the retrieved context and query parameters.
        6. Executes the query with the constructed system prompt and returns the response.

        Args:
            query (str): The query string to be processed.
            query_param (QueryParam): An object containing parameters for the query.

        Returns:
            str: The response generated from the query. If an error occurs during processing, a failure response is returned.
        """
        context = None
        start_time = time.time()
        keywords_prompt = PROMPTS["keywords_extraction"].format(query=query)

        r = await  llm.ask(keywords_prompt, core_input=query, category=CATEGORY_KEYWORD_EXTRACTION)
        result = r.answer
        try:
            keywords_data = json.loads(result)
            low_keywords = keywords_data.get("low_level_keywords", [])
            low_keywords = ", ".join(low_keywords)

        except json.JSONDecodeError:
            try:
                # todo: this will not work since result is json
                result = (result.replace(keywords_prompt[:-1], "").replace("user", "").replace("model", "").strip())
                result = "{" + result.split("{")[1].split("}")[0] + "}"

                keywords_data = json.loads(result)
                low_keywords = keywords_data.get("low_level_keywords", [])
                low_keywords = ", ".join(low_keywords)
            # Handle parsing error
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                return PROMPTS["fail_response"]
        if low_keywords:
            context = await self.get_local_query_context(low_keywords, query_param)
        rag_time = round(time.time() - start_time, 2)
        if query_param.only_need_context:
            return KnwlResponse(context=context)
        if context is None:
            return PROMPTS["fail_response"]
        sys_prompt_temp = PROMPTS["rag_response"]
        sys_prompt = sys_prompt_temp.format(context_data=context, response_type=query_param.response_type)
        r = await  llm.ask(query, system_prompt=sys_prompt)
        response = r.answer
        if len(response) > len(sys_prompt):
            response = (response.replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())

        return KnwlResponse(question=query, answer=response, context=context, rag_time=rag_time, llm_time=r.timing)

    async def get_local_query_context(self, query, query_param: GragParams) -> KnwlGragContext | None:
        """
        This really is the heart of the whole GraphRAG intelligence.

        Asynchronously retrieves the local query context based on the provided query and query parameters.

        This function performs the following steps:
        1. Queries the node vectors to get the top-k nodes based on the query.
        2. Retrieves node data for the top-k nodes from the graph storage.
        3. Logs a warning if some nodes are missing, indicating potential storage damage or sync issues.
        4. Retrieves node degrees for the top-k nodes.
        5. Finds the most related text units and edges from the entities.
        6. Logs the number of entities, relations, and text units used in the local query.
        7. Converts the entities, relations, and text units into CSV format.
        8. Returns a formatted string containing the entities, relationships, and sources in CSV format.

        Args:
            query (str): The query string to search for.
            query_param (QueryParam): The parameters for the query, including the top_k value.

        Returns:
            str: A formatted string containing the entities, relationships, and sources in CSV format, or None if no results are found.
        """
        primary_nodes = await self.get_primary_nodes(query, query_param)
        if primary_nodes is None:
            return None
        # chunk texts in descending order of importance
        use_texts = await self.get_rag_texts_from_nodes(primary_nodes)
        # the relations with endpoint names in descending order of importance
        use_relations = await self.get_graph_rag_relations(primary_nodes, query_param)

        # ====================== Primary Nodes ==================================
        node_recs = []
        for i, n in enumerate(primary_nodes):
            node_recs.append(KnwlGragNode(id=n.id, index=str(i), name=n.name, type=n.type, description=n.description, order=n.degree))

        # ====================== Relations ======================================
        edge_recs = []
        for i, e in enumerate(use_relations):
            edge_recs.append(KnwlGragEdge(id=e.id, index=str(i), source=e.source, target=e.target, description=e.description, keywords=e.keywords, weight=e.weight, order=e.order))

        # ====================== Chunks ========================================
        chunk_recs = []
        for i, t in enumerate(use_texts):
            chunk_recs.append(KnwlRagChunk(id=t.id, index=str(i), text=t.text, order=t.order))

        # ====================== References ====================================
        refs = await self.get_references([c.id for c in use_texts])

        return KnwlGragContext(nodes=node_recs, edges=edge_recs, chunks=chunk_recs, references=refs)

    async def get_primary_nodes(self, query: str, query_param: GragParams) -> List[KnwlDegreeNode] | None:
        """
        Asynchronously retrieves primary nodes based on a query and query parameters.
        This is essentially a basic RAG step over nodes.

        This function queries the node vectors to get the top-k nodes matching the query.
        It then retrieves the corresponding node data and node degrees from the graph storage.
        If any nodes are missing from the graph storage, a warning is logged.

        Args:
            query (str): The query string used to search for nodes.
            query_param (QueryParam): An object containing query parameters, including top_k.

        Returns:
            List[KnwlDegreeNode] | None: A list of KnwlDegreeNode objects if nodes are found,
                                         otherwise None.
        """
        # node rag: get top-k nodes
        found = await self.node_vectors.nearest(query, top_k=query_param.top_k)
        if not len(found):
            return None
        # todo: translation from vector to node not necessary if the vector storage contains the data as well
        node_datas = await asyncio.gather(*[self.graph_storage.get_node_by_id(r["id"]) for r in found])

        # if the node vector exists but the node isn't in the graph, it's likely that the storage is damaged or not in sync
        if not all([n is not None for n in node_datas]):
            logger.warning("Some nodes are missing, maybe the storage is damaged")
        # degree might also come in one go
        node_degrees = await asyncio.gather(*[self.graph_storage.node_degree(r["name"]) for r in found])
        nodes = [KnwlDegreeNode(degree=d, **n.model_dump(mode="json")) for k, n, d in zip(found, node_datas, node_degrees) if n is not None]
        return nodes

    async def get_attached_edges(self, nodes: List[KnwlNode]) -> List[KnwlEdge]:
        """
        Asynchronously retrieves the edges attached to the given nodes.

        Args:
            nodes (List[KnwlNode]): A list of KnwlNode objects for which to retrieve attached edges.

        Returns:
            List[KnwlEdge]: A list of KnwlEdge objects attached to the given nodes.
        """
        # return await asyncio.gather(*[self.graph_storage.get_node_edges(n.name) for n in nodes])

        return await self.graph_storage.get_attached_edges(nodes)

    @staticmethod
    def get_chunk_ids(nodes: List[KnwlNode] | List[KnwlEdge]) -> List[str]:
        if nodes is None:
            raise ValueError("get_chunk_ids: parameter is None")
        if not len(nodes):
            return []
        lists = [n.chunkIds for n in nodes]
        # flatten the list and remove duplicates
        return unique_strings(lists)

    async def create_chunk_stats_from_edges(self, primary_edges: List[KnwlEdge]) -> dict[str, int]:
        stats = {}
        for edge in primary_edges:
            for chunk_id in edge.chunkIds:
                stats[chunk_id] = stats.get(chunk_id, 0) + 1
        return stats

    async def create_chunk_stats_from_nodes(self, primary_nodes: List[KnwlNode]) -> dict[str, int]:
        """

        This returns for each chunk id in the given primary nodes, how many times it appears in the edges attached to the primary nodes.
        In essence, a chunk is more important if this chunk has many relations between entities within the chunk.
        One could also count the number of nodes present in a chunk as a measure but the relationship is an even stronger indicator of information.

        This method calculates the number of times each chunk appears in the edges attached to the primary nodes.

        Args:
            primary_nodes (List[KnwlNode]): A list of primary nodes to analyze.

        Returns:
            dict[str, int]: A dictionary where the keys are chunk IDs and the values are the counts of how many times each chunk appears in the edges.
        """
        primary_chunk_ids = Knwl.get_chunk_ids(primary_nodes)
        all_edges = await self.get_attached_edges(primary_nodes)
        node_map = {n.id: n for n in primary_nodes}
        edge_chunk_ids = {}
        stats = {}
        for edge in all_edges:
            if edge.source_id not in node_map:
                node_map[edge.source_id] = await self.graph_storage.get_node_by_id(edge.source_id)
            if edge.targetId not in node_map:
                node_map[edge.targetId] = await self.graph_storage.get_node_by_id(edge.targetId)
            # take the chunkId in both nodes
            source_chunks = node_map[edge.source_id].chunkIds
            target_chunks = node_map[edge.targetId].chunkIds
            common_chunk_ids = list(set(source_chunks).intersection(target_chunks))
            edge_chunk_ids[edge.id] = common_chunk_ids
        for chunk_id in primary_chunk_ids:
            # count how many times this chunk appears in the edge_chunk_ids
            stats[chunk_id] = sum([chunk_id in v for v in edge_chunk_ids.values()])
        return stats

    async def get_rag_texts_from_nodes(self, primary_nodes: list[KnwlNode]) -> List[KnwlGragText]:
        """
        Returns the most relevant paragraphs based on the given primary nodes.
        What makes the paragraphs relevant is defined in the `create_chunk_stats_from_nodes` method.

        This method first creates chunk statistics for the provided primary nodes, then retrieves the corresponding text
        for each chunk from the chunk storage. The chunks are then sorted in decreasing order of their count.

        Args:
            primary_nodes (list[KnwlNode]): A list of primary nodes for which to retrieve the graph RAG texts.

        Returns:
            list[dict]: A list of dictionaries, each containing 'count' and 'text' keys, sorted in decreasing order of count.
        """
        stats = await self.create_chunk_stats_from_nodes(primary_nodes)
        graph_rag_chunks = {}
        for i, v in enumerate(stats.items()):
            chunk_id, count = v
            chunk = await self.chunks_storage.get_by_id(chunk_id)
            graph_rag_chunks[chunk_id] = KnwlGragText(order=count, text=chunk["content"], index=str(i), id=chunk_id)
        # in decreasing order of count
        graph_rag_texts = sorted(graph_rag_chunks.values(), key=lambda x: x.order, reverse=True)
        return graph_rag_texts

    async def get_rag_records_from_edges(self, primary_edges: list[KnwlEdge]) -> List[KnwlGragNode]:
        """
        Collects the endpoint nodes of the given primary edges and retrieves their node information. The order corresponds to the degree of the node.

        Args:
            primary_edges (list[KnwlEdge]): A list of primary edges from which to extract node information.
        Returns:
            List[KnwlRagNode]: A list of KnwlRagNode records containing node information and their degrees.
        """

        node_ids = unique_strings([e.source_id for e in primary_edges] + [e.targetId for e in primary_edges])
        all_nodes = await asyncio.gather(*[self.graph_storage.get_node_by_id(n) for n in node_ids])
        all_degrees = await asyncio.gather(*[self.graph_storage.node_degree(n) for n in node_ids])
        records = []
        for i, v in enumerate(zip(all_nodes, all_degrees)):
            n, d = v
            records.append(KnwlGragNode(order=d, name=n.name, type=n.type, description=n.description, id=n.id, index=str(i)))
        return records

    async def get_graph_rag_relations(self, node_datas: list[KnwlDegreeNode], query_param: GragParams) -> List[KnwlGragEdge]:
        all_attached_edges = await self.graph_storage.get_attached_edges(node_datas)
        all_edges_degree = await self.graph_storage.get_edge_degrees(all_attached_edges)
        all_edge_ids = unique_strings([e.id for e in all_attached_edges])
        edge_endpoint_names = await self.graph_storage.get_semantic_endpoints(all_edge_ids)
        all_edges_data = []
        for i, v in enumerate(zip(all_attached_edges, all_edges_degree)):
            e, d = v
            if e is not None:
                all_edges_data.append(KnwlGragEdge(order=d, source=edge_endpoint_names[e.id][0], target=edge_endpoint_names[e.id][1], keywords=e.keywords, description=e.description, weight=e.weight, id=e.id, index=str(i)))
        # sort by edge degree and weight descending
        all_edges_data = sorted(all_edges_data, key=lambda x: (x.order, x.weight), reverse=True)
        return all_edges_data

    async def get_graph_rag_relations_from_edges(self, vector_edges: List[KnwlEdge]) -> List[KnwlGragEdge]:
        edge_degrees = await asyncio.gather(*[self.graph_storage.edge_degree(r.source_id, r.targetId) for r in vector_edges])
        degree_edges = [KnwlDegreeEdge(degree=d, **e.model_dump(mode="json")) for e, d in zip(vector_edges, edge_degrees)]
        degree_edges = sorted(degree_edges, key=lambda x: (x.degree, x.weight), reverse=True)
        edge_endpoint_ids = unique_strings([e.source_id for e in vector_edges] + [e.targetId for e in vector_edges])
        edge_endpoint_names = await self.node_id_to_name(edge_endpoint_ids)
        all_edges_data = []
        for i, e in enumerate(degree_edges):
            if e is not None:
                all_edges_data.append(KnwlGragEdge(order=e.degree, source=edge_endpoint_names[e.source_id], target=edge_endpoint_names[e.targetId], keywords=e.keywords, description=e.description, weight=e.weight, id=e.id, index=str(i)))
        return all_edges_data

    async def node_id_to_name(self, node_ids: List[str]) -> dict[str:str]:
        mapping = {}
        for node_id in node_ids:
            node = await self.graph_storage.get_node_by_id(node_id)
            mapping[node_id] = node.name
        return mapping

    async def query_global(self, query, query_param: GragParams) -> KnwlResponse:
        context = None
        start_time = time.time()

        kw_prompt_temp = PROMPTS["keywords_extraction"]
        kw_prompt = kw_prompt_temp.format(query=query)
        found = await  llm.ask(kw_prompt)
        result = found.answer

        try:
            keywords_data = json.loads(result)
            keywords = keywords_data.get("high_level_keywords", [])
            keywords = ", ".join(keywords)
        except json.JSONDecodeError:
            try:
                result = (result.replace(kw_prompt[:-1], "").replace("user", "").replace("model", "").strip())
                result = "{" + result.split("{")[1].split("}")[0] + "}"

                keywords_data = json.loads(result)
                keywords = keywords_data.get("high_level_keywords", [])
                keywords = ", ".join(keywords)

            except json.JSONDecodeError as e:
                # Handle parsing error
                print(f"JSON parsing error: {e}")
                return PROMPTS["fail_response"]
        if keywords:
            context = await self.get_global_query_context(keywords, query_param)
        rag_time = round(time.time() - start_time, 2)
        if query_param.only_need_context:
            return KnwlResponse(context=context)
        if context is None:
            return PROMPTS["fail_response"]

        sys_prompt_temp = PROMPTS["rag_response"]
        sys_prompt = sys_prompt_temp.format(context_data=context, response_type=query_param.response_type)
        a = await  llm.ask(query, system_prompt=sys_prompt, )
        response = a.answer
        if len(response) > len(sys_prompt):
            response = (response.replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())

        return KnwlResponse(answer=response, context=context, rag_time=rag_time, llm_time=a.timing)

    async def get_naive_query_context(self, chunks: List[KnwlRagChunk], query_param: GragParams):
        chunk_recs = []
        for i, t in enumerate(chunks):
            chunk_recs.append(KnwlRagChunk(id=str(i), text=t.text, order=t.order))
        return KnwlGragContext(chunks=chunk_recs)

    async def get_global_query_context(self, keywords, query_param: GragParams):

        # ====================== Primary Edge ======================================
        primary_edges = await self.edge_vectors.nearest(keywords, top_k=query_param.top_k)
        primary_edges = [KnwlEdge(**r) for r in primary_edges]

        if not len(primary_edges):
            return None

        semantic_edges = await self.get_graph_rag_relations_from_edges(primary_edges)
        # ====================== Relations ======================================
        edge_recs = []
        for i, e in enumerate(semantic_edges):
            edge_recs.append(KnwlGragEdge(index=str(i), id=e.id, source=e.source, target=e.target, description=e.description, keywords=e.keywords, weight=e.weight, order=e.order))

        # ====================== Entities ======================================
        node_recs = []
        use_nodes = await self.get_rag_records_from_edges(primary_edges)
        for i, n in enumerate(use_nodes):
            node_recs.append(KnwlGragNode(index=str(i), id=n.id, name=n.name, type=n.type, description=n.description, order=n.order))

        # ====================== Chunks ========================================
        use_texts = await self.get_rag_texts_from_edges(primary_edges, query_param)
        chunk_recs = []
        for i, t in enumerate(use_texts):
            chunk_recs.append(KnwlRagChunk(index=str(i), text=t.text, order=t.order, id=t.id))

        # ====================== References ====================================
        refs = await self.get_references([c.id for c in use_texts])

        return KnwlGragContext(nodes=node_recs, edges=edge_recs, chunks=chunk_recs, references=refs)

    async def create_description_stats_from_edges(self, primary_edge: list[KnwlEdge], query_param: GragParams):
        stats = {}
        for edge in primary_edge:
            degree = await self.graph_storage.edge_degree(edge.source_id, edge.targetId)
            stats[edge.id] = degree
        return stats

    async def get_rag_texts_from_edges(self, edges: list[KnwlEdge], query_param: GragParams, ) -> List[KnwlGragText]:
        stats = await self.create_chunk_stats_from_edges(edges)
        chunk_ids = unique_strings([e.chunkIds for e in edges])
        coll = []
        for i, chunk_id in enumerate(chunk_ids):
            chunk = await self.chunks_storage.get_by_id(chunk_id)
            coll.append(KnwlGragText(index=str(i), order=stats[chunk_id], text=chunk["content"], id=chunk_id))

        coll = sorted(coll, key=lambda x: x.order, reverse=True)
        return coll

    async def query_naive(self, query, query_param: GragParams) -> KnwlResponse:
        """
        Perform a naive query on the chunk vectors and generate a response.
        This is classic RAG without using the knowledge graph.

        Args:
            query (str): The query string to be processed.
            query_param (QueryParam): An instance of QueryParam containing parameters for the query.

        Returns:
            str: The generated response based on the query and parameters. If no results are found, returns a fail response prompt.
        """
        # =========================Standard RAG ===================================
        start_time = time.time()
        rag_chunks = await self.chunk_vectors.nearest(query, top_k=query_param.top_k)

        if not len(rag_chunks):
            return KnwlResponse(answer="No vectors found to answer the question.", context=None)
        chunks = []
        for i, chunk in enumerate(rag_chunks):
            chunks.append(KnwlRagChunk(id=chunk["id"], text=truncate_content(chunk["content"], config.max_tokens), order=0, index=str(i)))
        refs = await self.get_references([c.id for c in chunks])
        context = KnwlGragContext(chunks=chunks, references=refs)

        rag_time = round(time.time() - start_time, 2)

        if query_param.only_need_context:
            return KnwlResponse(context=context, rag_time=rag_time, llm_time=0.0)

        sys_prompt_temp = PROMPTS["naive_rag_response"]
        sys_prompt = sys_prompt_temp.format(content_data=context.get_documents(), response_type=query_param.response_type)
        r = await  llm.ask(query, system_prompt=sys_prompt, category=CATEGORY_NAIVE_QUERY)
        response = r.answer
        if len(response) > len(sys_prompt):
            response = (response[len(sys_prompt):].replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())

        return KnwlResponse(answer=response, context=context, rag_time=rag_time, llm_time=r.timing)

    async def query_hybrid(self, query, query_param: GragParams) -> KnwlResponse:
        low_level_context = None
        high_level_context = None

        kw_prompt_temp = PROMPTS["keywords_extraction"]
        kw_prompt = kw_prompt_temp.format(query=query)
        start_time = time.time()

        r = await  llm.ask(kw_prompt)
        result = r.answer
        try:
            keywords_data = json.loads(result)
            hl_keywords = keywords_data.get("high_level_keywords", [])
            ll_keywords = keywords_data.get("low_level_keywords", [])
            hl_keywords = ", ".join(hl_keywords)
            ll_keywords = ", ".join(ll_keywords)
        except json.JSONDecodeError:
            try:
                result = (result.replace(kw_prompt[:-1], "").replace("user", "").replace("model", "").strip())
                result = "{" + result.split("{")[1].split("}")[0] + "}"

                keywords_data = json.loads(result)
                hl_keywords = keywords_data.get("high_level_keywords", [])
                ll_keywords = keywords_data.get("low_level_keywords", [])
                hl_keywords = ", ".join(hl_keywords)
                ll_keywords = ", ".join(ll_keywords)
            # Handle parsing error
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                return PROMPTS["fail_response"]

        if ll_keywords:
            low_level_context = await self.get_local_query_context(ll_keywords, query_param)

        if hl_keywords:
            high_level_context = await self.get_global_query_context(hl_keywords, query_param)

        context = KnwlGragContext.combine(high_level_context, low_level_context)
        rag_time = round(time.time() - start_time, 2)

        if query_param.only_need_context:
            return KnwlResponse(context=context, rag_time=rag_time, llm_time=0.0)
        if context is None:
            return PROMPTS["fail_response"]

        sys_prompt_temp = PROMPTS["rag_response"]
        sys_prompt = sys_prompt_temp.format(context_data=context, response_type=query_param.response_type)
        r = await  llm.ask(query, system_prompt=sys_prompt, )
        response = r.answer
        if len(response) > len(sys_prompt):
            response = (response.replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())
        return KnwlResponse(answer=response, context=context, llm_time=r.timing, rag_time=rag_time)

    async def count_documents(self):
        return await self.document_storage.count()
