import warnings
from collections import Counter
from dataclasses import asdict
from typing import List
from urllib.parse import uses_query

from knwl.entities import extract_entities
from knwl.graphStorage import GraphStorage
from knwl.jsonStorage import JsonStorage
from knwl.llm import ollama_chat
from knwl.logging import set_logger
from knwl.prompt import GRAPH_FIELD_SEP, PROMPTS
from knwl.settings import settings
from knwl.tokenize import chunk, encode, decode, truncate_list_by_token_size
from knwl.utils import *
from knwl.utils import KnwlGraph, KnwlNode, KnwlEdge
from knwl.vectorStorage import VectorStorage

logger = set_logger()


class Simple:
    def __init__(self):
        self.document_storage = JsonStorage(namespace="documents")
        self.chunks_storage = JsonStorage(namespace="chunks")
        self.graph_storage = GraphStorage(namespace="graph")
        self.node_vectors = VectorStorage(namespace="nodes")
        self.edge_vectors = VectorStorage(namespace="edges")
        self.chunk_vectors = VectorStorage(namespace="chunks")

    async def insert(self, sources: str | List[str], basic_rag: bool = False) -> KnwlGraph | None:
        try:
            if isinstance(sources, str):
                sources = [sources]

            # =================== Sources ========================================
            new_sources = await self.save_sources(sources)
            if not len(new_sources):
                return None
            # ====================================================================

            # =================== Chunks =========================================
            new_chunks = await self.create_chunks(new_sources)
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
            chunks = {hash_with_prefix(u.content, prefix="chunk-"): u for u in chunk(source.content, source_key)}
            given_chunks.update(chunks)
        new_chunk_keys = await self.chunks_storage.filter_new_ids(list(given_chunks.keys()))
        # the filtered out ones
        actual_chunks: dict[Any, KnwlChunk] = {k: v for k, v in given_chunks.items() if k in new_chunk_keys}

        if not len(actual_chunks):
            logger.warning("All chunks are already in the storage")
            return {}
        logger.info(f"[New Chunks] inserting {len(actual_chunks)} chunk(s)")

        await self.chunks_storage.upsert(actual_chunks)
        await self.chunk_vectors.upsert({k: {"content": v.content} for k, v in actual_chunks.items()})
        return actual_chunks

    async def save_sources(self, sources: List[str]) -> dict[str, KnwlDocument]:
        """
        Saves the provided sources if they are not already present in the storage.

        Args:
            sources (List[str]): A list of source strings to be saved.

        Returns:
            dict[str, KnwlDocument]: A dictionary of new sources that were saved,
            where the keys are the hashed source identifiers and the values are
            the corresponding KnwlSource objects.

        Raises:
            ValueError: If the sources list is empty.

        Logs:
            - A warning if all sources are already in the storage.
            - An info message indicating the number of new sources being inserted.
        """
        if not len(sources):
            return {}
        new_sources: dict[str, KnwlDocument] = {hash_with_prefix(c.strip(), prefix="doc-"): KnwlDocument(c.strip()) for c in sources}
        new_keys = await self.document_storage.filter_new_ids(list(new_sources.keys()))
        new_sources = {k: v for k, v in new_sources.items() if k in new_keys}
        if not len(new_sources):
            logger.warning("All sources are already in the storage")
            return {}
        logger.info(f"[New Docs] inserting {len(new_sources)} source(s)")
        await self.document_storage.upsert(new_sources)
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

        nodes = {n.id: asdict(n) for n in g.nodes}
        await self.node_vectors.upsert(nodes)

        # todo: research the effect of these combinations
        edges = {e.id: asdict(e) for e in g.edges}
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
        compactified_description = await Simple.compactify_summary(entity_id, GRAPH_FIELD_SEP.join(unique_descriptions), smart_merge)
        node = KnwlNode(name=entity_name, type=majority_entity_type, description=compactified_description, chunkIds=chunk_ids)
        await self.graph_storage.upsert_node(entity_id, asdict(node))
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
                - "src_id" (str): The originId node ID.
                - "tgt_id" (str): The target node ID.
                - "description" (str): The merged description of the edge.
                - "keywords" (str): The merged keywords of the edge.
        """
        if edges is None or len(edges) == 0:
            return None
        # all the edges have the same source and target
        source_id: str = edges[0].sourceId
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
        compactified_description = await Simple.compactify_summary(str((source_id, target_id)), GRAPH_FIELD_SEP.join(unique_descriptions), smart_merge)
        for need_insert_id in [source_id, target_id]:
            if not (await self.graph_storage.node_exists(need_insert_id)):
                # logger.warning(f"Node {need_insert_id} referenced by an edge and not found, creating a new node")
                # await self.graph_storage.upsert_node(need_insert_id, node_data={"chunkIds": chunk_ids, "description": description, "type": '"UNKNOWN"'})
                raise ValueError(f"Node {need_insert_id} referenced by an edge and not found")

        edge = KnwlEdge(sourceId=source_id, targetId=target_id, weight=weight, description=compactified_description, keywords=keywords, chunkIds=chunk_ids)
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

        llm_max_tokens = settings.max_tokens
        summary_max_tokens = settings.summary_max

        tokens = encode(description)
        if len(tokens) < summary_max_tokens:  # No need for summary
            return description.replace(GRAPH_FIELD_SEP, " ")
        prompt_template = PROMPTS["summarize_entity_descriptions"]
        use_description = decode(tokens[:llm_max_tokens])
        descriptions = use_description.split(GRAPH_FIELD_SEP)
        context_base = {'entity_name': entity_or_relation_name, 'description_list': descriptions}
        use_prompt = prompt_template.format(**context_base)
        logger.debug(f"Trigger summary: {entity_or_relation_name}")
        # summary = await ollama_chat(use_prompt, max_tokens=summary_max_tokens)
        summary = await ollama_chat(use_prompt, core_input=" ".join(descriptions))
        return summary

    async def query(self, query: str, param: QueryParam = QueryParam()):
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
        context = None
        if param.mode == "local":
            response, context = await self.local_query(query, param)
        elif param.mode == "global":
            response = await self.global_query(query, param)

        elif param.mode == "hybrid":
            response = await self.hybrid_query(query, param)
        elif param.mode == "naive":
            response = await self.naive_query(query, param)
        else:
            raise ValueError(f"Unknown mode {param.mode}")
        return response, context

    async def local_query(self, query: str, query_param: QueryParam) -> tuple[str, str]:
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

        keywords_prompt = PROMPTS["keywords_extraction"].format(query=query)

        result = await ollama_chat(keywords_prompt, core_input=query, category=CATEGORY_KEYWORD_EXTRACTION)

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
        if query_param.only_need_context:
            return None, context
        if context is None:
            return PROMPTS["fail_response"]
        sys_prompt_temp = PROMPTS["rag_response"]
        sys_prompt = sys_prompt_temp.format(context_data=context, response_type=query_param.response_type)
        response = await ollama_chat(query, system_prompt=sys_prompt)
        if len(response) > len(sys_prompt):
            response = (response.replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())

        return response, context

    async def get_local_query_context(self, query, query_param: QueryParam) -> str | None:
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
        use_texts = await self.get_graph_rag_texts(primary_nodes)
        # the relations with endpoint names in descending order of importance
        use_relations = await self.get_graph_rag_relations(primary_nodes, query_param)

        # ====================== Primary Nodes ==================================
        entites_section_list = [["id", "entity", "type", "description", "order"]]
        for i, n in enumerate(primary_nodes):
            entites_section_list.append([i, n.name, n.type, n.description, n.degree])
        entities_context = list_of_list_to_csv(entites_section_list)

        # ====================== Relations ======================================
        relations_section_list = [["id", "source", "target", "description", "keywords", "weight", "order"]]
        for i, e in enumerate(use_relations):
            relations_section_list.append([i, e.source, e.target, e.description, e.keywords, e.weight, e.order])
        relations_context = list_of_list_to_csv(relations_section_list)
        # ====================== Chunks ========================================
        text_units_section_list = [["id", "content"]]
        for i, t in enumerate(use_texts):
            text_units_section_list.append([i, t.text])
        text_units_context = list_of_list_to_csv(text_units_section_list)
        context = f"""
            -----Entities-----
            ```csv
            {entities_context}
            ```
            -----Relationships-----
            ```csv
            {relations_context}
            ```
            -----Sources-----
            ```csv
            {text_units_context}
            ```
            """
        return context

    async def get_primary_nodes(self, query: str, query_param: QueryParam) -> List[KnwlDegreeNode] | None:
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
        found = await self.node_vectors.query(query, top_k=query_param.top_k)
        if not len(found):
            return None
        # todo: translation from vector to node not necessary if the vector storage contains the data as well
        node_datas = await asyncio.gather(*[self.graph_storage.get_node_by_id(r["id"]) for r in found])

        # if the node vector exists but the node isn't in the graph, it's likely that the storage is damaged or not in sync
        if not all([n is not None for n in node_datas]):
            logger.warning("Some nodes are missing, maybe the storage is damaged")
        # degree might also come in one go
        node_degrees = await asyncio.gather(*[self.graph_storage.node_degree(r["name"]) for r in found])
        nodes = [KnwlDegreeNode(degree=d, **asdict(n)) for k, n, d in zip(found, node_datas, node_degrees) if n is not None]
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
    def get_chunk_ids(nodes: List[KnwlNode]) -> List[str]:
        if nodes is None:
            raise ValueError("get_chunk_ids: parameter is None")
        if not len(nodes):
            return []
        lists = [n.chunkIds for n in nodes]
        # flatten the list and remove duplicates
        return list(set([item for sublist in lists for item in sublist]))

    async def create_chunk_stats(self, primary_nodes: List[KnwlNode]) -> dict[str, int]:
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
        primary_chunk_ids = Simple.get_chunk_ids(primary_nodes)
        all_edges = await self.get_attached_edges(primary_nodes)
        node_map = {n.id: n for n in primary_nodes}
        edge_chunk_ids = {}
        stats = {}
        for edge in all_edges:
            if edge.sourceId not in node_map:
                node_map[edge.sourceId] = await self.graph_storage.get_node_by_id(edge.sourceId)
            if edge.targetId not in node_map:
                node_map[edge.targetId] = await self.graph_storage.get_node_by_id(edge.targetId)
            # take the chunkId in both nodes
            source_chunks = node_map[edge.sourceId].chunkIds
            target_chunks = node_map[edge.targetId].chunkIds
            common_chunk_ids = list(set(source_chunks).intersection(target_chunks))
            edge_chunk_ids[edge.id] = common_chunk_ids
        for chunk_id in primary_chunk_ids:
            # count how many times this chunk appears in the edge_chunk_ids
            stats[chunk_id] = sum([chunk_id in v for v in edge_chunk_ids.values()])
        return stats

    async def get_graph_rag_texts(self, primary_nodes: list[KnwlNode]) -> List[KnwlRagText]:
        """
        Returns the most relevant paragraphs based on the given primary nodes.
        What makes the paragraphs relevant is defined in the `create_chunk_stats` method.

        This method first creates chunk statistics for the provided primary nodes, then retrieves the corresponding text
        for each chunk from the chunk storage. The chunks are then sorted in decreasing order of their count.

        Args:
            primary_nodes (list[KnwlNode]): A list of primary nodes for which to retrieve the graph RAG texts.

        Returns:
            list[dict]: A list of dictionaries, each containing 'count' and 'text' keys, sorted in decreasing order of count.
        """
        stats = await self.create_chunk_stats(primary_nodes)
        graph_rag_chunks = {}
        for chunk_id, count in stats.items():
            chunk = await self.chunks_storage.get_by_id(chunk_id)
            graph_rag_chunks[chunk_id] = KnwlRagText(order=count, text=chunk["content"])
        # in decreasing order of count
        graph_rag_texts = sorted(graph_rag_chunks.values(), key=lambda x: x.order, reverse=True)
        return graph_rag_texts

    async def get_graph_rag_relations(self, node_datas: list[KnwlDegreeNode], query_param: QueryParam) -> List[KnwlRagRelation]:
        all_attached_edges = await self.graph_storage.get_attached_edges(node_datas)
        all_edges_degree = await self.graph_storage.get_edge_degrees(all_attached_edges)
        all_edge_ids = unique_strings([e.id for e in all_attached_edges])
        edge_endpoint_names = await self.graph_storage.get_semantic_endpoints(all_edge_ids)
        all_edges_data = [
            KnwlRagRelation(order=d, source=edge_endpoint_names[e.id][0], target=edge_endpoint_names[e.id][1], keywords=e.keywords, description=e.description, weight=e.weight, id=e.id)
            for e, d in zip(all_attached_edges, all_edges_degree) if e is not None
        ]
        # sort by edge degree and weight descending
        all_edges_data = sorted(all_edges_data, key=lambda x: (x.order, x.weight), reverse=True)
        all_edges_data = truncate_list_by_token_size(all_edges_data, key=lambda x: x.description, max_token_size=query_param.max_token_for_global_context)
        return all_edges_data

    async def global_query(self, query, query_param: QueryParam) -> str:
        context = None

        kw_prompt_temp = PROMPTS["keywords_extraction"]
        kw_prompt = kw_prompt_temp.format(query=query)
        result = await ollama_chat(kw_prompt)

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

        if query_param.only_need_context:
            return context
        if context is None:
            return PROMPTS["fail_response"]

        sys_prompt_temp = PROMPTS["rag_response"]
        sys_prompt = sys_prompt_temp.format(context_data=context, response_type=query_param.response_type)
        response = await ollama_chat(query, system_prompt=sys_prompt, )
        if len(response) > len(sys_prompt):
            response = (response.replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())

        return response

    async def get_global_query_context(self, keywords, query_param: QueryParam):
        results = await self.edge_vectors.query(keywords, top_k=query_param.top_k)

        if not len(results):
            return None

        edge_datas = await asyncio.gather(*[self.graph_storage.get_edge(r["src_id"], r["tgt_id"]) for r in results])

        if not all([n is not None for n in edge_datas]):
            logger.warning("Some edges are missing, maybe the storage is damaged")
        edge_degree = await asyncio.gather(*[self.graph_storage.edge_degree(r["src_id"], r["tgt_id"]) for r in results])
        edge_datas = [{"src_id": k["src_id"], "tgt_id": k["tgt_id"], "rank": d, **v} for k, v, d in zip(results, edge_datas, edge_degree) if v is not None]
        edge_datas = sorted(edge_datas, key=lambda x: (x["rank"], x.weight), reverse=True)
        edge_datas = truncate_list_by_token_size(edge_datas, key=lambda x: x.description, max_token_size=query_param.max_token_for_global_context, )

        use_entities = await self._find_most_related_entities_from_relationships(edge_datas, query_param)
        use_text_units = await self._find_related_text_unit_from_relationships(edge_datas, query_param)
        logger.info(f"Global query uses {len(use_entities)} entites, {len(edge_datas)} relations, {len(use_text_units)} text units")
        relations_section_list = [["id", "source", "target", "description", "keywords", "weight", "rank"]]
        for i, e in enumerate(edge_datas):
            relations_section_list.append([i, e["src_id"], e["tgt_id"], e.description, e.keywords, e.weight, e["rank"], ])
        relations_context = list_of_list_to_csv(relations_section_list)

        entites_section_list = [["id", "entity", "type", "description", "rank"]]
        for i, n in enumerate(use_entities):
            entites_section_list.append([i, n["entity_name"], n.get("entity_type", "UNKNOWN"), n.get("description", "UNKNOWN"), n["rank"], ])
        entities_context = list_of_list_to_csv(entites_section_list)

        text_units_section_list = [["id", "content"]]
        for i, t in enumerate(use_text_units):
            text_units_section_list.append([i, t.content])
        text_units_context = list_of_list_to_csv(text_units_section_list)

        return f"""
    -----Entities-----
    ```csv
    {entities_context}
    ```
    -----Relationships-----
    ```csv
    {relations_context}
    ```
    -----Sources-----
    ```csv
    {text_units_context}
    ```
    """

    async def _find_most_related_entities_from_relationships(self, edge_datas: list[dict], query_param: QueryParam):
        entity_names = set()
        for e in edge_datas:
            entity_names.add(e["src_id"])
            entity_names.add(e["tgt_id"])

        node_datas = await asyncio.gather(*[self.graph_storage.get_node_by_id(entity_name) for entity_name in entity_names])

        node_degrees = await asyncio.gather(*[self.graph_storage.node_degree(entity_name) for entity_name in entity_names])
        node_datas = [{**n, "entity_name": k, "rank": d} for k, n, d in zip(entity_names, node_datas, node_degrees)]

        node_datas = truncate_list_by_token_size(node_datas, key=lambda x: x.description, max_token_size=query_param.max_token_for_local_context, )

        return node_datas

    async def _find_related_text_unit_from_relationships(self, edge_datas: list[dict], query_param: QueryParam, ):
        text_units = [split_string_by_multi_markers(dp["source_id"], [GRAPH_FIELD_SEP]) for dp in edge_datas]

        all_text_units_lookup = {}

        for index, unit_list in enumerate(text_units):
            for c_id in unit_list:
                if c_id not in all_text_units_lookup:
                    all_text_units_lookup[c_id] = {"data": await self.chunks_storage.get_by_id(c_id), "order": index, }

        if any([v is None for v in all_text_units_lookup.values()]):
            logger.warning("Text chunks are missing, maybe the storage is damaged")
        all_text_units = [{"id": k, **v} for k, v in all_text_units_lookup.items() if v is not None]
        all_text_units = sorted(all_text_units, key=lambda x: x["order"])
        all_text_units = truncate_list_by_token_size(all_text_units, key=lambda x: x["data"]["content"], max_token_size=query_param.max_token_for_text_unit, )
        all_text_units: list[KnwlChunk] = [t["data"] for t in all_text_units]

        return all_text_units

    async def naive_query(self, query, query_param: QueryParam):
        """
        Perform a naive query on the chunk vectors and generate a response.
        This is classic RAG without using the knowledge graph.

        Args:
            query (str): The query string to be processed.
            query_param (QueryParam): An instance of QueryParam containing parameters for the query.

        Returns:
            str: The generated response based on the query and parameters. If no results are found, returns a fail response prompt.
        """

        results = await self.chunk_vectors.query(query, top_k=query_param.top_k)
        if not len(results):
            return PROMPTS["fail_response"]
        chunks = results
        maybe_trun_chunks = truncate_list_by_token_size(chunks, key=lambda x: x["content"], max_token_size=query_param.max_token_for_text_unit, )
        logger.info(f"Truncate {len(chunks)} to {len(maybe_trun_chunks)} chunks")
        section = "--New Chunk--\n".join([c["content"] for c in maybe_trun_chunks])
        if query_param.only_need_context:
            return section
        sys_prompt_temp = PROMPTS["naive_rag_response"]
        sys_prompt = sys_prompt_temp.format(content_data=section, response_type=query_param.response_type)
        response = await ollama_chat(query, system_prompt=sys_prompt, category=CATEGORY_NAIVE_QUERY)

        if len(response) > len(sys_prompt):
            response = (response[len(sys_prompt):].replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())

        return response

    async def hybrid_query(self, query, query_param: QueryParam) -> str:
        low_level_context = None
        high_level_context = None

        kw_prompt_temp = PROMPTS["keywords_extraction"]
        kw_prompt = kw_prompt_temp.format(query=query)

        result = await ollama_chat(kw_prompt)
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

        context = self.combine_contexts(high_level_context, low_level_context)

        if query_param.only_need_context:
            return context
        if context is None:
            return PROMPTS["fail_response"]

        sys_prompt_temp = PROMPTS["rag_response"]
        sys_prompt = sys_prompt_temp.format(context_data=context, response_type=query_param.response_type)
        response = await ollama_chat(query, system_prompt=sys_prompt, )
        if len(response) > len(sys_prompt):
            response = (response.replace(sys_prompt, "").replace("user", "").replace("model", "").replace(query, "").replace("<system>", "").replace("</system>", "").strip())
        return response

    def combine_contexts(self, high_level_context, low_level_context):
        # Function to extract entities, relationships, and sources from context strings

        def extract_sections(context):
            entities_match = re.search(r"-----Entities-----\s*```csv\s*(.*?)\s*```", context, re.DOTALL)
            relationships_match = re.search(r"-----Relationships-----\s*```csv\s*(.*?)\s*```", context, re.DOTALL)
            sources_match = re.search(r"-----Sources-----\s*```csv\s*(.*?)\s*```", context, re.DOTALL)

            entities = entities_match.group(1) if entities_match else ""
            relationships = relationships_match.group(1) if relationships_match else ""
            sources = sources_match.group(1) if sources_match else ""

            return entities, relationships, sources

        # Extract sections from both contexts

        if high_level_context is None:
            warnings.warn("High Level context is None. Return empty High entity/relationship/source")
            hl_entities, hl_relationships, hl_sources = "", "", ""
        else:
            hl_entities, hl_relationships, hl_sources = extract_sections(high_level_context)

        if low_level_context is None:
            warnings.warn("Low Level context is None. Return empty Low entity/relationship/source")
            ll_entities, ll_relationships, ll_sources = "", "", ""
        else:
            ll_entities, ll_relationships, ll_sources = extract_sections(low_level_context)

        # Combine and deduplicate the entities
        combined_entities_set = set(filter(None, hl_entities.strip().split("\n") + ll_entities.strip().split("\n")))
        combined_entities = "\n".join(combined_entities_set)

        # Combine and deduplicate the relationships
        combined_relationships_set = set(filter(None, hl_relationships.strip().split("\n") + ll_relationships.strip().split("\n"), ))
        combined_relationships = "\n".join(combined_relationships_set)

        # Combine and deduplicate the sources
        combined_sources_set = set(filter(None, hl_sources.strip().split("\n") + ll_sources.strip().split("\n")))
        combined_sources = "\n".join(combined_sources_set)

        # Format the combined context
        return f"""
    -----Entities-----
    ```csv
    {combined_entities}
    -----Relationships-----
    {combined_relationships}
    -----Sources-----
    {combined_sources}
    """

    async def count_documents(self):
        return await self.document_storage.count()
