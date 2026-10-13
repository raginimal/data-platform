"""Versioned dataset contracts for ingested inputs (DATA-CON-001, DATA-CON-002)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ColumnType(str, Enum):
    INTEGER = "INTEGER"
    VARCHAR = "VARCHAR"
    DECIMAL = "DECIMAL(10,2)"
    DATE = "DATE"


@dataclass(frozen=True)
class Column:
    name: str
    type: ColumnType
    nullable: bool = False


@dataclass(frozen=True)
class DatasetContract:
    name: str
    version: str
    owner: str
    classification: str
    columns: tuple[Column, ...]
    primary_key: str

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.columns)


SALES_CONTRACT = DatasetContract(
    name="sales",
    version="1.0.0",
    owner="data-platform-team",
    classification="internal",
    columns=(
        Column("order_id", ColumnType.INTEGER),
        Column("customer_id", ColumnType.INTEGER),
        Column("product", ColumnType.VARCHAR),
        Column("quantity", ColumnType.INTEGER),
        Column("unit_price", ColumnType.DECIMAL),
        Column("order_date", ColumnType.DATE),
    ),
    primary_key="order_id",
)

CUSTOMERS_CONTRACT = DatasetContract(
    name="customers",
    version="1.0.0",
    owner="data-platform-team",
    classification="internal",
    columns=(
        Column("customer_id", ColumnType.INTEGER),
        Column("name", ColumnType.VARCHAR),
        Column("email", ColumnType.VARCHAR),
        Column("region", ColumnType.VARCHAR),
        Column("signup_date", ColumnType.DATE),
    ),
    primary_key="customer_id",
)
