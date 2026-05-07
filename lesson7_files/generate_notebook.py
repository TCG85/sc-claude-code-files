"""Generates EDA_Refactored.ipynb."""
import json, uuid, pathlib

def _id():
    return uuid.uuid4().hex[:12]

def md(lines):
    return {"cell_type": "markdown", "id": _id(), "metadata": {}, "source": lines}

def code(lines):
    return {"cell_type": "code", "execution_count": None, "id": _id(),
            "metadata": {}, "outputs": [], "source": lines}

cells = []

# ── Title ──────────────────────────────────────────────────────────────────
cells.append(md([
    "# E-Commerce Sales Analysis\n",
    "\n",
    "This notebook analyzes e-commerce transaction data to evaluate business performance across four dimensions:\n",
    "revenue trends, product category performance, geographic distribution, and customer experience.\n",
    "\n",
    "The analysis compares a configurable primary period against a prior-year baseline.\n",
    "All parameters are set in the **Configuration** section below.",
]))

# ── Table of Contents ───────────────────────────────────────────────────────
cells.append(md([
    "## Table of Contents\n",
    "\n",
    "1. [Introduction and Business Objectives](#1-introduction-and-business-objectives)\n",
    "2. [Data Dictionary](#2-data-dictionary)\n",
    "3. [Configuration](#3-configuration)\n",
    "4. [Data Loading](#4-data-loading)\n",
    "5. [Data Preparation and Transformation](#5-data-preparation-and-transformation)\n",
    "6. [Business Metrics](#6-business-metrics)\n",
    "   - 6.1 [Revenue Analysis](#61-revenue-analysis)\n",
    "   - 6.2 [Product Category Analysis](#62-product-category-analysis)\n",
    "   - 6.3 [Geographic Analysis](#63-geographic-analysis)\n",
    "   - 6.4 [Customer Experience Analysis](#64-customer-experience-analysis)\n",
    "7. [Summary of Observations](#7-summary-of-observations)",
]))

# ── 1. Introduction ─────────────────────────────────────────────────────────
cells.append(md([
    "## 1. Introduction and Business Objectives\n",
    "\n",
    "The dataset covers e-commerce orders placed on a US marketplace. Six tables are available:\n",
    "orders, order items, products, customers, reviews, and payments.\n",
    "\n",
    "Key questions this analysis addresses:\n",
    "\n",
    "- How did total revenue and order volume change year-over-year?\n",
    "- What is the month-over-month revenue growth trend within the analysis period?\n",
    "- Which product categories generate the most revenue?\n",
    "- Which US states produce the highest sales volume?\n",
    "- How does delivery speed correlate with customer review scores?\n",
    "- What share of orders reach delivered status versus other outcomes?",
]))

# ── 2. Data Dictionary ──────────────────────────────────────────────────────
cells.append(md([
    "## 2. Data Dictionary\n",
    "\n",
    "### Orders (`orders_dataset.csv`)\n",
    "\n",
    "| Column | Description |\n",
    "|--------|-------------|\n",
    "| order_id | Unique order identifier |\n",
    "| customer_id | Customer identifier (links to customers table) |\n",
    "| order_status | Order lifecycle state: delivered, canceled, shipped, etc. |\n",
    "| order_purchase_timestamp | Date and time the order was placed |\n",
    "| order_approved_at | Date and time payment was approved |\n",
    "| order_delivered_carrier_date | Date the order was handed to the carrier |\n",
    "| order_delivered_customer_date | Date the order was delivered to the customer |\n",
    "| order_estimated_delivery_date | Seller-estimated delivery date |\n",
    "\n",
    "### Order Items (`order_items_dataset.csv`)\n",
    "\n",
    "| Column | Description |\n",
    "|--------|-------------|\n",
    "| order_id | Order identifier (foreign key) |\n",
    "| order_item_id | Item sequence number within the order |\n",
    "| product_id | Product identifier (foreign key) |\n",
    "| seller_id | Seller identifier |\n",
    "| price | Item price in USD |\n",
    "| freight_value | Shipping cost in USD |\n",
    "\n",
    "### Products (`products_dataset.csv`)\n",
    "\n",
    "| Column | Description |\n",
    "|--------|-------------|\n",
    "| product_id | Unique product identifier |\n",
    "| product_category_name | Category the product belongs to |\n",
    "\n",
    "### Customers (`customers_dataset.csv`)\n",
    "\n",
    "| Column | Description |\n",
    "|--------|-------------|\n",
    "| customer_id | Order-level customer identifier |\n",
    "| customer_unique_id | Unique customer identifier across multiple orders |\n",
    "| customer_state | Two-letter US state abbreviation |\n",
    "| customer_city | Customer city name |\n",
    "\n",
    "### Order Reviews (`order_reviews_dataset.csv`)\n",
    "\n",
    "| Column | Description |\n",
    "|--------|-------------|\n",
    "| review_id | Unique review identifier |\n",
    "| order_id | Order being reviewed (foreign key) |\n",
    "| review_score | Rating from 1 (lowest) to 5 (highest) |\n",
    "| review_comment_title | Short review title |\n",
    "| review_comment_message | Full review text |\n",
    "\n",
    "### Business Terms\n",
    "\n",
    "| Term | Definition |\n",
    "|------|------------|\n",
    "| Revenue | Sum of item prices for delivered orders |\n",
    "| Average Order Value (AOV) | Mean total price per unique order |\n",
    "| YoY Growth | Year-over-year percentage change |\n",
    "| MoM Growth | Month-over-month percentage change |\n",
    "| Delivery Days | Days from order purchase to customer delivery |",
]))

