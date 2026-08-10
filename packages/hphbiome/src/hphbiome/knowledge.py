from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


def _validate_non_blank_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f'{field_name} must be a string')
    if not value.strip():
        raise ValueError(f'{field_name} must not be blank')


@dataclass(frozen=True)
class CuratedKnowledgeRecord:
    """A human-reviewed curated-knowledge record."""

    id: str
    title: str
    synthesis: str
    references: Sequence[str]
    review_status: str

    def __post_init__(self) -> None:
        _validate_non_blank_string('id', self.id)
        _validate_non_blank_string('title', self.title)
        _validate_non_blank_string('synthesis', self.synthesis)
        _validate_non_blank_string('review_status', self.review_status)

        if isinstance(
            self.references, (str, bytes, bytearray)
        ) or not isinstance(self.references, Sequence):
            raise TypeError(
                'references must be an ordered sequence of strings'
            )

        for index, reference in enumerate(self.references):
            _validate_non_blank_string(f'references[{index}]', reference)

        object.__setattr__(self, 'references', tuple(self.references))

    def to_dict(self) -> dict[str, object]:
        """Serialize the record using a stable field order."""
        return {
            'id': self.id,
            'title': self.title,
            'synthesis': self.synthesis,
            'references': list(self.references),
            'review_status': self.review_status,
        }
