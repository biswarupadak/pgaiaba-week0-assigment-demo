"""Read-only access to the Kartify orders database (SQLite)."""

import re
import sqlite3
from pathlib import Path

import pandas as pd

from .config import settings

ORDER_ID_PATTERN = re.compile(r"^O\d+$")


def is_valid_order_id(order_id: str) -> bool:
    return bool(ORDER_ID_PATTERN.match(order_id.strip()))


def _connect(db_path: Path | None) -> sqlite3.Connection:
    # Open read-only: the agent must never modify order records.
    path = Path(db_path or settings.db_path).resolve()
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def get_order(order_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """Return all columns for a single order (empty DataFrame if not found)."""
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM orders WHERE order_id = ?", conn, params=(order_id.strip(),)
        )


def get_customer_orders(cust_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """Return order_id and product_description for every order of a customer."""
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT order_id, product_description FROM orders WHERE customer_id = ?",
            conn,
            params=(cust_id.strip(),),
        )


def order_belongs_to_customer(order_id: str, cust_id: str,
                              db_path: Path | None = None) -> bool:
    orders = get_customer_orders(cust_id, db_path)
    return order_id.strip() in set(orders["order_id"])
