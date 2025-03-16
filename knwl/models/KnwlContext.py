from knwl.models.KnwlRagEdge import KnwlRagEdge
from knwl.models.KnwlRagReference import KnwlRagReference
from knwl.models.KnwlRagNode import KnwlRagNode
from knwl.models.KnwlRagChunk import KnwlRagChunk


from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnwlContext:
    chunks: List[KnwlRagChunk] = field(default_factory=list)
    nodes: List[KnwlRagNode] = field(default_factory=list)
    edges: List[KnwlRagEdge] = field(default_factory=list)
    references: List[KnwlRagReference] = field(default_factory=list)

    def get_chunk_table(self):
        return "\n".join(["\t".join(KnwlRagChunk.get_header())] + [chunk.to_row() for chunk in self.chunks])

    def get_nodes_table(self):
        return "\n".join(["\t".join(KnwlRagNode.get_header())] + [node.to_row() for node in self.nodes])

    def get_edges_table(self):
        return "\n".join(["\t".join(KnwlRagEdge.get_header())] + [edge.to_row() for edge in self.edges])

    def get_references_table(self):
        return "\n".join(["\t".join(["id", "name", "description", "timestamp"])] + [
            "\t".join([reference.index, reference.name or "Not set", reference.description or "Not provided", reference.timestamp]) for reference in
            self.references])

    def get_documents(self):
        return "\n--Document--\n" + "\n--Document--\n".join([c.text for c in self.chunks])

    @staticmethod
    def combine(first: 'KnwlContext', second: 'KnwlContext') -> 'KnwlContext':
        chunks = [c for c in first.chunks]
        nodes = [n for n in first.nodes]
        edges = [e for e in first.edges]
        references = [r for r in first.references]
        # ================= Chunks ===========================================
        chunk_ids = [cc.id for cc in chunks]
        for c in second.chunks:
            if c.id not in chunk_ids:
                chunks.append(c)
        # ================= Nodes  ===========================================
        node_ids = [cc.id for cc in nodes]
        for n in second.nodes:
            if n.id not in node_ids:
                nodes.append(n)
        # ================= Edges  ===========================================
        edge_ids = [cc.id for cc in edges]
        for e in second.edges:
            if e.id not in edge_ids:
                edges.append(e)

        # ================= References  ======================================
        reference_ids = [cc.id for cc in references]
        for r in second.references:
            if r.id not in reference_ids:
                references.append(r)

        return KnwlContext(chunks=chunks, nodes=nodes, edges=edges, references=references)

    def __str__(self):
        nodes = f"""
-----Entities-----
```csv
{self.get_nodes_table()}
```
            """ if len(self.nodes) > 0 else ""
        edges = f"""
-----Relationships-----
```csv
{self.get_edges_table()}
```
            """ if len(self.edges) > 0 else ""
        chunks = f"""
-----Sources-----
```csv
{self.get_chunk_table()}
```
            """ if len(self.chunks) > 0 else ""

        return f"""{nodes}{edges}{chunks}"""