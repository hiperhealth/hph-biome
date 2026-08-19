from dataclasses import FrozenInstanceError, replace

import pytest

from hphbiome import (
    CuratedKnowledgeRecord,
    RetrievedKnowledge,
    ScientificReference,
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
