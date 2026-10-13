"""Ingestion error types."""

from __future__ import annotations


class IngestionError(Exception):
    """Base class for all ingestion failures."""


class SourceFileError(IngestionError):
    """The input file is missing, unreadable, or not an accepted file type."""


class SchemaValidationError(IngestionError):
    """The input does not satisfy its dataset contract."""

    def __init__(self, dataset: str, source: str, issues: list[str]) -> None:
        self.dataset = dataset
        self.source = source
        self.issues = issues
        detail = "\n".join(f"  - {i}" for i in issues)
        super().__init__(
            f"Schema validation failed for '{dataset}' ({source}): "
            f"{len(issues)} issue(s)\n{detail}"
        )
