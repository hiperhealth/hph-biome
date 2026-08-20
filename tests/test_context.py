import pytest

from hphbiome import (
    CuratedKnowledgeRecord,
    RetrievedKnowledge,
    ScientificReference,
    build_structured_knowledge_context,
    build_text_knowledge_context,
)


def make_reference(
    name: str,
    *,
    identifier: str | None = None,
    canonical_url: str | None = None,
) -> ScientificReference:
    return ScientificReference(
        title=f'Fictional source {name}',
        authors=[f'Example Author {name}'],
        source='Imaginary Research Review',
        identifier=identifier,
        canonical_url=canonical_url,
    )


def make_result(
    record_id: str,
    *,
    title: str | None = None,
    synthesis: str | None = None,
    review_status: str = 'fictional-status',
    score: float = 0.5,
    references: list[ScientificReference] | None = None,
) -> RetrievedKnowledge:
    resolved_references = [] if references is None else references
    return RetrievedKnowledge(
        record=CuratedKnowledgeRecord(
            id=record_id,
            title=title or f'Fictional title for {record_id}',
            synthesis=(
                synthesis
                if synthesis is not None
                else f'Fictional synthesis for {record_id}.'
            ),
            references=[
                reference.identifier or reference.canonical_url
                for reference in resolved_references
            ],
            review_status=review_status,
        ),
        score=score,
        references=resolved_references,
    )


def test_empty_results_produce_documented_empty_context() -> None:
    assert build_structured_knowledge_context([]) == {'results': []}
    assert build_text_knowledge_context([]) == ''


def test_one_result_preserves_record_fields_and_score() -> None:
    result = make_result(
        'fictional-record-1',
        title='Fictional title',
        synthesis='Fictional synthesis.',
        review_status='fictional-status-a',
        score=0.75,
    )

    structured = build_structured_knowledge_context([result])
    text = build_text_knowledge_context([result])

    assert structured == {
        'results': [
            {
                'record_id': 'fictional-record-1',
                'title': 'Fictional title',
                'synthesis': 'Fictional synthesis.',
                'review_status': 'fictional-status-a',
                'score': 0.75,
                'references': [],
            }
        ]
    }
    assert list(structured) == ['results']
    assert list(structured['results'][0]) == [
        'record_id',
        'title',
        'synthesis',
        'review_status',
        'score',
        'references',
    ]
    assert text == (
        'Result 1\n'
        'Record ID: fictional-record-1\n'
        'Title: Fictional title\n'
        'Review status: fictional-status-a\n'
        'Relevance score: 0.75\n'
        'Synthesis:\n'
        'Fictional synthesis.\n'
        'References:\n'
        'None'
    )


def test_multiple_results_preserve_retrieval_order() -> None:
    first = make_result('fictional-record-b', score=0.8)
    second = make_result('fictional-record-a', score=0.4)

    structured = build_structured_knowledge_context([first, second])
    text = build_text_knowledge_context([first, second])

    assert [result['record_id'] for result in structured['results']] == [
        'fictional-record-b',
        'fictional-record-a',
    ]
    assert text.index('Record ID: fictional-record-b') < text.index(
        'Record ID: fictional-record-a'
    )


def test_multiple_references_preserve_identifiers_urls_and_order() -> None:
    identifier_reference = make_reference(
        'identifier', identifier='fictional-id:alpha'
    )
    url_reference = make_reference(
        'URL', canonical_url='https://example.test/sources/beta'
    )
    result = make_result(
        'fictional-record-1',
        references=[url_reference, identifier_reference],
    )

    structured = build_structured_knowledge_context([result])
    text = build_text_knowledge_context([result])

    assert structured['results'][0]['references'] == [
        {
            'identifier': None,
            'canonical_url': 'https://example.test/sources/beta',
        },
        {
            'identifier': 'fictional-id:alpha',
            'canonical_url': None,
        },
    ]
    assert text.index('https://example.test/sources/beta') < text.index(
        'fictional-id:alpha'
    )
    assert '1. Identifier: Not provided' in text
    assert '2. Identifier: fictional-id:alpha' in text


def test_synthesis_text_is_preserved_exactly() -> None:
    synthesis = '  First fictional line.\nSecond fictional line.  '
    result = make_result('fictional-record-1', synthesis=synthesis)

    structured = build_structured_knowledge_context([result])
    text = build_text_knowledge_context([result])

    assert structured['results'][0]['synthesis'] == synthesis
    assert f'Synthesis:\n{synthesis}\nReferences:' in text


def test_repeated_generation_is_deterministic() -> None:
    results = [
        make_result('fictional-record-1', score=0.75),
        make_result('fictional-record-2', score=0.25),
    ]

    assert build_structured_knowledge_context(
        results
    ) == build_structured_knowledge_context(results)
    assert build_text_knowledge_context(
        results
    ) == build_text_knowledge_context(results)


@pytest.mark.parametrize(
    'results',
    ['not-results', {'unordered': 'mapping'}, {'unordered'}],
    ids=['string', 'mapping', 'set'],
)
def test_context_rejects_invalid_result_containers(results: object) -> None:
    with pytest.raises(
        TypeError,
        match=r'^results must be an ordered sequence of RetrievedKnowledge$',
    ):
        build_structured_knowledge_context(results)


def test_context_validates_each_result() -> None:
    with pytest.raises(
        TypeError,
        match=r'^results\[0\] must be a RetrievedKnowledge$',
    ):
        build_text_knowledge_context(['not-a-result'])
