from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RECOMMENDED_BIOME_FIELDS: tuple[str, ...] = (
    'symptoms',
    'dietary_history',
    'stool_pattern',
    'recent_antibiotics',
    'medications',
    'allergies',
)

FIELD_LABELS: dict[str, str] = {
    'symptoms': 'Current gastrointestinal or systemic symptoms',
    'dietary_history': 'Recent dietary pattern and fiber intake',
    'stool_pattern': 'Bowel movement frequency and stool pattern',
    'recent_antibiotics': 'Recent antibiotic or antimicrobial exposure',
    'medications': 'Current medications and supplements',
    'allergies': 'Known allergies or intolerances',
}

_FIELD_DESCRIPTIONS: dict[str, str] = {
    'symptoms': (
        'Include duration, severity, associated symptoms, and triggers.'
    ),
    'dietary_history': (
        'Include typical meals, fiber intake, alcohol, and fluids.'
    ),
    'stool_pattern': (
        'Include frequency, consistency, urgency, blood, or mucus.'
    ),
    'recent_antibiotics': 'Include agent, indication, dates, and response.',
    'medications': 'Include prescription, over-the-counter, and supplements.',
    'allergies': 'Include reactions and relevant food intolerances.',
}


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (Mapping, list, tuple, set)):
        return bool(value)
    return True


def missing_recommended_fields(
    patient: Mapping[str, Any],
) -> tuple[str, ...]:
    return tuple(
        field
        for field in RECOMMENDED_BIOME_FIELDS
        if not has_value(patient.get(field))
    )


def field_label(field: str) -> str:
    return FIELD_LABELS.get(field, field.replace('_', ' ').title())


def field_description(field: str) -> str:
    return _FIELD_DESCRIPTIONS.get(field, '')


def build_biome_context(patient: Mapping[str, Any]) -> dict[str, Any]:
    available = {
        field: patient[field]
        for field in RECOMMENDED_BIOME_FIELDS
        if field in patient and has_value(patient[field])
    }
    return {
        'available_fields': available,
        'missing_recommended_fields': list(
            missing_recommended_fields(patient)
        ),
    }


def build_prompt_fragment() -> str:
    return (
        'Consider gut microbiome context when clinically appropriate. '
        'Use available diet, stool pattern, medication, antibiotic exposure, '
        'allergy, and symptom information. Keep conclusions cautious, '
        'identify missing information, and do not replace clinician judgment.'
    )