# ── 3. Configuration ────────────────────────────────────────────────────────
cells.append(md([
    "## 3. Configuration\n",
    "\n",
    "Set the analysis period below. Re-run all cells after changing any value.\n",
    "\n",
    "- `ANALYSIS_MONTH = None` analyzes the full year.\n",
    "- Set `ANALYSIS_MONTH` to an integer (1-12) to restrict to a single calendar month.",
]))

cells.append(code([
    "# Analysis period\n",
    "ANALYSIS_YEAR   = 2023   # Primary year to analyze\n",
    "COMPARISON_YEAR = 2022   # Baseline year for year-over-year comparisons\n",
    "ANALYSIS_MONTH  = None   # Integer 1-12 for a single month, or None for a full year\n",
    "\n",
    "DATA_DIR = 'ecommerce_data'",
]))

# ── 4. Data Loading ─────────────────────────────────────────────────────────
cells.append(md([
    "## 4. Data Loading\n",
    "\n",
    "All six datasets are loaded from the configured data directory.\n",
    "Row counts are printed for a quick sanity check.",
]))

cells.append(code([
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import matplotlib.ticker as mticker\n",
    "import plotly.express as px\n",
    "\n",
    "from data_loader import load_data, build_sales_data, filter_by_period\n",
    "from business_metrics import (\n",
    "    calculate_revenue,\n",
    "    calculate_revenue_growth,\n",
    "    calculate_monthly_revenue,\n",
    "    calculate_monthly_growth,\n",
    "    calculate_avg_order_value,\n",
    "    calculate_total_orders,\n",
    "    calculate_product_sales,\n",
    "    calculate_sales_by_state,\n",
    "    calculate_delivery_metrics,\n",
    "    calculate_avg_review_by_delivery,\n",
    "    calculate_review_distribution,\n",
    "    calculate_order_status_distribution,\n",
    ")\n",
    "\n",
    "orders, order_items, products, customers, reviews, order_payments = load_data(DATA_DIR)\n",
    "\n",
    "print(f'Orders:       {len(orders):>8,} rows')\n",
    "print(f'Order items:  {len(order_items):>8,} rows')\n",
    "print(f'Products:     {len(products):>8,} rows')\n",
    "print(f'Customers:    {len(customers):>8,} rows')\n",
    "print(f'Reviews:      {len(reviews):>8,} rows')\n",
    "print(f'Payments:     {len(order_payments):>8,} rows')",
]))

# ── 5. Data Preparation ─────────────────────────────────────────────────────
cells.append(md([
    "## 5. Data Preparation and Transformation\n",
    "\n",
    "Order items are joined with orders and filtered to delivered orders only.\n",
    "Timestamps are parsed and year/month columns are added to support period filtering.\n",
    "The resulting `sales_delivered` DataFrame is then split into the analysis and comparison periods.",
]))

