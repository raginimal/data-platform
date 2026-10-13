from datetime import date
from decimal import Decimal

import pytest

from ai_data_platform.domain.contracts import CUSTOMERS_CONTRACT, SALES_CONTRACT
from ai_data_platform.domain.errors import SchemaValidationError, SourceFileError
from ai_data_platform.domain.validation import read_dataset

SALES_HEADER = "order_id,customer_id,product,quantity,unit_price,order_date\n"


def write(tmp_path, text, name="sales.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_sales_rows_are_typed(tmp_path):
    path = write(tmp_path, SALES_HEADER + "1,2,Widget,3,9.99,2026-01-05\n")
    assert read_dataset(path, SALES_CONTRACT) == [
        (1, 2, "Widget", 3, Decimal("9.99"), date(2026, 1, 5))
    ]


def test_valid_customers(tmp_path):
    path = write(
        tmp_path,
        "customer_id,name,email,region,signup_date\n1,A,a@example.com,EMEA,2025-01-01\n",
        "customers.csv",
    )
    assert len(read_dataset(path, CUSTOMERS_CONTRACT)) == 1


def test_missing_file(tmp_path):
    with pytest.raises(SourceFileError, match="not found"):
        read_dataset(tmp_path / "nope.csv", SALES_CONTRACT)


def test_wrong_extension(tmp_path):
    with pytest.raises(SourceFileError, match="Unsupported"):
        read_dataset(write(tmp_path, "x", "sales.txt"), SALES_CONTRACT)


def test_empty_file(tmp_path):
    with pytest.raises(SchemaValidationError, match="empty"):
        read_dataset(write(tmp_path, ""), SALES_CONTRACT)


def test_header_only_has_no_data(tmp_path):
    with pytest.raises(SchemaValidationError, match="no data rows"):
        read_dataset(write(tmp_path, SALES_HEADER), SALES_CONTRACT)


def test_missing_and_extra_columns(tmp_path):
    path = write(tmp_path, "order_id,customer_id,product,quantity,extra,order_date\n")
    with pytest.raises(SchemaValidationError) as info:
        read_dataset(path, SALES_CONTRACT)
    assert any("missing columns" in i and "unit_price" in i for i in info.value.issues)
    assert any("unexpected columns" in i and "extra" in i for i in info.value.issues)


def test_bad_types_report_line_and_column(tmp_path):
    path = write(
        tmp_path,
        SALES_HEADER + "1,2,Widget,abc,9.99,2026-01-05\n2,2,Widget,1,9.99,2026-13-45\n",
    )
    with pytest.raises(SchemaValidationError) as info:
        read_dataset(path, SALES_CONTRACT)
    assert any("line 2" in i and "quantity" in i for i in info.value.issues)
    assert any("line 3" in i and "order_date" in i for i in info.value.issues)


def test_required_value_missing(tmp_path):
    path = write(tmp_path, SALES_HEADER + "1,2,,3,9.99,2026-01-05\n")
    with pytest.raises(SchemaValidationError, match="'product' is required"):
        read_dataset(path, SALES_CONTRACT)


def test_wrong_field_count(tmp_path):
    path = write(tmp_path, SALES_HEADER + "1,2,Widget\n")
    with pytest.raises(SchemaValidationError, match="expected 6 fields"):
        read_dataset(path, SALES_CONTRACT)


def test_duplicate_primary_key(tmp_path):
    row = "1,2,Widget,3,9.99,2026-01-05\n"
    with pytest.raises(SchemaValidationError, match="duplicate order_id"):
        read_dataset(write(tmp_path, SALES_HEADER + row + row), SALES_CONTRACT)


def test_price_with_too_many_decimals_rejected(tmp_path):
    path = write(tmp_path, SALES_HEADER + "1,2,Widget,3,9.999,2026-01-05\n")
    with pytest.raises(SchemaValidationError, match="unit_price"):
        read_dataset(path, SALES_CONTRACT)


def test_non_utf8_file(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(SourceFileError, match="UTF-8"):
        read_dataset(path, SALES_CONTRACT)
