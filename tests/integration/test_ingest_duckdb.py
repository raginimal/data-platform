from pathlib import Path

import duckdb
import pytest

from ai_data_platform.application.ingest import ingest_sales_and_customers
from ai_data_platform.cli.main import main
from ai_data_platform.domain.errors import SchemaValidationError

SEEDS = Path(__file__).resolve().parents[2] / "data" / "seeds"
SALES = SEEDS / "sales.csv"
CUSTOMERS = SEEDS / "customers.csv"


def rows(db, sql):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_ingest_seed_files(tmp_path):
    db = tmp_path / "t.duckdb"
    result = ingest_sales_and_customers(db, SALES, CUSTOMERS)
    assert result.row_counts == {"sales": 5, "customers": 4}
    assert rows(db, "SELECT count(*) FROM raw.sales") == [(5,)]
    assert rows(db, "SELECT count(*) FROM raw.customers") == [(4,)]
    assert rows(db, "SELECT dataset, row_count FROM raw.ingestion_runs ORDER BY dataset") == [
        ("customers", 4),
        ("sales", 5),
    ]
    assert rows(db, "SELECT typeof(unit_price), typeof(order_date) FROM raw.sales LIMIT 1") == [
        ("DECIMAL(10,2)", "DATE")
    ]


def test_reingest_replaces_rather_than_duplicates(tmp_path):
    db = tmp_path / "t.duckdb"
    ingest_sales_and_customers(db, SALES, CUSTOMERS)
    ingest_sales_and_customers(db, SALES, CUSTOMERS)
    assert rows(db, "SELECT count(*) FROM raw.sales") == [(5,)]


def test_invalid_input_leaves_database_untouched(tmp_path):
    db = tmp_path / "t.duckdb"
    ingest_sales_and_customers(db, SALES, CUSTOMERS)
    bad = tmp_path / "customers.csv"
    bad.write_text("customer_id,name\n1,A\n", encoding="utf-8")
    with pytest.raises(SchemaValidationError):
        ingest_sales_and_customers(db, SALES, bad)
    assert rows(db, "SELECT count(*) FROM raw.customers") == [(4,)]
    assert rows(db, "SELECT count(*) FROM raw.ingestion_runs") == [(2,)]


def test_invalid_input_does_not_create_database(tmp_path):
    db = tmp_path / "t.duckdb"
    with pytest.raises(SchemaValidationError):
        ingest_sales_and_customers(db, _bad_sales(tmp_path), CUSTOMERS)
    assert not db.exists()


def _bad_sales(tmp_path):
    bad = tmp_path / "sales.csv"
    bad.write_text(
        "order_id,customer_id,product,quantity,unit_price,order_date\n1,1,W,x,1.00,2026-01-01\n",
        encoding="utf-8",
    )
    return bad


def test_cli_success_and_failure(tmp_path, capsys):
    db = str(tmp_path / "cli.duckdb")
    assert main(["ingest", "--sales", str(SALES), "--customers", str(CUSTOMERS), "--database", db]) == 0
    assert "succeeded" in capsys.readouterr().out
    code = main(["ingest", "--sales", str(_bad_sales(tmp_path)), "--customers", str(CUSTOMERS), "--database", db])
    assert code == 1
    assert "ERROR" in capsys.readouterr().err
