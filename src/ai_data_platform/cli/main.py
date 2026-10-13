"""Command-line interface: python -m ai_data_platform.cli.main ingest ..."""

from __future__ import annotations

import argparse
import sys

from ..application.ingest import ingest_sales_and_customers
from ..domain.errors import IngestionError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-data-platform")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Load sales and customer CSV files into DuckDB")
    ingest.add_argument("--sales", default="data/seeds/sales.csv")
    ingest.add_argument("--customers", default="data/seeds/customers.csv")
    ingest.add_argument("--database", default="data/platform.duckdb")
    args = parser.parse_args(argv)

    try:
        result = ingest_sales_and_customers(args.database, args.sales, args.customers)
    except IngestionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    counts = ", ".join(f"{k}={v}" for k, v in result.row_counts.items())
    print(f"Ingestion run {result.run_id} succeeded: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
