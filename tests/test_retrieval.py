from dataclasses import FrozenInstanceError, replace

import pytest

from hphbiome import (
    CuratedKnowledgeRecord,
    KnowledgeCollection,
    RetrievedKnowledge,
    ScientificReference,
    retrieve_knowledge,
)


def make_record() -> CuratedKnowledgeRecord:
    return CuratedKnowledgeRecord(
        id='fictional-record-1',
        title='Fictional knowledge note',
        synthesis='A fictional synthesis used only for retrieval testing.',
        references=['fictional-id:alpha-001'],
        review_status='fictional-review-state',
    )


def make_reference(name: str) -> ScientificReference:
    return ScientificReference(
        title=f'Fictional source {name}',
        authors=[f'Example Author {name}'],
        source='Imaginary Research Review',
        identifier=f'fictional-id:{name.lower()}',
    )


def make_result() -> RetrievedKnowledge:
    return RetrievedKnowledge(
        record=make_record(),
        score=2.5,
        references=[make_reference('Alpha-001')],
    )


def make_search_record(
    record_id: str,
    *,
    title: str,
    synthesis: str,
    references: list[str] | None = None,
    review_status: str = 'fictional-review-state',
) -> CuratedKnowledgeRecord:
    return CuratedKnowledgeRecord(
        id=record_id,
        title=title,
        synthesis=synthesis,
        references=[] if references is None else references,
        review_status=review_status,
    )


def test_result_preserves_record_reference_order_and_immutability() -> None:
    record = make_record()
    first_reference = make_reference('First')
    second_reference = make_reference('Second')
    references = [first_reference, second_reference]

    result = RetrievedKnowledge(
        record=record,
        score=3,
        references=references,
    )
    references.reverse()

    assert result.record is record
    assert result.score == 3.0
    assert result.references == (first_reference, second_reference)
    with pytest.raises(FrozenInstanceError):
        setattr(result, 'score', 4.0)


def test_result_accepts_empty_references() -> None:
    result = RetrievedKnowledge(
        record=replace(make_record(), references=[]),
        score=-1.25,
        references=[],
    )

    assert result.score == -1.25
    assert result.references == ()


def test_all_fields_are_required() -> None:
    with pytest.raises(TypeError, match='references'):
        RetrievedKnowledge(record=make_record(), score=1.0)


@pytest.mark.parametrize(
    'record',
    [None, 'fictional-record-1'],
    ids=['none', 'record-id'],
)
def test_result_rejects_invalid_record(record: object) -> None:
    with pytest.raises(
        TypeError,
        match=r'^record must be a CuratedKnowledgeRecord$',
    ):
        replace(make_result(), record=record)


@pytest.mark.parametrize(
    'score',
    [None, True, '1.0'],
    ids=['none', 'boolean', 'string'],
)
def test_result_rejects_non_numeric_scores(score: object) -> None:
    with pytest.raises(TypeError, match=r'^score must be a real number$'):
        replace(make_result(), score=score)


@pytest.mark.parametrize(
    'score',
    [float('nan'), float('inf'), float('-inf')],
    ids=['nan', 'positive-infinity', 'negative-infinity'],
)
def test_result_rejects_non_finite_scores(score: float) -> None:
    with pytest.raises(ValueError, match=r'^score must be finite$'):
        replace(make_result(), score=score)


@pytest.mark.parametrize(
    'references',
    ['fictional-reference', {'fictional-reference': 'value'}, {'unordered'}],
    ids=['string', 'mapping', 'set'],
)
def test_result_rejects_invalid_reference_containers(
    references: object,
) -> None:
    with pytest.raises(
        TypeError,
        match=(
            r'^references must be an ordered sequence of '
            r'ScientificReference$'
        ),
    ):
        replace(make_result(), references=references)


def test_result_validates_each_reference() -> None:
    with pytest.raises(
        TypeError,
        match=r'^references\[0\] must be a ScientificReference$',
    ):
        replace(make_result(), references=['not-a-reference'])


def test_to_dict_is_deterministic() -> None:
    result = make_result()
    expected = {
        'record': {
            'id': 'fictional-record-1',
            'title': 'Fictional knowledge note',
            'synthesis': (
                'A fictional synthesis used only for retrieval testing.'
            ),
            'references': ['fictional-id:alpha-001'],
            'review_status': 'fictional-review-state',
        },
        'score': 2.5,
        'references': [
            {
                'title': 'Fictional source Alpha-001',
                'authors': ['Example Author Alpha-001'],
                'source': 'Imaginary Research Review',
                'identifier': 'fictional-id:alpha-001',
                'canonical_url': None,
            }
        ],
    }

    first = result.to_dict()
    second = result.to_dict()

    assert first == expected
    assert second == expected
    assert list(first) == ['record', 'score', 'references']


