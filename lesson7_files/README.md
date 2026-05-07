# E-Commerce Sales Analysis

Exploratory data analysis of e-commerce transactions covering revenue trends, product performance, geographic distribution, and customer experience metrics.

## Project Structure

```
lesson7_files/
├── EDA_Refactored.ipynb   # Main analysis notebook
├── data_loader.py         # Data loading and transformation utilities
├── business_metrics.py    # Business metric calculation functions
├── requirements.txt       # Python dependencies
└── ecommerce_data/        # Raw CSV datasets
    ├── orders_dataset.csv
    ├── order_items_dataset.csv
    ├── products_dataset.csv
    ├── customers_dataset.csv
    ├── order_reviews_dataset.csv
    └── order_payments_dataset.csv
```

## Setup

```bash
pip install -r requirements.txt
```

### Jupyter Notebook

```bash
jupyter notebook EDA_Refactored.ipynb
```

### Streamlit Dashboard

```bash
streamlit run dashboard.py
```

Open the URL printed in the terminal (default: http://localhost:8501).
Use the **Analysis Year** selector in the top-right corner to switch periods.
All charts and KPI cards update automatically.

## Configuring the Analysis Period

Open `EDA_Refactored.ipynb` and edit the **Configuration** cell near the top:

```python
ANALYSIS_YEAR   = 2023   # Year to analyze
COMPARISON_YEAR = 2022   # Baseline year for year-over-year comparisons
ANALYSIS_MONTH  = None   # Set to 1-12 for a single month, or None for a full year
```

Re-run all cells (Kernel > Restart & Run All) to regenerate results for the new period.

**Examples**

| Goal | Settings |
|------|----------|
| Full-year 2023 vs 2022 | `ANALYSIS_YEAR=2023`, `ANALYSIS_MONTH=None` |
| Q1 2023 (month-by-month) | Run once per month: `ANALYSIS_MONTH=1`, then `2`, then `3` |
| Single month, e.g. July 2023 | `ANALYSIS_YEAR=2023`, `ANALYSIS_MONTH=7` |

## Module Reference

### data_loader.py

| Function | Description |
|----------|-------------|
| `load_data(data_dir)` | Reads all six CSV files; returns a tuple of DataFrames |
| `build_sales_data(orders, order_items)` | Joins and cleans data; returns delivered orders with year/month columns |
| `filter_by_period(df, year, month)` | Filters a sales DataFrame to the specified year (and optional month) |

### business_metrics.py

| Function | Description |
|----------|-------------|
| `calculate_revenue(sales_df)` | Total revenue for the period |
| `calculate_revenue_growth(current, prior)` | Period-over-period growth rate |
| `calculate_monthly_revenue(sales_df)` | Revenue per month |
| `calculate_monthly_growth(sales_df)` | Month-over-month growth rates |
| `calculate_avg_order_value(sales_df)` | Mean total spend per order |
| `calculate_total_orders(sales_df)` | Count of unique delivered orders |
| `calculate_product_sales(sales_df, products_df)` | Revenue by product category |
| `calculate_sales_by_state(sales_df, orders_df, customers_df)` | Revenue by US state |
| `calculate_delivery_metrics(sales_df, reviews_df)` | Delivery days and review scores per order |
| `calculate_avg_review_by_delivery(delivery_df)` | Mean review score by delivery speed bucket |
| `calculate_review_distribution(delivery_df)` | Normalized review score frequency |
| `calculate_order_status_distribution(orders_df, year)` | Order status breakdown |
