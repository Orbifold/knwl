from knwl.models import KnwlInput
from knwl.models.KnwlEdge import KnwlEdge
from knwl.models.KnwlReference import KnwlReference

from pydantic import BaseModel, Field
from typing import List

from knwl.models.KnwlText import KnwlText
from knwl.models.KnwlNode import KnwlNode


class KnwlContext(BaseModel):
    """
    Represents the augmented context based on the knowledge graph for a given input.
    """

    input: str | KnwlInput = Field(
        description="The original input text or KnwlInput object."
    )
    texts: list[KnwlText] = Field(default_factory=list)
    nodes: list[KnwlNode] = Field(default_factory=list)
    edges: list[KnwlEdge] = Field(default_factory=list)
    references: list[KnwlReference] = Field(default_factory=list)

    @staticmethod
    def combine(
        first: "KnwlContext", second: "KnwlContext"
    ) -> "KnwlContext":
        texts = [c for c in first.texts]
        nodes = [n for n in first.nodes]
        edges = [e for e in first.edges]
        references = [r for r in first.references]
        # ================= Texts ===========================================
        chunk_ids = [cc.id for cc in texts]
        for c in second.texts:
            if c.id not in chunk_ids:
                texts.append(c)
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

        return KnwlContext(
            input=first.input,
            texts=texts,
            nodes=nodes,
            edges=edges,
            references=references,
        )

    @staticmethod
    def empty(input: KnwlInput) -> "KnwlContext":
        return KnwlContext(
            input=input,
            texts=[],
            nodes=[],
            edges=[],
            references=[],
        )

    def __repr__(self):
        return f"<KnwlContext, texts={len(self.texts)}, nodes={len(self.nodes)}, edges={len(self.edges)}, references={len(self.references)}>"
    def __str__(self):
        return self.__repr__()