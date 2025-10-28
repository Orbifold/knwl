from knwl.models import KnwlInput
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlGragInput import KnwlGragInput
from knwl.models.KnwlGragReference import KnwlGragReference

from pydantic import BaseModel, Field
from typing import List

from knwl.models.KnwlGragText import KnwlGragText
from knwl.models.KnwlNode import KnwlNode


class KnwlGragContext(BaseModel):
    """
    Represents the augmented context based on the knowledge graph for a given input.
    """

    input: str | KnwlGragInput = Field(
        description="The original input text or KnwlInput object."
    )
    texts: List[KnwlGragText] = Field(default_factory=list)
    nodes: List[KnwlNode] = Field(default_factory=list)
    edges: List[KnwlEdge] = Field(default_factory=list)
    references: List[KnwlGragReference] = Field(default_factory=list)

    def get_chunk_table(self):
        return "\n".join(
            ["\t".join(KnwlGragText.get_header())]
            + [chunk.to_row() for chunk in self.chunks]
        )

    def get_nodes_table(self):
        return "\n".join(
            ["\t".join(KnwlNode.get_header())]
            + [node.to_row() for node in self.nodes]
        )

    def get_edges_table(self):
        return "\n".join(
            ["\t".join(KnwlEdge.get_header())]
            + [edge.to_row() for edge in self.edges]
        )

    def get_references_table(self):
        return "\n".join(
            ["\t".join(["id", "name", "description", "timestamp"])]
            + [
                "\t".join(
                    [
                        reference.index,
                        reference.name or "Not set",
                        reference.description or "Not provided",
                        reference.timestamp,
                    ]
                )
                for reference in self.references
            ]
        )

    def get_documents(self):
        return "\n--Document--\n" + "\n--Document--\n".join(
            [c.text for c in self.chunks]
        )

    @staticmethod
    def combine(first: "KnwlGragContext", second: "KnwlGragContext") -> "KnwlGragContext":
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

        return KnwlGragContext(
            chunks=chunks, nodes=nodes, edges=edges, references=references
        )

    def __str__(self):
        nodes = (
            f"""
-----Entities-----
```csv
{self.get_nodes_table()}
```
            """
            if len(self.nodes) > 0
            else ""
        )
        edges = (
            f"""
-----Relationships-----
```csv
{self.get_edges_table()}
```
            """
            if len(self.edges) > 0
            else ""
        )
        chunks = (
            f"""
-----Sources-----
```csv
{self.get_chunk_table()}
```
            """
            if len(self.chunks) > 0
            else ""
        )

        return f"""{nodes}{edges}{chunks}"""