cells.append(code([
    "# Build unified sales dataset (delivered orders only)\n",
    "sales_delivered = build_sales_data(orders, order_items)\n",
    "\n",
    "# Filter to the configured periods\n",
    "sales_current = filter_by_period(sales_delivered, ANALYSIS_YEAR, ANALYSIS_MONTH)\n",
    "sales_prior   = filter_by_period(sales_delivered, COMPARISON_YEAR, ANALYSIS_MONTH)\n",
    "\n",
    "# Human-readable labels used throughout the notebook\n",
    "if ANALYSIS_MONTH:\n",
    "    period_label = f'{ANALYSIS_YEAR}-{ANALYSIS_MONTH:02d}'\n",
    "    prior_label  = f'{COMPARISON_YEAR}-{ANALYSIS_MONTH:02d}'\n",
    "else:\n",
    "    period_label = str(ANALYSIS_YEAR)\n",
    "    prior_label  = str(COMPARISON_YEAR)\n",
    "\n",
    "print(f'Analysis period  : {period_label}  '\n",
    "      f'({sales_current[\"order_id\"].nunique():,} orders, '\n",
    "      f'{len(sales_current):,} line items)')\n",
    "print(f'Comparison period: {prior_label}  '\n",
    "      f'({sales_prior[\"order_id\"].nunique():,} orders, '\n",
    "      f'{len(sales_prior):,} line items)')",
]))

# ── 6. Business Metrics header ───────────────────────────────────────────────
cells.append(md(["## 6. Business Metrics"]))

# ── 6.1 Revenue Analysis ────────────────────────────────────────────────────
cells.append(md([
    "### 6.1 Revenue Analysis\n",
    "\n",
    "Total revenue, order volume, and average order value for the analysis period,\n",
    "each compared against the prior-year baseline.",
]))

cells.append(code([
    "revenue_current = calculate_revenue(sales_current)\n",
    "revenue_prior   = calculate_revenue(sales_prior)\n",
    "revenue_growth  = calculate_revenue_growth(revenue_current, revenue_prior)\n",
    "\n",
    "orders_current = calculate_total_orders(sales_current)\n",
    "orders_prior   = calculate_total_orders(sales_prior)\n",
    "orders_growth  = calculate_revenue_growth(orders_current, orders_prior)\n",
    "\n",
    "aov_current = calculate_avg_order_value(sales_current)\n",
    "aov_prior   = calculate_avg_order_value(sales_prior)\n",
    "aov_growth  = calculate_revenue_growth(aov_current, aov_prior)\n",
    "\n",
    "def fmt_growth(g):\n",
    "    return f'{g * 100:+.1f}%' if g is not None else 'N/A'\n",
    "\n",
    "print(f'Revenue ({period_label}):          ${revenue_current:>12,.2f}')\n",
    "print(f'Revenue ({prior_label}):          ${revenue_prior:>12,.2f}')\n",
    "print(f'Revenue YoY growth:               {fmt_growth(revenue_growth):>8}')\n",
    "print()\n",
    "print(f'Total orders ({period_label}):    {orders_current:>12,}')\n",
    "print(f'Total orders ({prior_label}):    {orders_prior:>12,}')\n",
    "print(f'Orders YoY growth:                {fmt_growth(orders_growth):>8}')\n",
    "print()\n",
    "print(f'Avg order value ({period_label}):  ${aov_current:>11,.2f}')\n",
    "print(f'Avg order value ({prior_label}):  ${aov_prior:>11,.2f}')\n",
    "print(f'AOV YoY growth:                   {fmt_growth(aov_growth):>8}')",
]))

# Monthly revenue chart
cells.append(md([
    "#### Monthly Revenue Trend\n",
    "\n",
    "Total revenue per calendar month for the analysis period.",
]))

