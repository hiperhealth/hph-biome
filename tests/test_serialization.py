import pytest

from hphbiome import (
    KNOWLEDGE_COLLECTION_SCHEMA_VERSION,
    CuratedKnowledgeRecord,
    KnowledgeCollection,
    ScientificReference,
    knowledge_collection_from_dict,
    knowledge_collection_to_dict,
)


def make_reference(
    name: str,
    *,
    identifier: str | None = None,
    canonical_url: str | None = None,
) -> ScientificReference:
    return ScientificReference(
        title=f'Fictional source {name}',
        authors=[f'Example Author {name}', f'Sample Contributor {name}'],
        source='Imaginary Research Review',
        identifier=identifier,
        canonical_url=canonical_url,
    )


def make_record(
    record_id: str,
    *,
    references: list[str] | None = None,
) -> CuratedKnowledgeRecord:
    return CuratedKnowledgeRecord(
        id=record_id,
        title=f'Fictional title for {record_id}',
        synthesis=f'Fictional synthesis for {record_id}.',
        references=[] if references is None else references,
        review_status='fictional-review-state',
    )


def make_collection() -> KnowledgeCollection:
    first_identifier = 'fictional-id:first'
    second_url = 'https://example.test/sources/second'
    first_reference = make_reference('first', identifier=first_identifier)
    second_reference = make_reference('second', canonical_url=second_url)
    first_record = make_record(
        'fictional-record-b', references=[second_url, first_identifier]
    )
    second_record = make_record(
        'fictional-record-a', references=[first_identifier]
    )
    return KnowledgeCollection(
        records=[first_record, second_record],
        references=[first_reference, second_reference],
    )


def test_empty_collection_round_trip() -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())

    assert serialized == {
        'schema_version': KNOWLEDGE_COLLECTION_SCHEMA_VERSION,
        'references': [],
        'records': [],
    }
    assert knowledge_collection_from_dict(serialized) == KnowledgeCollection()


def test_populated_collection_round_trip_preserves_all_ordering() -> None:
    collection = make_collection()

    reconstructed = knowledge_collection_from_dict(
        knowledge_collection_to_dict(collection)
    )

    assert reconstructed == collection
    assert [record.id for record in reconstructed.records] == [
        'fictional-record-b',
        'fictional-record-a',
    ]
    assert [reference.title for reference in reconstructed.references] == [
        'Fictional source first',
        'Fictional source second',
    ]
    assert reconstructed.references[0].authors == (
        'Example Author first',
        'Sample Contributor first',
    )
    assert reconstructed.records[0].references == (
        'https://example.test/sources/second',
        'fictional-id:first',
    )


def test_serialized_field_order_is_deterministic() -> None:
    first = knowledge_collection_to_dict(make_collection())
    second = knowledge_collection_to_dict(make_collection())

    assert first == second
    assert list(first) == ['schema_version', 'references', 'records']
    assert list(first['references'][0]) == [
        'title',
        'authors',
        'source',
        'identifier',
        'canonical_url',
    ]
    assert list(first['records'][0]) == [
        'id',
        'title',
        'synthesis',
        'references',
        'review_status',
    ]


def test_to_dict_requires_a_knowledge_collection() -> None:
    with pytest.raises(
        TypeError, match=r'^collection must be a KnowledgeCollection$'
    ):
        knowledge_collection_to_dict({})  # type: ignore[arg-type]


def test_from_dict_requires_a_mapping() -> None:
    with pytest.raises(TypeError, match=r'^value must be a mapping$'):
        knowledge_collection_from_dict([])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    'field_name', ['schema_version', 'references', 'records']
)
def test_from_dict_rejects_missing_top_level_fields(
    field_name: str,
) -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    del serialized[field_name]

    with pytest.raises(
        ValueError,
        match=rf"^collection: missing required field '{field_name}'$",
    ):
        knowledge_collection_from_dict(serialized)


