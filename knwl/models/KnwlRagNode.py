from dataclasses import dataclass


@dataclass(frozen=True)
class KnwlRagNode:
    id: str
    index: str
    name: str
    type: str
    description: str
    order: int

    @staticmethod
    def get_header():
        return ["id", "name", "type", "description", ]

    def to_row(self):
        return "\t".join(
            [self.index, self.name, self.type, self.description]
        )