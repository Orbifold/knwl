from dataclasses import dataclass


@dataclass(frozen=True)
class KnwlRagChunk:
    index: str
    text: str
    order: int
    id: str

    @staticmethod
    def get_header():
        return ["id", "content"]

    def to_row(self):
        return "\t".join(
            [self.index, self.text]
        )