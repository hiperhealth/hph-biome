from dataclasses import FrozenInstanceError, replace

import pytest

from hphbiome import CuratedKnowledgeRecord


def make_record() -> CuratedKnowledgeRecord:
    return CuratedKnowledgeRecord(
        id='fictional-record-1',
        title='Fictional knowledge note',
        synthesis='A fictional synthesis used only for model testing.',
        references=['fictional-reference-b', 'fictional-reference-a'],
        review_status='fictional-review-state',
    )


def test_record_preserves_text_and_reference_order() -> None:
    references = ['fictional-reference-b', 'fictional-reference-a']
    record = CuratedKnowledgeRecord(
        id='  fictional-record-1  ',
        title='  Fictional knowledge note  ',
        synthesis='  Fictional synthesis text.  ',
        references=references,
        review_status='  fictional-review-state  ',
    )

    references.reverse()

    assert record.id == '  fictional-record-1  '
    assert record.title == '  Fictional knowledge note  '
    assert record.synthesis == '  Fictional synthesis text.  '
    assert record.references == (
        'fictional-reference-b',
        'fictional-reference-a',
    )
    assert record.review_status == '  fictional-review-state  '
    with pytest.raises(FrozenInstanceError):
        setattr(record, 'title', 'Changed title')


def test_empty_references_are_accepted_and_normalized() -> None:
    record = replace(make_record(), references=[])

    assert record.references == ()


def test_to_dict_is_deterministic() -> None:
    record = make_record()
    expected = {
        'id': 'fictional-record-1',
        'title': 'Fictional knowledge note',
        'synthesis': 'A fictional synthesis used only for model testing.',
        'references': ['fictional-reference-b', 'fictional-reference-a'],
        'review_status': 'fictional-review-state',
    }

    first = record.to_dict()
    second = record.to_dict()

    assert first == expected
    assert second == expected
    assert list(first) == [
        'id',
        'title',
        'synthesis',
        'references',
        'review_status',
    ]


def test_all_fields_are_required() -> None:
    with pytest.raises(TypeError, match='review_status'):
        CuratedKnowledgeRecord(
            id='fictional-record-1',
            title='Fictional knowledge note',
            synthesis='Fictional synthesis text.',
            references=[],
        )


@pytest.mark.parametrize(
    'field_name', ['id', 'title', 'synthesis', 'review_status']
)
@pytest.mark.parametrize('value', [None, 42], ids=['none', 'integer'])
def test_scalar_fields_reject_non_strings(
    field_name: str, value: object
) -> None:
    with pytest.raises(TypeError, match=rf'^{field_name} must be a string$'):
        replace(make_record(), **{field_name: value})


@pytest.mark.parametrize(
    'field_name', ['id', 'title', 'synthesis', 'review_status']
)
@pytest.mark.parametrize('value', ['', '  '], ids=['empty', 'whitespace'])
def test_scalar_fields_reject_blank_strings(
    field_name: str, value: str
) -> None:
    with pytest.raises(ValueError, match=rf'^{field_name} must not be blank$'):
        replace(make_record(), **{field_name: value})


@pytest.mark.parametrize(
    'references',
    ['fictional-reference', {'fictional-reference': 'value'}, {'unordered'}],
    ids=['string', 'mapping', 'set'],
)
def test_references_reject_invalid_containers(references: object) -> None:
    with pytest.raises(
        TypeError,
        match=r'^references must be an ordered sequence of strings$',
    ):
        replace(make_record(), references=references)


@pytest.mark.parametrize(
    ('references', 'error_type', 'message'),
    [
        ([42], TypeError, r'^references\[0\] must be a string$'),
        (['  '], ValueError, r'^references\[0\] must not be blank$'),
    ],
    ids=['non-string', 'blank'],
)
def test_references_validate_each_entry(
    references: object,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        replace(make_record(), references=references)
