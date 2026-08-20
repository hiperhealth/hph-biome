from __future__ import annotations

from collections.abc import Sequence

from hphbiome.reference import ScientificReference
from hphbiome.retrieval import RetrievedKnowledge


def _normalize_results(value: object) -> tuple[RetrievedKnowledge, ...]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, Sequence
    ):
        raise TypeError(
            'results must be an ordered sequence of RetrievedKnowledge'
        )

    results: list[RetrievedKnowledge] = []
    for index, result in enumerate(value):
        if not isinstance(result, RetrievedKnowledge):
            raise TypeError(f'results[{index}] must be a RetrievedKnowledge')
        results.append(result)
    return tuple(results)


def _reference_context(reference: ScientificReference) -> dict[str, object]:
    return {
        'identifier': reference.identifier,
        'canonical_url': reference.canonical_url,
    }


def _result_context(result: RetrievedKnowledge) -> dict[str, object]:
    return {
        'record_id': result.record.id,
        'title': result.record.title,
        'synthesis': result.record.synthesis,
        'review_status': result.record.review_status,
        'score': result.score,
        'references': [
            _reference_context(reference) for reference in result.references
        ],
    }


def build_structured_knowledge_context(
    results: Sequence[RetrievedKnowledge],
) -> dict[str, object]:
    """Return ordered structured context, or ``{'results': []}`` if empty."""
    normalized_results = _normalize_results(results)
    return {
        'results': [_result_context(result) for result in normalized_results]
    }


def _optional_text(value: str | None) -> str:
    return value if value is not None else 'Not provided'


def _result_text(result: RetrievedKnowledge, position: int) -> str:
    lines = [
        f'Result {position}',
        f'Record ID: {result.record.id}',
        f'Title: {result.record.title}',
        f'Review status: {result.record.review_status}',
        f'Relevance score: {result.score}',
        'Synthesis:',
        result.record.synthesis,
        'References:',
    ]

    if not result.references:
        lines.append('None')
    else:
        for reference_position, reference in enumerate(
            result.references, start=1
        ):
            lines.extend(
                [
                    f'{reference_position}. Identifier: '
                    f'{_optional_text(reference.identifier)}',
                    '   Canonical URL: '
                    f'{_optional_text(reference.canonical_url)}',
                ]
            )
    return '\n'.join(lines)


def build_text_knowledge_context(
    results: Sequence[RetrievedKnowledge],
) -> str:
    """Return ordered plain-text context, or an empty string if empty."""
    normalized_results = _normalize_results(results)
    return '\n\n'.join(
        _result_text(result, position)
        for position, result in enumerate(normalized_results, start=1)
    )
