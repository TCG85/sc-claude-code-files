"""
data_loader.py

Handles loading, parsing, and cleaning of the e-commerce datasets.
All functions return plain DataFrames; no business logic lives here.
"""

import os
import pandas as pd


DATA_DIR = "ecommerce_data"

_ORDER_TIMESTAMP_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def load_data(data_dir: str = DATA_DIR) -> tuple:
    """
    Load all six e-commerce CSV files from data_dir.

    Parameters
    ----------
    data_dir : str
        Path to the directory containing the CSV files.

    Returns
    -------
    tuple
        (orders, order_items, products, customers, reviews, order_payments)
        Each element is a pd.DataFrame.
    """
    def _read(name):
        return pd.read_csv(os.path.join(data_dir, name))

    orders = _read("orders_dataset.csv")
    order_items = _read("order_items_dataset.csv")
    products = _read("products_dataset.csv")
    customers = _read("customers_dataset.csv")
    reviews = _read("order_reviews_dataset.csv")
    order_payments = _read("order_payments_dataset.csv")

    return orders, order_items, products, customers, reviews, order_payments


def _parse_order_timestamps(orders: pd.DataFrame) -> pd.DataFrame:
    """Convert all timestamp columns in orders to datetime."""
    orders = orders.copy()
    for col in _ORDER_TIMESTAMP_COLS:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col])
    return orders


def build_sales_data(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    """
    Join order items with orders and return a clean sales DataFrame.

    Only delivered orders are retained. Adds integer year and month columns
    derived from order_purchase_timestamp.

    Parameters
    ----------
    orders : pd.DataFrame
        Raw orders dataset.
    order_items : pd.DataFrame
        Raw order items dataset.

    Returns
    -------
    pd.DataFrame
        One row per order item (delivered orders only), with columns:
        order_id, order_item_id, product_id, price, freight_value,
        order_status, order_purchase_timestamp, order_delivered_customer_date,
        customer_id, year, month.
    """
    orders = _parse_order_timestamps(orders)

    item_cols = ["order_id", "order_item_id", "product_id", "price", "freight_value"]
    order_cols = [
        "order_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "customer_id",
    ]

    sales = pd.merge(
        order_items[item_cols],
        orders[order_cols],
        on="order_id",
    )

    sales = sales[sales["order_status"] == "delivered"].copy()
    sales["year"] = sales["order_purchase_timestamp"].dt.year
    sales["month"] = sales["order_purchase_timestamp"].dt.month

    return sales


def filter_by_period(df: pd.DataFrame, year: int, month: int = None) -> pd.DataFrame:
    """
    Return rows matching the specified year and optionally a specific month.

    Parameters
    ----------
    df : pd.DataFrame
        Sales DataFrame produced by build_sales_data (must have year, month columns).
    year : int
        Calendar year to select.
    month : int or None
        If provided, restricts results to this month (1-12).
        If None, the entire year is returned.

    Returns
    -------
    pd.DataFrame
        Filtered copy of df.
    """
    result = df[df["year"] == year]
    if month is not None:
        result = result[result["month"] == month]
    return result.copy()
