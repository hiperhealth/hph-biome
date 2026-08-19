from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

from hphbiome.knowledge import CuratedKnowledgeRecord
from hphbiome.reference import ScientificReference


def _normalize_references(value: object) -> tuple[ScientificReference, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, Sequence
    ):
        raise TypeError(
            'references must be an ordered sequence of ScientificReference'
        )

    references: list[ScientificReference] = []
    for index, reference in enumerate(value):
        if not isinstance(reference, ScientificReference):
            raise TypeError(
                f'references[{index}] must be a ScientificReference'
            )
        references.append(reference)
    return tuple(references)


@dataclass(frozen=True)
class RetrievedKnowledge:
    """One retrieved curated record with relevance and source provenance."""

    record: CuratedKnowledgeRecord
    score: float
    references: Sequence[ScientificReference]

    def __post_init__(self) -> None:
        if not isinstance(self.record, CuratedKnowledgeRecord):
            raise TypeError('record must be a CuratedKnowledgeRecord')
        if isinstance(self.score, bool) or not isinstance(
            self.score, (int, float)
        ):
            raise TypeError('score must be a real number')

        score = float(self.score)
        if not isfinite(score):
            raise ValueError('score must be finite')

        references = _normalize_references(self.references)
        object.__setattr__(self, 'score', score)
        object.__setattr__(self, 'references', references)

    def to_dict(self) -> dict[str, object]:
        """Serialize the result using a stable field order."""
        return {
            'record': self.record.to_dict(),
            'score': self.score,
            'references': [
                reference.to_dict() for reference in self.references
            ],
        }
