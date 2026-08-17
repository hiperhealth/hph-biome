from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from hphbiome.collection import KnowledgeCollection
from hphbiome.knowledge import CuratedKnowledgeRecord
from hphbiome.reference import ScientificReference

KNOWLEDGE_COLLECTION_SCHEMA_VERSION = 1


def _required_value(value: Mapping[str, object], field_name: str) -> object:
    try:
        return value[field_name]
    except KeyError:
        raise ValueError(f'missing required field {field_name!r}') from None


def _ordered_sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
        value, Sequence
    ):
        raise TypeError(f'{field_name} must be an ordered sequence')
    return value


def _reference_from_mapping(value: object, index: int) -> ScientificReference:
    location = f'references[{index}]'
    if not isinstance(value, Mapping):
        raise TypeError(f'{location} must be a mapping')

    try:
        return ScientificReference(
            title=cast(str, _required_value(value, 'title')),
            authors=cast(Sequence[str], _required_value(value, 'authors')),
            source=cast(str, _required_value(value, 'source')),
            identifier=cast(str | None, value.get('identifier')),
            canonical_url=cast(str | None, value.get('canonical_url')),
        )
    except TypeError as error:
        raise TypeError(f'{location}: {error}') from error
    except ValueError as error:
        raise ValueError(f'{location}: {error}') from error


def _record_from_mapping(value: object, index: int) -> CuratedKnowledgeRecord:
    location = f'records[{index}]'
    if not isinstance(value, Mapping):
        raise TypeError(f'{location} must be a mapping')

    try:
        return CuratedKnowledgeRecord(
            id=cast(str, _required_value(value, 'id')),
            title=cast(str, _required_value(value, 'title')),
            synthesis=cast(str, _required_value(value, 'synthesis')),
            references=cast(
                Sequence[str], _required_value(value, 'references')
            ),
            review_status=cast(str, _required_value(value, 'review_status')),
        )
    except TypeError as error:
        raise TypeError(f'{location}: {error}') from error
    except ValueError as error:
        raise ValueError(f'{location}: {error}') from error


def knowledge_collection_to_dict(
    collection: KnowledgeCollection,
) -> dict[str, object]:
    """Convert a knowledge collection to the current versioned mapping."""
    if not isinstance(collection, KnowledgeCollection):
        raise TypeError('collection must be a KnowledgeCollection')

    return {
        'schema_version': KNOWLEDGE_COLLECTION_SCHEMA_VERSION,
        'references': [
            reference.to_dict() for reference in collection.references
        ],
        'records': [record.to_dict() for record in collection.records],
    }


def knowledge_collection_from_dict(
    value: Mapping[str, object],
) -> KnowledgeCollection:
    """Reconstruct a validated knowledge collection from a mapping."""
    if not isinstance(value, Mapping):
        raise TypeError('value must be a mapping')

    try:
        schema_version = _required_value(value, 'schema_version')
        reference_values = _required_value(value, 'references')
        record_values = _required_value(value, 'records')
    except ValueError as error:
        raise ValueError(f'collection: {error}') from error

    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise TypeError('schema_version must be an integer')
    if schema_version != KNOWLEDGE_COLLECTION_SCHEMA_VERSION:
        raise ValueError(f'unsupported schema_version: {schema_version!r}')

    references = tuple(
        _reference_from_mapping(reference, index)
        for index, reference in enumerate(
            _ordered_sequence(reference_values, 'references')
        )
    )
    records = tuple(
        _record_from_mapping(record, index)
        for index, record in enumerate(
            _ordered_sequence(record_values, 'records')
        )
    )
    return KnowledgeCollection(records=records, references=references)