@pytest.mark.parametrize('schema_version', [0, 2])
def test_from_dict_rejects_unsupported_schema_versions(
    schema_version: int,
) -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    serialized['schema_version'] = schema_version

    with pytest.raises(
        ValueError,
        match=rf'^unsupported schema_version: {schema_version}$',
    ):
        knowledge_collection_from_dict(serialized)


@pytest.mark.parametrize('schema_version', [True, '1', None])
def test_from_dict_rejects_invalid_schema_version_types(
    schema_version: object,
) -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    serialized['schema_version'] = schema_version

    with pytest.raises(
        TypeError, match=r'^schema_version must be an integer$'
    ):
        knowledge_collection_from_dict(serialized)


@pytest.mark.parametrize('field_name', ['references', 'records'])
@pytest.mark.parametrize(
    'value', ['not-a-sequence', {'unordered': 'mapping'}, {'unordered'}]
)
def test_from_dict_rejects_invalid_top_level_collections(
    field_name: str, value: object
) -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    serialized[field_name] = value

    with pytest.raises(
        TypeError,
        match=rf'^{field_name} must be an ordered sequence$',
    ):
        knowledge_collection_from_dict(serialized)


@pytest.mark.parametrize('field_name', ['references', 'records'])
def test_from_dict_requires_nested_mappings(field_name: str) -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    serialized[field_name] = ['not-a-mapping']

    with pytest.raises(
        TypeError, match=rf'^{field_name}\[0\] must be a mapping$'
    ):
        knowledge_collection_from_dict(serialized)


def test_from_dict_reports_invalid_reference_context() -> None:
    serialized = knowledge_collection_to_dict(make_collection())
    serialized['references'][1]['authors'] = []

    with pytest.raises(
        ValueError,
        match=(r'^references\[1\]: authors must contain at least one author$'),
    ):
        knowledge_collection_from_dict(serialized)


def test_from_dict_reports_invalid_record_context() -> None:
    serialized = knowledge_collection_to_dict(make_collection())
    serialized['records'][1]['title'] = '  '

    with pytest.raises(
        ValueError,
        match=r'^records\[1\]: title must not be blank$',
    ):
        knowledge_collection_from_dict(serialized)


@pytest.mark.parametrize(
    ('field_name', 'nested_field', 'message'),
    [
        (
            'references',
            'source',
            r'^references\[0\]: source must be a string$',
        ),
        (
            'records',
            'review_status',
            r'^records\[0\]: review_status must be a string$',
        ),
    ],
)
def test_from_dict_reports_nested_type_error_context(
    field_name: str, nested_field: str, message: str
) -> None:
    serialized = knowledge_collection_to_dict(make_collection())
    serialized[field_name][0][nested_field] = 42

    with pytest.raises(TypeError, match=message):
        knowledge_collection_from_dict(serialized)


@pytest.mark.parametrize(
    ('field_name', 'entry'),
    [
        (
            'references',
            {
                'authors': ['Example Author'],
                'source': 'Imaginary Research Review',
                'identifier': 'fictional-id:missing-title',
            },
        ),
        (
            'records',
            {
                'id': 'fictional-record-missing-title',
                'synthesis': 'Fictional synthesis.',
                'references': [],
                'review_status': 'fictional-review-state',
            },
        ),
    ],
)
def test_from_dict_reports_missing_nested_fields(
    field_name: str, entry: dict[str, object]
) -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    serialized[field_name] = [entry]

    with pytest.raises(
        ValueError,
        match=rf"^{field_name}\[0\]: missing required field 'title'$",
    ):
        knowledge_collection_from_dict(serialized)


def test_from_dict_rejects_dangling_record_references() -> None:
    serialized = knowledge_collection_to_dict(KnowledgeCollection())
    serialized['records'] = [
        make_record(
            'fictional-record-dangling',
            references=['fictional-id:unknown'],
        ).to_dict()
    ]

    with pytest.raises(
        ValueError,
        match=(
            r"^record 'fictional-record-dangling' contains unresolved "
            r"scientific reference 'fictional-id:unknown'$"
        ),
    ):
        knowledge_collection_from_dict(serialized)
