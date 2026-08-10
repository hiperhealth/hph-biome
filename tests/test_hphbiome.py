import pytest

from hphbiome import (
    build_biome_context,
    build_prompt_fragment,
    field_description,
    field_label,
    has_value,
    missing_recommended_fields,
)


@pytest.mark.parametrize(
    'value',
    [None, '', '  ', {}, [], (), set()],
    ids=[
        'none',
        'empty-string',
        'whitespace',
        'mapping',
        'list',
        'tuple',
        'set',
    ],
)
def test_has_value_rejects_supported_empty_values(value: object) -> None:
    assert not has_value(value)


def test_has_value_accepts_non_empty_values() -> None:
    assert has_value('bloating')
    assert has_value(0)


def test_build_biome_context_fully_partitions_recommended_fields() -> None:
    patient = {
        'symptoms': 'bloating',
        'dietary_history': '',
        'stool_pattern': 'daily',
        'recent_antibiotics': [],
        'medications': ['probiotic'],
        'allergies': {},
        'unrelated': 'ignored',
    }

    context = build_biome_context(patient)

    assert context == {
        'available_fields': {
            'symptoms': 'bloating',
            'stool_pattern': 'daily',
            'medications': ['probiotic'],
        },
        'missing_recommended_fields': [
            'dietary_history',
            'recent_antibiotics',
            'allergies',
        ],
    }


def test_field_metadata_falls_back_for_unknown_fields() -> None:
    assert field_label('clinical_notes') == 'Clinical Notes'
    assert field_description('clinical_notes') == ''


def test_missing_fields_and_prompt_fragment_are_stable() -> None:
    missing = missing_recommended_fields({'symptoms': 'bloating'})

    assert 'symptoms' not in missing
    assert 'stool_pattern' in missing
    assert field_label('stool_pattern') == (
        'Bowel movement frequency and stool pattern'
    )
    assert field_description('stool_pattern') == (
        'Include frequency, consistency, urgency, blood, or mucus.'
    )
    assert 'clinician judgment' in build_prompt_fragment()


def test_version_fallback(monkeypatch) -> None:
    import hphbiome

    def raise_not_found(_: str) -> str:
        raise hphbiome.PackageNotFoundError

    monkeypatch.setattr(hphbiome, 'version', raise_not_found)

    assert hphbiome._version() == '0.1.0'
