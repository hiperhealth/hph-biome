from __future__ import annotations

import re

from collections.abc import Sequence, Set
from dataclasses import dataclass
from math import isfinite

from hphbiome.collection import KnowledgeCollection
from hphbiome.knowledge import CuratedKnowledgeRecord
from hphbiome.reference import ScientificReference

_WORD_PATTERN = re.compile(r'\w+')


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


def _word_tokens(text: str) -> tuple[str, ...]:
    return tuple(_WORD_PATTERN.findall(text.casefold()))


def _normalize_allowed_review_statuses(
    value: object,
) -> frozenset[str] | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, (Sequence, Set)
    ):
        raise TypeError(
            'allowed_review_statuses must be a sequence or set of strings'
        )

    statuses: set[str] = set()
    for status in value:
        if not isinstance(status, str):
            raise TypeError(
                'allowed_review_statuses must contain only strings'
            )
        if not status.strip():
            raise ValueError(
                'allowed_review_statuses must not contain blank values'
            )
        statuses.add(status)
    return frozenset(statuses)


def _validate_limit(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError('limit must be an integer')
    if value <= 0:
        raise ValueError('limit must be greater than zero')
    return value


def retrieve_knowledge(
    collection: KnowledgeCollection,
    query: str,
    *,
    allowed_review_statuses: Sequence[str] | Set[str] | None = None,
    limit: int | None = None,
) -> tuple[RetrievedKnowledge, ...]:
    """Return deterministic lexical matches from titles and syntheses.

    The score is the fraction of distinct query word tokens present in a
    record's title or synthesis. Higher scores rank first, and ties preserve
    the record order from ``collection``. By default, all review statuses and
    all matches are returned. Caller-provided statuses are matched exactly;
    an empty allowlist returns no results. A limit is applied after status
    filtering and deterministic ranking.
    """
    if not isinstance(collection, KnowledgeCollection):
        raise TypeError('collection must be a KnowledgeCollection')
    if not isinstance(query, str):
        raise TypeError('query must be a string')
    if not query.strip():
        raise ValueError('query must not be blank')

    allowed_statuses = _normalize_allowed_review_statuses(
        allowed_review_statuses
    )
    result_limit = _validate_limit(limit)

    query_tokens = tuple(dict.fromkeys(_word_tokens(query)))
    if not query_tokens:
        return ()

    ranked_results: list[tuple[int, RetrievedKnowledge]] = []
    for index, record in enumerate(collection.records):
        if (
            allowed_statuses is not None
            and record.review_status not in allowed_statuses
        ):
            continue

        record_tokens = set(_word_tokens(record.title))
        record_tokens.update(_word_tokens(record.synthesis))
        match_count = sum(token in record_tokens for token in query_tokens)
        if not match_count:
            continue

        result = RetrievedKnowledge(
            record=record,
            score=match_count / len(query_tokens),
            references=collection.resolve_references(record.id),
        )
        ranked_results.append((index, result))

    ranked_results.sort(key=lambda item: (-item[1].score, item[0]))
    results = tuple(result for _, result in ranked_results)
    return results if result_limit is None else results[:result_limit]
