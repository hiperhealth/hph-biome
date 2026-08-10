from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit


def _validate_non_blank_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f'{field_name} must be a string')
    if not value.strip():
        raise ValueError(f'{field_name} must not be blank')


@dataclass(frozen=True)
class ScientificReference:
    """Metadata for one scientific source.

    Instances are not deduplicated or merged. Exact duplicates compare equal,
    so callers can choose whether an ordered collection preserves them or a
    set removes them.
    """

    title: str
    authors: Sequence[str]
    source: str
    identifier: str | None = None
    canonical_url: str | None = None

    def __post_init__(self) -> None:
        _validate_non_blank_string('title', self.title)
        _validate_non_blank_string('source', self.source)

        if isinstance(self.authors, (str, bytes, bytearray)) or not isinstance(
            self.authors, Sequence
        ):
            raise TypeError('authors must be an ordered sequence of strings')
        if not self.authors:
            raise ValueError('authors must contain at least one author')

        for index, author in enumerate(self.authors):
            _validate_non_blank_string(f'authors[{index}]', author)

        if self.identifier is not None:
            _validate_non_blank_string('identifier', self.identifier)
        if self.canonical_url is not None:
            _validate_non_blank_string('canonical_url', self.canonical_url)
            self._validate_canonical_url()
        if self.identifier is None and self.canonical_url is None:
            raise ValueError('identifier or canonical_url must be provided')

        object.__setattr__(self, 'authors', tuple(self.authors))

    def _validate_canonical_url(self) -> None:
        canonical_url = self.canonical_url
        if canonical_url is None:
            return

        try:
            parsed_url = urlsplit(canonical_url)
            parsed_url.port
        except ValueError as error:
            raise ValueError(
                'canonical_url must be an absolute HTTP or HTTPS URL'
            ) from error

        if (
            parsed_url.scheme not in {'http', 'https'}
            or not parsed_url.netloc
            or not parsed_url.hostname
            or any(character.isspace() for character in canonical_url)
        ):
            raise ValueError(
                'canonical_url must be an absolute HTTP or HTTPS URL'
            )

    def to_dict(self) -> dict[str, object]:
        """Serialize the reference using a stable field order."""
        return {
            'title': self.title,
            'authors': list(self.authors),
            'source': self.source,
            'identifier': self.identifier,
            'canonical_url': self.canonical_url,
        }
