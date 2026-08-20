from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from hphbiome import (
    ArticleText,
    CuratedKnowledgeRecord,
    KnowledgeCollection,
    ScientificReference,
    load_article_texts,
)


def make_record(
    record_id: str,
    *,
    references: list[str] | None = None,
) -> CuratedKnowledgeRecord:
    return CuratedKnowledgeRecord(
        id=record_id,
        title=f'Fictional article {record_id}',
        synthesis=f'Fictional synthesis for {record_id}.',
        references=[] if references is None else references,
        review_status='fictional-reviewed',
    )


def test_article_text_is_immutable_and_preserves_exact_text() -> None:
    article = ArticleText(
        record_id='fictional-record-1',
        text='  Fictional opening.\n\nFictional ending.  \n',
    )

    assert article.record_id == 'fictional-record-1'
    assert article.text == '  Fictional opening.\n\nFictional ending.  \n'
    with pytest.raises(FrozenInstanceError):
        setattr(article, 'text', 'Changed text')


@pytest.mark.parametrize('field_name', ['record_id', 'text'])
@pytest.mark.parametrize('value', [None, 42], ids=['none', 'integer'])
def test_article_text_rejects_non_string_fields(
    field_name: str,
    value: object,
) -> None:
    article = ArticleText('fictional-record-1', 'Fictional article text.')

    with pytest.raises(TypeError, match=rf'^{field_name} must be a string$'):
        replace(article, **{field_name: value})


@pytest.mark.parametrize('field_name', ['record_id', 'text'])
@pytest.mark.parametrize('value', ['', ' \n\t'], ids=['empty', 'whitespace'])
def test_article_text_rejects_blank_fields(
    field_name: str,
    value: str,
) -> None:
    article = ArticleText('fictional-record-1', 'Fictional article text.')

    with pytest.raises(ValueError, match=rf'^{field_name} must not be blank$'):
        replace(article, **{field_name: value})


def test_loader_reads_one_utf8_file_and_preserves_text(
    tmp_path: Path,
) -> None:
    collection = KnowledgeCollection(
        records=[make_record('fictional-record-1')]
    )
    expected_text = '  Fictional café text.\r\nSecond line.  \r\n'
    (tmp_path / 'fictional-record-1.txt').write_bytes(
        expected_text.encode('utf-8')
    )

    articles = load_article_texts(tmp_path, collection)

    assert articles == (ArticleText('fictional-record-1', expected_text),)


def test_loader_returns_multiple_files_in_filename_order(
    tmp_path: Path,
) -> None:
    collection = KnowledgeCollection(
        records=[
            make_record('fictional-record-b'),
            make_record('fictional-record-a'),
        ]
    )
    (tmp_path / 'fictional-record-b.txt').write_text(
        'Fictional B text.',
        encoding='utf-8',
    )
    (tmp_path / 'fictional-record-a.txt').write_text(
        'Fictional A text.',
        encoding='utf-8',
    )

    articles = load_article_texts(tmp_path, collection)

    assert tuple(article.record_id for article in articles) == (
        'fictional-record-a',
        'fictional-record-b',
    )


def test_loader_requires_a_knowledge_collection(tmp_path: Path) -> None:
    with pytest.raises(
        TypeError,
        match=r'^collection must be a KnowledgeCollection$',
    ):
        load_article_texts(tmp_path, object())  # type: ignore[arg-type]


def test_loader_rejects_a_missing_directory(tmp_path: Path) -> None:
    missing_directory = tmp_path / 'missing'

    with pytest.raises(ValueError) as error:
        load_article_texts(missing_directory, KnowledgeCollection())

    assert str(error.value) == (
        'article text directory does not exist or is not a directory: '
        f'{str(missing_directory)!r}'
    )


@pytest.mark.parametrize('content', ['', ' \n\t'], ids=['empty', 'whitespace'])
def test_loader_rejects_blank_files_with_the_path(
    tmp_path: Path,
    content: str,
) -> None:
    collection = KnowledgeCollection(
        records=[make_record('fictional-record-1')]
    )
    path = tmp_path / 'fictional-record-1.txt'
    path.write_text(content, encoding='utf-8')

    with pytest.raises(ValueError) as error:
        load_article_texts(tmp_path, collection)

    assert str(error.value) == (
        f'article text file {str(path)!r} must not be blank'
    )


def test_loader_rejects_invalid_utf8_with_the_path(tmp_path: Path) -> None:
    collection = KnowledgeCollection(
        records=[make_record('fictional-record-1')]
    )
    path = tmp_path / 'fictional-record-1.txt'
    path.write_bytes(b'Fictional text: \xff')

    with pytest.raises(ValueError) as error:
        load_article_texts(tmp_path, collection)

    assert str(error.value) == (
        f'article text file {str(path)!r} is not valid UTF-8'
    )


def test_loader_rejects_unknown_record_id_with_the_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / 'fictional-record-missing.txt'
    path.write_text('Fictional article text.', encoding='utf-8')

    with pytest.raises(ValueError) as error:
        load_article_texts(tmp_path, KnowledgeCollection())

    assert str(error.value) == (
        f'article text file {str(path)!r} maps to unknown curated record '
        "'fictional-record-missing'"
    )


def test_loader_ignores_non_txt_files_and_nested_directories(
    tmp_path: Path,
) -> None:
    collection = KnowledgeCollection(
        records=[make_record('fictional-record-1')]
    )
    (tmp_path / 'fictional-record-1.txt').write_text(
        'Direct fictional text.',
        encoding='utf-8',
    )
    (tmp_path / 'notes.md').write_text('Ignored notes.', encoding='utf-8')
    (tmp_path / 'uppercase.TXT').write_text(
        'Ignored uppercase extension.',
        encoding='utf-8',
    )
    nested = tmp_path / 'nested'
    nested.mkdir()
    (nested / 'unknown-record.txt').write_text(
        'Ignored nested text.',
        encoding='utf-8',
    )

    articles = load_article_texts(tmp_path, collection)

    assert articles == (
        ArticleText('fictional-record-1', 'Direct fictional text.'),
    )


def test_loaded_article_provenance_resolves_through_collection(
    tmp_path: Path,
) -> None:
    reference = ScientificReference(
        title='Fictional source title',
        authors=['Example Author'],
        source='Imaginary Research Review',
        identifier='fictional-id:article-source',
    )
    record = make_record(
        'fictional-record-1',
        references=['fictional-id:article-source'],
    )
    collection = KnowledgeCollection(
        records=[record],
        references=[reference],
    )
    (tmp_path / 'fictional-record-1.txt').write_text(
        'Fictional article text.',
        encoding='utf-8',
    )

    article = load_article_texts(tmp_path, collection)[0]

    assert collection.get_record(article.record_id) is record
    assert collection.resolve_references(article.record_id) == (reference,)
