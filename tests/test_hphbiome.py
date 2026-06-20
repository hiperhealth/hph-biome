from hphbiome import (
    build_biome_context,
    build_prompt_fragment,
    field_label,
    has_value,
    missing_recommended_fields,
)


def test_has_value_handles_common_empty_values() -> None:
    assert not has_value(None)
    assert not has_value('  ')
    assert not has_value([])
    assert has_value('bloating')
    assert has_value(0)


def test_build_biome_context_keeps_available_recommended_fields() -> None:
    patient = {
        'symptoms': 'bloating',
        'dietary_history': '',
        'unrelated': 'ignored',
    }

    context = build_biome_context(patient)

    assert context['available_fields'] == {'symptoms': 'bloating'}
    assert 'dietary_history' in context['missing_recommended_fields']
    assert 'unrelated' not in context['missing_recommended_fields']


def test_missing_fields_and_prompt_fragment_are_stable() -> None:
    missing = missing_recommended_fields({'symptoms': 'bloating'})

    assert 'symptoms' not in missing
    assert 'stool_pattern' in missing
    assert field_label('stool_pattern') == (
        'Bowel movement frequency and stool pattern'
    )
    assert 'clinician judgment' in build_prompt_fragment()


def test_version_fallback(monkeypatch) -> None:
    import hphbiome

    def raise_not_found(_: str) -> str:
        raise hphbiome.PackageNotFoundError

    monkeypatch.setattr(hphbiome, 'version', raise_not_found)

    assert hphbiome._version() == '0.1.0'
