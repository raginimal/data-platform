"""Ingestion orchestration: validate every input first, then load atomically."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from ..adapters.duckdb_store import DuckDBStore
from ..domain.contracts import CUSTOMERS_CONTRACT, SALES_CONTRACT
from ..domain.validation import read_dataset


@dataclass(frozen=True)
class IngestionResult:
    run_id: str
    row_counts: dict[str, int]


def ingest_sales_and_customers(
    database: str | Path, sales_csv: str | Path, customers_csv: str | Path
) -> IngestionResult:
    sales_rows = read_dataset(sales_csv, SALES_CONTRACT)
    customer_rows = read_dataset(customers_csv, CUSTOMERS_CONTRACT)

    run_id = uuid.uuid4().hex
    with DuckDBStore(database) as store:
        store.load_datasets(
            [
                (SALES_CONTRACT, sales_rows, Path(sales_csv).name),
                (CUSTOMERS_CONTRACT, customer_rows, Path(customers_csv).name),
            ],
            run_id,
        )
    return IngestionResult(
        run_id,
        {SALES_CONTRACT.name: len(sales_rows), CUSTOMERS_CONTRACT.name: len(customer_rows)},
    )