cells.append(code([
    "PALETTE = {\n",
    "    'primary':   '#2C5F8A',\n",
    "    'secondary': '#4A90D9',\n",
    "    'positive':  '#2C7A4B',\n",
    "    'negative':  '#C0392B',\n",
    "    'light':     '#A8C8E8',\n",
    "    'grid':      '#E8EDF2',\n",
    "}\n",
    "\n",
    "monthly_rev = calculate_monthly_revenue(sales_current)\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(10, 5))\n",
    "ax.bar(monthly_rev.index, monthly_rev.values, color=PALETTE['primary'], width=0.6)\n",
    "ax.set_title(f'Monthly Revenue ({period_label})', fontsize=14, fontweight='bold', pad=12)\n",
    "ax.set_xlabel('Month', fontsize=11)\n",
    "ax.set_ylabel('Revenue (USD)', fontsize=11)\n",
    "ax.set_xticks(monthly_rev.index)\n",
    "ax.set_xticklabels(\n",
    "    [pd.Timestamp(2020, m, 1).strftime('%b') for m in monthly_rev.index]\n",
    ")\n",
    "ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))\n",
    "ax.set_facecolor(PALETTE['grid'])\n",
    "ax.grid(axis='y', color='white', linewidth=0.8)\n",
    "ax.spines[['top', 'right']].set_visible(False)\n",
    "plt.tight_layout()\n",
    "plt.show()",
]))

# MoM growth chart
cells.append(md([
    "#### Month-over-Month Revenue Growth\n",
    "\n",
    "Percentage change in revenue from one month to the next within the analysis period.\n",
    "This chart is only shown when a full year is selected (ANALYSIS_MONTH = None).",
]))

cells.append(code([
    "if ANALYSIS_MONTH is None:\n",
    "    monthly_growth = calculate_monthly_growth(sales_current).dropna()\n",
    "\n",
    "    colors = [\n",
    "        PALETTE['positive'] if v >= 0 else PALETTE['negative']\n",
    "        for v in monthly_growth.values\n",
    "    ]\n",
    "\n",
    "    fig, ax = plt.subplots(figsize=(10, 4))\n",
    "    ax.bar(monthly_growth.index, monthly_growth.values * 100, color=colors, width=0.6)\n",
    "    ax.axhline(0, color='black', linewidth=0.8)\n",
    "    ax.set_title(\n",
    "        f'Month-over-Month Revenue Growth ({period_label})',\n",
    "        fontsize=14, fontweight='bold', pad=12\n",
    "    )\n",
    "    ax.set_xlabel('Month', fontsize=11)\n",
    "    ax.set_ylabel('Growth (%)', fontsize=11)\n",
    "    ax.set_xticks(monthly_growth.index)\n",
    "    ax.set_xticklabels(\n",
    "        [pd.Timestamp(2020, m, 1).strftime('%b') for m in monthly_growth.index]\n",
    "    )\n",
    "    ax.yaxis.set_major_formatter(\n",
    "        mticker.FuncFormatter(lambda x, _: f'{x:+.1f}%')\n",
    "    )\n",
    "    ax.set_facecolor(PALETTE['grid'])\n",
    "    ax.grid(axis='y', color='white', linewidth=0.8)\n",
    "    ax.spines[['top', 'right']].set_visible(False)\n",
    "    plt.tight_layout()\n",
    "    plt.show()\n",
    "\n",
    "    mean_growth = monthly_growth.mean()\n",
    "    print(f'Mean month-over-month growth ({period_label}): {mean_growth * 100:+.1f}%')\n",
    "else:\n",
    "    print('Month-over-month growth requires a full-year selection (set ANALYSIS_MONTH = None).')",
]))

# ── 6.2 Product Category ────────────────────────────────────────────────────
cells.append(md([
    "### 6.2 Product Category Analysis\n",
    "\n",
    "Revenue breakdown by product category for the analysis period,\n",
    "highlighting which categories drive the most value.",
]))

cells.append(code([
    "product_sales = calculate_product_sales(sales_current, products)\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(12, 5))\n",
    "ax.bar(product_sales.index, product_sales.values, color=PALETTE['secondary'], width=0.7)\n",
    "ax.set_title(\n",
    "    f'Revenue by Product Category ({period_label})',\n",
    "    fontsize=14, fontweight='bold', pad=12\n",
    ")\n",
    "ax.set_xlabel('Product Category', fontsize=11)\n",
    "ax.set_ylabel('Revenue (USD)', fontsize=11)\n",
    "ax.set_xticklabels(product_sales.index, rotation=45, ha='right', fontsize=9)\n",
    "ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))\n",
    "ax.set_facecolor(PALETTE['grid'])\n",
    "ax.grid(axis='y', color='white', linewidth=0.8)\n",
    "ax.spines[['top', 'right']].set_visible(False)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "total_product_rev = product_sales.sum()\n",
    "print(f'\\nTop 5 categories by revenue ({period_label}):')\n",
    "for cat, rev in product_sales.head(5).items():\n",
    "    share = rev / total_product_rev * 100\n",
    "    print(f'  {cat:<35} ${rev:>10,.2f}  ({share:.1f}%)')",
]))