def test_retrieval_matches_titles_and_syntheses_case_insensitively() -> None:
    title_match = make_search_record(
        'fictional-record-title',
        title='Amber Constellation',
        synthesis='Fictional background text.',
    )
    synthesis_match = make_search_record(
        'fictional-record-synthesis',
        title='Fictional note',
        synthesis='A constellation appears in this fictional synthesis.',
    )
    collection = KnowledgeCollection(records=[title_match, synthesis_match])

    results = retrieve_knowledge(collection, 'CONSTELLATION')

    assert tuple(result.record for result in results) == (
        title_match,
        synthesis_match,
    )
    assert tuple(result.score for result in results) == (1.0, 1.0)


def test_retrieval_ranks_by_distinct_query_token_coverage() -> None:
    full_match = make_search_record(
        'fictional-record-full',
        title='Amber note',
        synthesis='A fictional comet observation.',
    )
    partial_match = make_search_record(
        'fictional-record-partial',
        title='Amber archive',
        synthesis='Fictional background text.',
    )
    collection = KnowledgeCollection(records=[partial_match, full_match])

    results = retrieve_knowledge(collection, 'amber comet comet')

    assert tuple(result.record for result in results) == (
        full_match,
        partial_match,
    )
    assert tuple(result.score for result in results) == (1.0, 0.5)


def test_retrieval_ties_preserve_collection_order() -> None:
    first = make_search_record(
        'fictional-record-z',
        title='Shared token',
        synthesis='First fictional synthesis.',
    )
    second = make_search_record(
        'fictional-record-a',
        title='Another note',
        synthesis='Second fictional synthesis with a shared token.',
    )
    collection = KnowledgeCollection(records=[first, second])

    results = retrieve_knowledge(collection, 'shared')

    assert tuple(result.record for result in results) == (first, second)


def test_retrieval_returns_resolved_provenance_in_record_order() -> None:
    identifier = 'fictional-id:alpha'
    canonical_url = 'https://example.test/sources/beta'
    identifier_reference = ScientificReference(
        title='Fictional identifier source',
        authors=['Example Author Alpha'],
        source='Imaginary Research Review',
        identifier=identifier,
    )
    url_reference = ScientificReference(
        title='Fictional URL source',
        authors=['Example Author Beta'],
        source='Imaginary Research Review',
        canonical_url=canonical_url,
    )
    record = make_search_record(
        'fictional-record-1',
        title='Traceable constellation',
        synthesis='Fictional provenance example.',
        references=[canonical_url, identifier],
    )
    collection = KnowledgeCollection(
        records=[record],
        references=[identifier_reference, url_reference],
    )

    result = retrieve_knowledge(collection, 'traceable')[0]

    assert result.references == (url_reference, identifier_reference)


def test_retrieval_searches_only_title_and_synthesis() -> None:
    metadata_value = 'metadata-only-token'
    reference = ScientificReference(
        title='Fictional source',
        authors=['Example Author'],
        source='Imaginary Research Review',
        identifier=metadata_value,
    )
    record = make_search_record(
        metadata_value,
        title='Fictional title',
        synthesis='Fictional synthesis.',
        references=[metadata_value],
        review_status=metadata_value,
    )
    collection = KnowledgeCollection(
        records=[record],
        references=[reference],
    )

    assert retrieve_knowledge(collection, 'metadata') == ()


@pytest.mark.parametrize('query', ['', '  '], ids=['empty', 'whitespace'])
def test_retrieval_rejects_blank_queries(query: str) -> None:
    with pytest.raises(ValueError, match=r'^query must not be blank$'):
        retrieve_knowledge(KnowledgeCollection(), query)


@pytest.mark.parametrize(
    'query',
    [None, 42],
    ids=['none', 'integer'],
)
def test_retrieval_rejects_non_string_queries(query: object) -> None:
    with pytest.raises(TypeError, match=r'^query must be a string$'):
        retrieve_knowledge(KnowledgeCollection(), query)


def test_retrieval_rejects_invalid_collections() -> None:
    with pytest.raises(
        TypeError,
        match=r'^collection must be a KnowledgeCollection$',
    ):
        retrieve_knowledge('not-a-collection', 'fictional')


def test_retrieval_returns_empty_immutable_results_deterministically() -> None:
    collection = KnowledgeCollection(
        records=[
            make_search_record(
                'fictional-record-1',
                title='Fictional title',
                synthesis='Fictional synthesis.',
            )
        ]
    )

    first = retrieve_knowledge(collection, '---')
    second = retrieve_knowledge(collection, 'missing')

    assert first == ()
    assert second == ()
    assert retrieve_knowledge(collection, 'missing') == second
