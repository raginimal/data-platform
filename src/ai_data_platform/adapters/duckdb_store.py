"""DuckDB adapter: the only place DuckDB-specific behavior lives (ARCH rules)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import duckdb

from ..domain.contracts import DatasetContract
from ..domain.errors import IngestionError

RAW_SCHEMA = "raw"


def raw_table(contract: DatasetContract) -> str:
    return f"{RAW_SCHEMA}.{contract.name}"


class DuckDBStore:
    def __init__(self, database: str | Path) -> None:
        database = str(database)
        if database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        try:
            self._con = duckdb.connect(database)
        except duckdb.Error as exc:
            raise IngestionError(f"Cannot open DuckDB database '{database}': {exc}") from exc

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> "DuckDBStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[tuple[Any, ...]]:
        return self._con.execute(sql, list(params)).fetchall()

    def load_datasets(
        self, datasets: Sequence[tuple[DatasetContract, list[tuple[Any, ...]], str]], run_id: str
    ) -> None:
        """Replace raw tables and record run metadata in one transaction."""
        con = self._con
        try:
            con.execute("BEGIN TRANSACTION")
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
            con.execute(
                f"""CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}.ingestion_runs (
                    run_id VARCHAR, dataset VARCHAR, contract_version VARCHAR,
                    source_file VARCHAR, row_count INTEGER, loaded_at TIMESTAMP)"""
            )
            loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)
            for contract, rows, source in datasets:
                columns = ", ".join(
                    f"{c.name} {c.type.value}{'' if c.nullable else ' NOT NULL'}"
                    for c in contract.columns
                )
                table = raw_table(contract)
                con.execute(f"DROP TABLE IF EXISTS {table}")
                con.execute(
                    f"CREATE TABLE {table} ({columns}, PRIMARY KEY ({contract.primary_key}))"
                )
                placeholders = ", ".join("?" for _ in contract.columns)
                con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
                con.execute(
                    f"INSERT INTO {RAW_SCHEMA}.ingestion_runs VALUES (?, ?, ?, ?, ?, ?)",
                    [run_id, contract.name, contract.version, source, len(rows), loaded_at],
                )
            con.execute("COMMIT")
        except duckdb.Error as exc:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
            raise IngestionError(f"DuckDB load failed; no changes were applied: {exc}") from exc