# ── 6.3 Geographic ──────────────────────────────────────────────────────────
cells.append(md([
    "### 6.3 Geographic Analysis\n",
    "\n",
    "Revenue distribution across US states, shown as a choropleth map and a ranked table.",
]))

cells.append(code([
    "sales_by_state = calculate_sales_by_state(sales_current, orders, customers)\n",
    "\n",
    "fig = px.choropleth(\n",
    "    sales_by_state,\n",
    "    locations='customer_state',\n",
    "    color='price',\n",
    "    locationmode='USA-states',\n",
    "    scope='usa',\n",
    "    title=f'Revenue by State ({period_label})',\n",
    "    color_continuous_scale='Blues',\n",
    "    labels={'price': 'Revenue (USD)', 'customer_state': 'State'},\n",
    ")\n",
    "fig.update_layout(\n",
    "    title_font_size=16,\n",
    "    coloraxis_colorbar=dict(title='Revenue (USD)', tickformat='$,.0f'),\n",
    ")\n",
    "fig.show()\n",
    "\n",
    "total_state_rev = sales_by_state['price'].sum()\n",
    "print(f'\\nTop 10 states by revenue ({period_label}):')\n",
    "for _, row in sales_by_state.head(10).iterrows():\n",
    "    share = row['price'] / total_state_rev * 100\n",
    "    print(f'  {row[\"customer_state\"]:<6} ${row[\"price\"]:>12,.2f}  ({share:.1f}%)')",
]))

# ── 6.4 Customer Experience ─────────────────────────────────────────────────
cells.append(md([
    "### 6.4 Customer Experience Analysis\n",
    "\n",
    "Delivery performance and customer satisfaction metrics.\n",
    "Delivery speed is grouped into three buckets: 1-3 days, 4-7 days, and 8+ days.",
]))

cells.append(code([
    "delivery_df = calculate_delivery_metrics(sales_current, reviews)\n",
    "\n",
    "avg_delivery = delivery_df['delivery_days'].mean()\n",
    "avg_review   = delivery_df['review_score'].mean()\n",
    "\n",
    "print(f'Average delivery time ({period_label}): {avg_delivery:.1f} days')\n",
    "print(f'Average review score  ({period_label}): {avg_review:.2f} / 5.0')",
]))

cells.append(md([
    "#### Review Score Distribution\n",
    "\n",
    "Proportion of orders receiving each review score (1 = lowest, 5 = highest).",
]))

cells.append(code([
    "review_dist = calculate_review_distribution(delivery_df)\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(8, 4))\n",
    "ax.barh(\n",
    "    review_dist.index.astype(str),\n",
    "    review_dist.values * 100,\n",
    "    color=PALETTE['primary'],\n",
    "    height=0.55,\n",
    ")\n",
    "ax.set_title(\n",
    "    f'Review Score Distribution ({period_label})',\n",
    "    fontsize=14, fontweight='bold', pad=12\n",
    ")\n",
    "ax.set_xlabel('Share of Orders (%)', fontsize=11)\n",
    "ax.set_ylabel('Review Score', fontsize=11)\n",
    "ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))\n",
    "ax.set_facecolor(PALETTE['grid'])\n",
    "ax.grid(axis='x', color='white', linewidth=0.8)\n",
    "ax.spines[['top', 'right']].set_visible(False)\n",
    "plt.tight_layout()\n",
    "plt.show()",
]))

cells.append(md([
    "#### Average Review Score by Delivery Speed\n",
    "\n",
    "Mean customer rating for each delivery speed bucket.",
]))

