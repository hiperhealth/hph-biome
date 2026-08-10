from dataclasses import FrozenInstanceError, replace

import pytest

from hphbiome import ScientificReference


def make_reference() -> ScientificReference:
    return ScientificReference(
        title='Fictional source title',
        authors=['Example Author', 'Sample Contributor'],
        source='Imaginary Research Review',
        identifier='fictional-id:alpha-001',
        canonical_url='https://example.test/sources/alpha-001',
    )


def test_reference_preserves_text_and_author_order() -> None:
    authors = ['  Example Author  ', '  Sample Contributor  ']
    reference = ScientificReference(
        title='  Fictional source title  ',
        authors=authors,
        source='  Imaginary Research Review  ',
        identifier='  fictional-id:alpha-001  ',
    )

    authors.reverse()

    assert reference.title == '  Fictional source title  '
    assert reference.authors == (
        '  Example Author  ',
        '  Sample Contributor  ',
    )
    assert reference.source == '  Imaginary Research Review  '
    assert reference.identifier == '  fictional-id:alpha-001  '
    with pytest.raises(FrozenInstanceError):
        setattr(reference, 'title', 'Changed title')


@pytest.mark.parametrize(
    ('identifier', 'canonical_url'),
    [
        ('fictional-id:alpha-001', None),
        (None, 'https://example.test/sources/alpha-001'),
        (
            'fictional-id:alpha-001',
            'https://example.test/sources/alpha-001',
        ),
    ],
    ids=['identifier', 'canonical-url', 'both'],
)
def test_reference_accepts_supported_source_identification(
    identifier: str | None, canonical_url: str | None
) -> None:
    reference = replace(
        make_reference(),
        identifier=identifier,
        canonical_url=canonical_url,
    )

    assert reference.identifier == identifier
    assert reference.canonical_url == canonical_url


def test_reference_requires_source_identification() -> None:
    with pytest.raises(
        ValueError,
        match=r'^identifier or canonical_url must be provided$',
    ):
        replace(make_reference(), identifier=None, canonical_url=None)


@pytest.mark.parametrize('field_name', ['title', 'source'])
@pytest.mark.parametrize('value', [None, 42], ids=['none', 'integer'])
def test_required_scalar_fields_reject_non_strings(
    field_name: str, value: object
) -> None:
    with pytest.raises(TypeError, match=rf'^{field_name} must be a string$'):
        replace(make_reference(), **{field_name: value})


@pytest.mark.parametrize('field_name', ['title', 'source'])
@pytest.mark.parametrize('value', ['', '  '], ids=['empty', 'whitespace'])
def test_required_scalar_fields_reject_blank_strings(
    field_name: str, value: str
) -> None:
    with pytest.raises(ValueError, match=rf'^{field_name} must not be blank$'):
        replace(make_reference(), **{field_name: value})


@pytest.mark.parametrize(
    'authors',
    ['Example Author', {'Example Author': 'value'}, {'Example Author'}],
    ids=['string', 'mapping', 'set'],
)
def test_authors_reject_invalid_containers(authors: object) -> None:
    with pytest.raises(
        TypeError,
        match=r'^authors must be an ordered sequence of strings$',
    ):
        replace(make_reference(), authors=authors)


def test_authors_require_at_least_one_entry() -> None:
    with pytest.raises(
        ValueError, match=r'^authors must contain at least one author$'
    ):
        replace(make_reference(), authors=[])


@pytest.mark.parametrize(
    ('authors', 'error_type', 'message'),
    [
        ([42], TypeError, r'^authors\[0\] must be a string$'),
        (['  '], ValueError, r'^authors\[0\] must not be blank$'),
    ],
    ids=['non-string', 'blank'],
)
def test_authors_validate_each_entry(
    authors: object,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        replace(make_reference(), authors=authors)


@pytest.mark.parametrize('field_name', ['identifier', 'canonical_url'])
@pytest.mark.parametrize('value', [42, '  '], ids=['non-string', 'blank'])
def test_optional_identification_fields_validate_when_present(
    field_name: str, value: object
) -> None:
    error_type = TypeError if not isinstance(value, str) else ValueError
    message = (
        rf'^{field_name} must be a string$'
        if error_type is TypeError
        else rf'^{field_name} must not be blank$'
    )

    with pytest.raises(error_type, match=message):
        replace(make_reference(), **{field_name: value})


@pytest.mark.parametrize(
    'canonical_url',
    [
        'example.test/sources/alpha-001',
        '/sources/alpha-001',
        'ftp://example.test/sources/alpha-001',
        'https://example test/sources/alpha-001',
        'https://example.test:invalid/sources/alpha-001',
    ],
    ids=[
        'missing-scheme',
        'relative',
        'unsupported-scheme',
        'whitespace',
        'invalid-port',
    ],
)
def test_canonical_url_rejects_malformed_values(canonical_url: str) -> None:
    with pytest.raises(
        ValueError,
        match=r'^canonical_url must be an absolute HTTP or HTTPS URL$',
    ):
        replace(make_reference(), canonical_url=canonical_url)


def test_to_dict_is_deterministic() -> None:
    reference = make_reference()
    expected = {
        'title': 'Fictional source title',
        'authors': ['Example Author', 'Sample Contributor'],
        'source': 'Imaginary Research Review',
        'identifier': 'fictional-id:alpha-001',
        'canonical_url': 'https://example.test/sources/alpha-001',
    }

    first = reference.to_dict()
    second = reference.to_dict()

    assert first == expected
    assert second == expected
    assert list(first) == [
        'title',
        'authors',
        'source',
        'identifier',
        'canonical_url',
    ]


def test_duplicate_handling_uses_collection_semantics() -> None:
    first = make_reference()
    second = make_reference()
    references = [first, second]

    assert first == second
    assert len(references) == 2
    assert len({first, second}) == 1
