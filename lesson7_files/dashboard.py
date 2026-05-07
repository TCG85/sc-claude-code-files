"""
dashboard.py

Streamlit e-commerce sales dashboard.
Run with: streamlit run dashboard.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_loader import load_data, build_sales_data, filter_by_period
from business_metrics import (
    calculate_avg_order_value,
    calculate_avg_review_by_delivery,
    calculate_delivery_metrics,
    calculate_monthly_growth,
    calculate_monthly_revenue,
    calculate_product_sales,
    calculate_revenue,
    calculate_revenue_growth,
    calculate_sales_by_state,
    calculate_total_orders,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Colour tokens ──────────────────────────────────────────────────────────────
C = {
    "primary": "#2C5F8A",
    "light":   "#A8C8E8",
    "pos":     "#16a34a",
    "neg":     "#dc2626",
    "grid":    "#e2e8f0",
}

PLOT_BASE = dict(
    paper_bgcolor="white",
    plot_bgcolor="#f8fafc",
    font=dict(family="sans-serif", size=12, color="#374151"),
    margin=dict(l=16, r=16, t=52, b=16),
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Collapse empty blocks Streamlit injects after plotly charts */
div[data-testid="stVerticalBlock"] > div:empty { display: none; }
div[data-testid="stElementContainer"]:empty    { display: none; }

/* KPI cards */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 20px 22px;
    height: 120px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-label {
    font-size: 11px;
    color: #6b7280;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
.kpi-value {
    font-size: 30px;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.1;
}
.kpi-delta { font-size: 12px; font-weight: 500; }

/* Bottom metric cards */
.bottom-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 28px 22px;
    height: 150px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}
.bottom-label {
    font-size: 11px;
    color: #6b7280;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 8px;
}
.bottom-value {
    font-size: 38px;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.1;
}
.bottom-delta { font-size: 12px; font-weight: 500; margin-top: 6px; }
.star-row     { font-size: 20px; color: #f59e0b; margin: 4px 0; letter-spacing: 3px; }
.bottom-subtitle { font-size: 12px; color: #6b7280; margin-top: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Utilities ──────────────────────────────────────────────────────────────────
def fmt_currency(value) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def fmt_pct(g) -> str:
    if g is None or pd.isna(g):
        return "N/A"
    sign = "+" if g >= 0 else ""
    return f"{sign}{g * 100:.2f}%"


def trend_html(g, comp_label: str, inverted: bool = False, css_class: str = "kpi-delta") -> str:
    if g is None or pd.isna(g):
        return ""
    good = (g < 0) if inverted else (g >= 0)
    color = C["pos"] if good else C["neg"]
    arrow = "▼ " if g < 0 else "▲ "
    return (
        f'<div class="{css_class}" style="color:{color};">'
        f"{arrow}{fmt_pct(g)} vs {comp_label}</div>"
    )


def star_rating(score) -> str:
    if score is None or pd.isna(score):
        return "☆☆☆☆☆"
    n = max(0, min(5, round(score)))
    return "★" * n + "☆" * (5 - n)


def make_yticks(values: list) -> tuple[list, list]:
    clean = [v for v in values if v is not None and not pd.isna(v) and v >= 0]
    if not clean or max(clean) == 0:
        return [0], ["$0"]
    max_val = max(clean)
    for step in [5_000_000, 2_000_000, 1_000_000, 500_000, 200_000, 100_000,
                 50_000, 25_000, 10_000, 5_000, 2_000, 1_000, 500]:
        if max_val / step >= 3:
            break
    else:
        step = 100
    ticks = [i * step for i in range(int(max_val / step) + 2)]
    texts = []
    for t in ticks:
        if t >= 1_000_000:
            texts.append(f"${t / 1_000_000:.1f}M")
        elif t >= 1_000:
            texts.append(f"${t / 1_000:.0f}K")
        else:
            texts.append(f"${t:.0f}")
    return ticks, texts


def blue_gradient(n: int) -> list[str]:
    """Index 0 = darkest (highest value), last = lightest."""
    return [
        f"rgba(44, 95, 138, {1.0 - 0.65 * i / max(n - 1, 1):.2f})"
        for i in range(n)
    ]


# ── Data (cached) ──────────────────────────────────────────────────────────────
@st.cache_data
def get_data(data_dir: str = "ecommerce_data"):
    orders, order_items, products, customers, reviews, _ = load_data(data_dir)
    sales = build_sales_data(orders, order_items)
    return orders, products, customers, reviews, sales


orders_df, products_df, customers_df, reviews_df, sales_all = get_data()

# ── Header & filters ───────────────────────────────────────────────────────────
col_title, col_year, col_month = st.columns([4, 1, 1])

with col_title:
    st.markdown("## E-Commerce Sales Dashboard")

with col_year:
    years = sorted(sales_all["year"].unique(), reverse=True)
    default_year_idx = years.index(2023) if 2023 in years else 0
    selected_year = st.selectbox("Year", years, index=default_year_idx)

with col_month:
    # "All" at index 0; month names at indices 1–12 map directly to month numbers
    month_opts = ["All"] + [pd.Timestamp(2020, m, 1).strftime("%b") for m in range(1, 13)]
    sel_month_label = st.selectbox("Month", month_opts, index=0)
    selected_month = None if sel_month_label == "All" else month_opts.index(sel_month_label)

comparison_year = selected_year - 1

period_label = f"{sel_month_label} {selected_year}" if selected_month else str(selected_year)
comp_label   = f"{sel_month_label} {comparison_year}" if selected_month else str(comparison_year)

st.markdown(
    f"<p style='color:#6b7280;font-size:13px;margin-top:-14px;'>"
    f"Showing {period_label} — compared to {comp_label}</p>",
    unsafe_allow_html=True,
)

# ── Filtered data ──────────────────────────────────────────────────────────────
sales_cur = filter_by_period(sales_all, selected_year, selected_month)
sales_pri = filter_by_period(sales_all, comparison_year, selected_month)

# ── Metrics ────────────────────────────────────────────────────────────────────
revenue_cur = calculate_revenue(sales_cur)
revenue_pri = calculate_revenue(sales_pri)
rev_growth  = calculate_revenue_growth(revenue_cur, revenue_pri)

orders_cur  = calculate_total_orders(sales_cur)
orders_pri  = calculate_total_orders(sales_pri)
ord_growth  = calculate_revenue_growth(orders_cur, orders_pri)

aov_cur     = calculate_avg_order_value(sales_cur)
aov_pri     = calculate_avg_order_value(sales_pri)
aov_growth  = calculate_revenue_growth(aov_cur, aov_pri)

# MoM growth requires at least two months of data
if selected_month is None:
    mom_vals = calculate_monthly_growth(sales_cur).dropna()
    mom_mean = mom_vals.mean() if len(mom_vals) > 0 else None
else:
    mom_mean = None

delivery_cur = calculate_delivery_metrics(sales_cur, reviews_df)
delivery_pri = calculate_delivery_metrics(sales_pri, reviews_df)
avg_del_cur  = delivery_cur["delivery_days"].mean()
avg_del_pri  = delivery_pri["delivery_days"].mean() if len(delivery_pri) > 0 else None
del_growth   = calculate_revenue_growth(avg_del_cur, avg_del_pri)
avg_rev_cur  = delivery_cur["review_score"].mean()

# ── KPI Row ────────────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, growth=None, inverted: bool = False) -> str:
    delta = trend_html(growth, comp_label, inverted=inverted) if growth is not None else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta}'
        f'</div>'
    )


kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    st.markdown(kpi_card("Total Revenue", fmt_currency(revenue_cur), rev_growth), unsafe_allow_html=True)
with kc2:
    st.markdown(kpi_card("Avg Monthly Growth", fmt_pct(mom_mean)), unsafe_allow_html=True)
with kc3:
    st.markdown(kpi_card("Avg Order Value", f"${aov_cur:,.0f}", aov_growth), unsafe_allow_html=True)
with kc4:
    st.markdown(kpi_card("Total Orders", f"{orders_cur:,}", ord_growth), unsafe_allow_html=True)

# ── Chart Row 1 ────────────────────────────────────────────────────────────────
row1_l, row1_r = st.columns(2)

with row1_l:
    monthly_cur = calculate_monthly_revenue(sales_cur)
    monthly_pri = calculate_monthly_revenue(sales_pri)
    all_rev = list(monthly_cur.values) + (list(monthly_pri.values) if len(monthly_pri) else [])
    yticks, ytexts = make_yticks(all_rev)

    def mlabels(idx):
        return [pd.Timestamp(2020, m, 1).strftime("%b") for m in idx]

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=mlabels(monthly_cur.index),
        y=monthly_cur.values,
        name=str(selected_year),
        mode="lines+markers",
        line=dict(color=C["primary"], width=2.5),
        marker=dict(size=6, color=C["primary"]),
        hovertemplate="%{x}: %{customdata}<extra></extra>",
        customdata=[fmt_currency(v) for v in monthly_cur.values],
    ))
    if len(monthly_pri) > 0:
        fig_trend.add_trace(go.Scatter(
            x=mlabels(monthly_pri.index),
            y=monthly_pri.values,
            name=str(comparison_year),
            mode="lines+markers",
            line=dict(color=C["light"], width=2, dash="dash"),
            marker=dict(size=5, color=C["light"]),
            hovertemplate="%{x}: %{customdata}<extra></extra>",
            customdata=[fmt_currency(v) for v in monthly_pri.values],
        ))
    fig_trend.update_layout(
        title=f"Monthly Revenue — {period_label} vs {comp_label}",
        xaxis=dict(title="Month", showgrid=True, gridcolor=C["grid"]),
        yaxis=dict(title="Revenue", showgrid=True, gridcolor=C["grid"],
                   tickvals=yticks, ticktext=ytexts),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **PLOT_BASE,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with row1_r:
    prod_sales = calculate_product_sales(sales_cur, products_df).head(10)
    n = len(prod_sales)
    yticks_c, ytexts_c = make_yticks(prod_sales.values.tolist())

    fig_cats = go.Figure(go.Bar(
        x=prod_sales.index.tolist(),
        y=prod_sales.values,
        marker_color=blue_gradient(n),
        hovertemplate="%{x}<br>Revenue: %{customdata}<extra></extra>",
        customdata=[fmt_currency(v) for v in prod_sales.values],
    ))
    fig_cats.update_layout(
        title=f"Top 10 Categories by Revenue ({period_label})",
        xaxis=dict(title="", tickangle=-35, showgrid=False),
        yaxis=dict(title="Revenue", showgrid=True, gridcolor=C["grid"],
                   tickvals=yticks_c, ticktext=ytexts_c),
        **PLOT_BASE,
    )
    st.plotly_chart(fig_cats, use_container_width=True)

# ── Chart Row 2 ────────────────────────────────────────────────────────────────
row2_l, row2_r = st.columns(2)

with row2_l:
    state_data = calculate_sales_by_state(sales_cur, orders_df, customers_df)
    state_data["Revenue"] = state_data["price"].apply(fmt_currency)
    yticks_m, ytexts_m = make_yticks(state_data["price"].tolist())

    fig_map = px.choropleth(
        state_data,
        locations="customer_state",
        color="price",
        locationmode="USA-states",
        scope="usa",
        color_continuous_scale="Blues",
        hover_name="customer_state",
        hover_data={"price": False, "customer_state": False, "Revenue": True},
    )
    fig_map.update_layout(
        title=f"Revenue by State ({period_label})",
        coloraxis_colorbar=dict(title="Revenue", tickvals=yticks_m,
                                ticktext=ytexts_m, len=0.75),
        margin=dict(l=0, r=0, t=52, b=0),
        paper_bgcolor="white",
        font=dict(family="sans-serif", size=12, color="#374151"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with row2_r:
    bucket_order = ["1-3 days", "4-7 days", "8+ days"]
    rev_by_del = calculate_avg_review_by_delivery(delivery_cur)
    rev_by_del["delivery_bucket"] = pd.Categorical(
        rev_by_del["delivery_bucket"], categories=bucket_order, ordered=True
    )
    rev_by_del = rev_by_del.sort_values("delivery_bucket")

    fig_del = go.Figure(go.Bar(
        x=rev_by_del["delivery_bucket"].astype(str),
        y=rev_by_del["review_score"],
        marker_color=C["primary"],
        width=0.45,
        hovertemplate="%{x}<br>Avg Score: %{y:.2f}<extra></extra>",
    ))
    fig_del.update_layout(
        title=f"Customer Satisfaction by Delivery Speed ({period_label})",
        xaxis=dict(title="Delivery Time", showgrid=False),
        yaxis=dict(title="Avg Review Score", showgrid=True, gridcolor=C["grid"],
                   range=[0, 5], dtick=1),
        **PLOT_BASE,
    )
    st.plotly_chart(fig_del, use_container_width=True)

# ── Bottom Row ─────────────────────────────────────────────────────────────────
bot_l, bot_r = st.columns(2)

with bot_l:
    del_delta = trend_html(del_growth, comp_label, inverted=True, css_class="bottom-delta")
    avg_del_display = f"{avg_del_cur:.1f} days" if not pd.isna(avg_del_cur) else "N/A"
    st.markdown(
        f'<div class="bottom-card">'
        f'<div class="bottom-label">Average Delivery Time</div>'
        f'<div class="bottom-value">{avg_del_display}</div>'
        f'{del_delta}'
        f'</div>',
        unsafe_allow_html=True,
    )

with bot_r:
    avg_rev_display = f"{avg_rev_cur:.2f}" if not pd.isna(avg_rev_cur) else "N/A"
    st.markdown(
        f'<div class="bottom-card">'
        f'<div class="bottom-label">Customer Satisfaction</div>'
        f'<div class="bottom-value">{avg_rev_display}</div>'
        f'<div class="star-row">{star_rating(avg_rev_cur)}</div>'
        f'<div class="bottom-subtitle">Average Review Score</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
