from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path

from hphbiome.collection import KnowledgeCollection


def _validate_non_blank_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f'{field_name} must be a string')
    if not value.strip():
        raise ValueError(f'{field_name} must not be blank')


@dataclass(frozen=True)
class ArticleText:
    """Exact text loaded for one parent curated-knowledge record."""

    record_id: str
    text: str

    def __post_init__(self) -> None:
        _validate_non_blank_string('record_id', self.record_id)
        _validate_non_blank_string('text', self.text)


def load_article_texts(
    directory: str | PathLike[str],
    collection: KnowledgeCollection,
) -> tuple[ArticleText, ...]:
    """Load direct ``<record-id>.txt`` files in filename order.

    Only lowercase ``.txt`` files directly inside ``directory`` are loaded.
    Other files and nested directories are ignored. Text is decoded as UTF-8
    and preserved exactly, including whitespace and newlines.
    """
    if not isinstance(collection, KnowledgeCollection):
        raise TypeError('collection must be a KnowledgeCollection')

    root = Path(directory)
    if not root.is_dir():
        raise ValueError(
            'article text directory does not exist or is not a directory: '
            f'{str(root)!r}'
        )

    paths = sorted(
        (
            path
            for path in root.iterdir()
            if path.is_file() and path.suffix == '.txt'
        ),
        key=lambda path: path.name,
    )

    articles: list[ArticleText] = []
    for path in paths:
        record_id = path.stem
        if collection.get_record(record_id) is None:
            raise ValueError(
                f'article text file {str(path)!r} maps to unknown curated '
                f'record {record_id!r}'
            )

        try:
            text = path.read_bytes().decode('utf-8')
        except UnicodeDecodeError as error:
            raise ValueError(
                f'article text file {str(path)!r} is not valid UTF-8'
            ) from error

        if not text.strip():
            raise ValueError(
                f'article text file {str(path)!r} must not be blank'
            )

        articles.append(ArticleText(record_id=record_id, text=text))

    return tuple(articles)
