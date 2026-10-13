"""Boundary validation of untrusted CSV input against a dataset contract."""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .contracts import Column, ColumnType, DatasetContract
from .errors import SchemaValidationError, SourceFileError

MAX_ISSUES = 20
MAX_FILE_BYTES = 50 * 1024 * 1024


def _convert(raw: str, column: Column) -> Any:
    if column.type is ColumnType.INTEGER:
        return int(raw)
    if column.type is ColumnType.DECIMAL:
        value = Decimal(raw)
        if not value.is_finite() or abs(value) >= Decimal("1e8") or -value.as_tuple().exponent > 2:
            raise ValueError("out of range or more than 2 decimal places")
        return value
    if column.type is ColumnType.DATE:
        return date.fromisoformat(raw)
    return raw


def read_dataset(path: str | Path, contract: DatasetContract) -> list[tuple[Any, ...]]:
    """Return typed rows or raise SourceFileError / SchemaValidationError."""
    path = Path(path)
    if path.suffix.lower() != ".csv":
        raise SourceFileError(f"Unsupported file type '{path.suffix}' for {path}; expected .csv")
    if not path.is_file():
        raise SourceFileError(f"Input file not found: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise SourceFileError(f"Input file exceeds {MAX_FILE_BYTES} bytes: {path}")

    source = str(path)
    issues: list[str] = []
    rows: list[tuple[Any, ...]] = []
    seen_keys: set[Any] = set()
    key_index = contract.column_names.index(contract.primary_key)

    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if header is None:
                raise SchemaValidationError(contract.name, source, ["file is empty"])

            header = [h.strip() for h in header]
            expected = list(contract.column_names)
            if header != expected:
                missing = [c for c in expected if c not in header]
                extra = [c for c in header if c not in expected]
                problems = [f"header must be exactly {expected}, found {header}"]
                if missing:
                    problems.append(f"missing columns: {missing}")
                if extra:
                    problems.append(f"unexpected columns: {extra}")
                raise SchemaValidationError(contract.name, source, problems)

            for line_no, record in enumerate(reader, start=2):
                if len(issues) >= MAX_ISSUES:
                    issues.append(f"stopped after {MAX_ISSUES} issues")
                    break
                if not any(cell.strip() for cell in record):
                    continue
                if len(record) != len(expected):
                    issues.append(
                        f"line {line_no}: expected {len(expected)} fields, found {len(record)}"
                    )
                    continue
                values: list[Any] = []
                row_ok = True
                for column, cell in zip(contract.columns, record):
                    cell = cell.strip()
                    if cell == "":
                        if not column.nullable:
                            issues.append(f"line {line_no}: '{column.name}' is required")
                            row_ok = False
                        values.append(None)
                        continue
                    try:
                        values.append(_convert(cell, column))
                    except (ValueError, InvalidOperation):
                        issues.append(
                            f"line {line_no}: '{column.name}' value {cell!r} "
                            f"is not a valid {column.type.value}"
                        )
                        row_ok = False
                        values.append(None)
                if not row_ok:
                    continue
                key = values[key_index]
                if key in seen_keys:
                    issues.append(f"line {line_no}: duplicate {contract.primary_key} {key!r}")
                    continue
                seen_keys.add(key)
                rows.append(tuple(values))
    except UnicodeDecodeError as exc:
        raise SourceFileError(f"File is not valid UTF-8: {path} ({exc.reason})") from exc
    except csv.Error as exc:
        raise SchemaValidationError(contract.name, source, [f"malformed CSV: {exc}"]) from exc
    except OSError as exc:
        raise SourceFileError(f"Cannot read {path}: {exc.strerror}") from exc

    if issues:
        raise SchemaValidationError(contract.name, source, issues)
    if not rows:
        raise SchemaValidationError(contract.name, source, ["file contains no data rows"])
    return rows
