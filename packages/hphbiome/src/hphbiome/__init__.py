from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

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


def _version() -> str:
    try:
        return version('hphbiome')
    except PackageNotFoundError:
        return '0.1.0'


__version__ = _version()

__all__ = [
    'FIELD_LABELS',
    'RECOMMENDED_BIOME_FIELDS',
    '__version__',
    'build_biome_context',
    'build_prompt_fragment',
    'field_description',
    'field_label',
    'has_value',
    'missing_recommended_fields',
]
