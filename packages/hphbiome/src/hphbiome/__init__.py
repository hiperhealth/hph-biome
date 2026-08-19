from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from hphbiome.collection import KnowledgeCollection
from hphbiome.core import (
    FIELD_LABELS,
    RECOMMENDED_BIOME_FIELDS,
    build_biome_context,
    build_prompt_fragment,
    field_description,
    field_label,
    has_value,
    missing_recommended_fields,
)
from hphbiome.knowledge import CuratedKnowledgeRecord
from hphbiome.reference import ScientificReference
from hphbiome.retrieval import RetrievedKnowledge, retrieve_knowledge
from hphbiome.serialization import (
    KNOWLEDGE_COLLECTION_SCHEMA_VERSION,
    knowledge_collection_from_dict,
    knowledge_collection_to_dict,
)


def _version() -> str:
    try:
        return version('hphbiome')
    except PackageNotFoundError:
        return '0.1.0'


__version__ = _version()

__all__ = [
    'FIELD_LABELS',
    'KNOWLEDGE_COLLECTION_SCHEMA_VERSION',
    'RECOMMENDED_BIOME_FIELDS',
    'CuratedKnowledgeRecord',
    'KnowledgeCollection',
    'RetrievedKnowledge',
    'ScientificReference',
    '__version__',
    'build_biome_context',
    'build_prompt_fragment',
    'field_description',
    'field_label',
    'has_value',
    'knowledge_collection_from_dict',
    'knowledge_collection_to_dict',
    'missing_recommended_fields',
    'retrieve_knowledge',
]