cells.append(code([
    "bucket_order = ['1-3 days', '4-7 days', '8+ days']\n",
    "review_by_delivery = calculate_avg_review_by_delivery(delivery_df)\n",
    "review_by_delivery['delivery_bucket'] = pd.Categorical(\n",
    "    review_by_delivery['delivery_bucket'], categories=bucket_order, ordered=True\n",
    ")\n",
    "review_by_delivery = review_by_delivery.sort_values('delivery_bucket')\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(8, 4))\n",
    "ax.bar(\n",
    "    review_by_delivery['delivery_bucket'],\n",
    "    review_by_delivery['review_score'],\n",
    "    color=PALETTE['secondary'],\n",
    "    width=0.45,\n",
    ")\n",
    "ax.set_title(\n",
    "    f'Average Review Score by Delivery Speed ({period_label})',\n",
    "    fontsize=14, fontweight='bold', pad=12\n",
    ")\n",
    "ax.set_xlabel('Delivery Time', fontsize=11)\n",
    "ax.set_ylabel('Average Review Score', fontsize=11)\n",
    "ax.set_ylim(0, 5)\n",
    "ax.set_facecolor(PALETTE['grid'])\n",
    "ax.grid(axis='y', color='white', linewidth=0.8)\n",
    "ax.spines[['top', 'right']].set_visible(False)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f'\\nAverage review score by delivery bucket ({period_label}):')\n",
    "for _, row in review_by_delivery.iterrows():\n",
    "    print(f'  {row[\"delivery_bucket\"]:<12} {row[\"review_score\"]:.2f} / 5.0')",
]))

cells.append(md([
    "#### Order Status Distribution\n",
    "\n",
    "Share of all orders by status for the analysis year (includes non-delivered orders).",
]))

cells.append(code([
    "status_dist = calculate_order_status_distribution(orders, ANALYSIS_YEAR)\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(8, 4))\n",
    "ax.barh(\n",
    "    status_dist.index,\n",
    "    status_dist.values * 100,\n",
    "    color=PALETTE['light'],\n",
    "    edgecolor=PALETTE['primary'],\n",
    "    height=0.55,\n",
    ")\n",
    "ax.set_title(\n",
    "    f'Order Status Distribution ({ANALYSIS_YEAR})',\n",
    "    fontsize=14, fontweight='bold', pad=12\n",
    ")\n",
    "ax.set_xlabel('Share of Orders (%)', fontsize=11)\n",
    "ax.set_ylabel('Order Status', fontsize=11)\n",
    "ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))\n",
    "ax.set_facecolor(PALETTE['grid'])\n",
    "ax.grid(axis='x', color='white', linewidth=0.8)\n",
    "ax.spines[['top', 'right']].set_visible(False)\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "print(f'\\nOrder status breakdown ({ANALYSIS_YEAR}):')\n",
    "for status, share in status_dist.items():\n",
    "    print(f'  {status:<20} {share * 100:.1f}%')",
]))

# ── 7. Summary ──────────────────────────────────────────────────────────────
cells.append(md([
    "## 7. Summary of Observations\n",
    "\n",
    "The sections above cover the following dimensions for the configured period:\n",
    "\n",
    "**Revenue**\n",
    "- Total revenue and year-over-year change relative to the prior period.\n",
    "- Monthly revenue trend and mean month-over-month growth rate.\n",
    "- Average order value and its year-over-year change.\n",
    "\n",
    "**Products**\n",
    "- Revenue by product category, identifying the highest-contributing segments.\n",
    "\n",
    "**Geography**\n",
    "- Revenue distribution across US states via choropleth map and ranked table.\n",
    "\n",
    "**Customer Experience**\n",
    "- Average delivery time in days.\n",
    "- Review score distribution (1-5 scale).\n",
    "- Correlation between delivery speed buckets and average review score.\n",
    "- Order status breakdown for the analysis year.\n",
    "\n",
    "To run this analysis for a different period, update `ANALYSIS_YEAR`, `COMPARISON_YEAR`,\n",
    "and `ANALYSIS_MONTH` in Section 3 and run **Kernel > Restart and Run All**.",
]))

# ── Write notebook ──────────────────────────────────────────────────────────
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = pathlib.Path(__file__).parent / "EDA_Refactored.ipynb"
out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print(f"Written: {out}  ({len(cells)} cells)")
