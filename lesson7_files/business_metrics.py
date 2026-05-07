"""
business_metrics.py

Pure calculation functions for e-commerce business metrics.
Each function accepts DataFrames and returns scalars, Series, or DataFrames.
No I/O, no plotting.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Revenue metrics
# ---------------------------------------------------------------------------

def calculate_revenue(sales_df: pd.DataFrame) -> float:
    """Return total revenue (sum of item prices) for the given period."""
    return sales_df["price"].sum()


def calculate_revenue_growth(revenue_current: float, revenue_prior: float) -> float | None:
    """
    Return period-over-period revenue growth as a decimal (e.g. 0.15 = 15%).

    Returns None when the prior period has no revenue.
    """
    if revenue_prior is None or revenue_prior == 0:
        return None
    return (revenue_current - revenue_prior) / revenue_prior


def calculate_monthly_revenue(sales_df: pd.DataFrame) -> pd.Series:
    """Return total revenue per month as a Series indexed by month number (1-12)."""
    return sales_df.groupby("month")["price"].sum()


def calculate_monthly_growth(sales_df: pd.DataFrame) -> pd.Series:
    """
    Return month-over-month revenue growth as a Series of pct_change values.

    The first month in the period will be NaN (no prior month to compare).
    Requires at least two months of data for meaningful output.
    """
    return calculate_monthly_revenue(sales_df).pct_change()


def calculate_avg_order_value(sales_df: pd.DataFrame) -> float:
    """Return mean total order value (sum of item prices per order_id, then mean)."""
    return sales_df.groupby("order_id")["price"].sum().mean()


def calculate_total_orders(sales_df: pd.DataFrame) -> int:
    """Return count of unique delivered orders in the period."""
    return sales_df["order_id"].nunique()


# ---------------------------------------------------------------------------
# Product metrics
# ---------------------------------------------------------------------------

def calculate_product_sales(sales_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.Series:
    """
    Aggregate delivered revenue by product category.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales data for the target period (must have product_id, price columns).
    products_df : pd.DataFrame
        Products reference table (must have product_id, product_category_name columns).

    Returns
    -------
    pd.Series
        Total revenue per category, sorted descending, indexed by category name.
    """
    merged = pd.merge(
        products_df[["product_id", "product_category_name"]],
        sales_df[["product_id", "price"]],
        on="product_id",
    )
    return (
        merged.groupby("product_category_name")["price"]
        .sum()
        .sort_values(ascending=False)
    )


# ---------------------------------------------------------------------------
# Geographic metrics
# ---------------------------------------------------------------------------

def calculate_sales_by_state(
    sales_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate delivered revenue by customer state.

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales data for the target period (must have order_id, price columns).
    orders_df : pd.DataFrame
        Full orders table (must have order_id, customer_id columns).
    customers_df : pd.DataFrame
        Customers reference table (must have customer_id, customer_state columns).

    Returns
    -------
    pd.DataFrame
        Columns: customer_state, price. Sorted by price descending.
    """
    sales_customers = pd.merge(
        sales_df[["order_id", "price"]],
        orders_df[["order_id", "customer_id"]],
        on="order_id",
    )
    sales_states = pd.merge(
        sales_customers,
        customers_df[["customer_id", "customer_state"]],
        on="customer_id",
    )
    return (
        sales_states.groupby("customer_state")["price"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


# ---------------------------------------------------------------------------
# Customer experience metrics
# ---------------------------------------------------------------------------

def calculate_delivery_metrics(
    sales_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute per-order delivery speed and attach review scores.

    Adds:
    - delivery_days  : integer days from purchase to customer delivery
    - delivery_bucket: '1-3 days', '4-7 days', or '8+ days'
    - review_score   : from the reviews table (NaN when no review exists)

    Parameters
    ----------
    sales_df : pd.DataFrame
        Sales data for the target period. Must have order_id,
        order_purchase_timestamp, and order_delivered_customer_date columns.
    reviews_df : pd.DataFrame
        Reviews table with order_id and review_score columns.

    Returns
    -------
    pd.DataFrame
        One row per order with columns: order_id, delivery_days,
        delivery_bucket, review_score.
    """
    df = sales_df.copy()
    df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"])
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days

    df = df.merge(reviews_df[["order_id", "review_score"]], on="order_id", how="left")
    order_level = df[["order_id", "delivery_days", "review_score"]].drop_duplicates("order_id")
    order_level = order_level.copy()
    order_level["delivery_bucket"] = order_level["delivery_days"].apply(_bucket_delivery)
    return order_level


def _bucket_delivery(days) -> str:
    """Map a delivery day count to a human-readable speed bucket."""
    if pd.isna(days):
        return "Unknown"
    if days <= 3:
        return "1-3 days"
    if days <= 7:
        return "4-7 days"
    return "8+ days"


def calculate_avg_review_by_delivery(delivery_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return mean review score for each delivery speed bucket.

    Parameters
    ----------
    delivery_df : pd.DataFrame
        Output of calculate_delivery_metrics.

    Returns
    -------
    pd.DataFrame
        Columns: delivery_bucket, review_score (mean).
    """
    return (
        delivery_df.groupby("delivery_bucket")["review_score"]
        .mean()
        .reset_index()
    )


def calculate_review_distribution(delivery_df: pd.DataFrame) -> pd.Series:
    """
    Return the normalized frequency of each review score (1-5).

    Parameters
    ----------
    delivery_df : pd.DataFrame
        Output of calculate_delivery_metrics.

    Returns
    -------
    pd.Series
        Index: review score (int). Values: proportion of orders (float).
    """
    return delivery_df["review_score"].value_counts(normalize=True).sort_index()


def calculate_order_status_distribution(orders_df: pd.DataFrame, year: int) -> pd.Series:
    """
    Return normalized distribution of order statuses for the given year.

    Parameters
    ----------
    orders_df : pd.DataFrame
        Full orders table with order_purchase_timestamp and order_status columns.
    year : int
        Calendar year to filter on.

    Returns
    -------
    pd.Series
        Index: order_status (str). Values: proportion of orders (float).
    """
    orders = orders_df.copy()
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    orders["year"] = orders["order_purchase_timestamp"].dt.year
    return orders[orders["year"] == year]["order_status"].value_counts(normalize=True)
