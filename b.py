"""
Sales Performance Dashboard  –  FIXED
Dataset : product_sales_dataset_final.csv
Fix     : added include_plotlyjs='cdn' to write_html (was causing "Plotly is not defined")
          removed unused kagglehub imports
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# 1. LOAD DATASET  – update path if needed
# ─────────────────────────────────────────────
CSV_PATH = r"C:/Users/Ramsai vakkapatla/Downloads/product_sales_dataset_final.csv"   # ← change to your local path if different

print("📦 Loading dataset...")
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
print(f"✅ Loaded {len(df):,} rows | Columns: {list(df.columns)}")

# ─────────────────────────────────────────────
# 2. AUTO-DETECT COLUMNS
# ─────────────────────────────────────────────
col_lower = {c.lower().replace(" ", "_"): c for c in df.columns}

def find_col(*candidates):
    for c in candidates:
        if c in col_lower:
            return col_lower[c]
    return None

date_col     = find_col("date", "order_date", "orderdate", "invoice_date", "sale_date")
sales_col    = find_col("sales", "revenue", "amount", "total", "total_sales", "sale_amount")
profit_col   = find_col("profit", "profit_amount", "net_profit")
qty_col      = find_col("quantity", "qty", "units", "quantity_sold")
category_col = find_col("category", "product_category", "cat")
product_col  = find_col("product", "product_name", "sub-category", "sub_category", "item")
region_col   = find_col("region", "area", "zone", "territory", "state", "city")
segment_col  = find_col("segment", "customer_segment", "customer_type")

print(f"\n📋 Column mapping detected:")
for label, col in [("Date", date_col), ("Sales", sales_col), ("Profit", profit_col),
                   ("Quantity", qty_col), ("Category", category_col),
                   ("Product", product_col), ("Region", region_col), ("Segment", segment_col)]:
    print(f"  {label:10s} → {col}")

# ─────────────────────────────────────────────
# 3. DATA CLEANING
# ─────────────────────────────────────────────
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    df = df.dropna(subset=[date_col])
    df["Month"] = df[date_col].dt.to_period("M").astype(str)
    df["Year"]  = df[date_col].dt.year

for col in [sales_col, profit_col, qty_col]:
    if col:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ─────────────────────────────────────────────
# 4. KPIs
# ─────────────────────────────────────────────
total_sales  = df[sales_col].sum()  if sales_col  else 0
total_profit = df[profit_col].sum() if profit_col else 0
total_orders = len(df)
margin_pct   = (total_profit / total_sales * 100) if total_sales else 0

print(f"\n💰 KPIs  |  Revenue: ${total_sales:,.0f}  |  Profit: ${total_profit:,.0f}  |  Margin: {margin_pct:.1f}%")

# ─────────────────────────────────────────────
# 5. BUILD DASHBOARD
# ─────────────────────────────────────────────
BG      = "#0d1117"
CARD_BG = "#161b22"
ACCENT  = "#58a6ff"
GREEN   = "#3fb950"
ORANGE  = "#d29922"
PINK    = "#f78166"
TEXT    = "#e6edf3"
MUTED   = "#8b949e"
COLORS  = [ACCENT, GREEN, ORANGE, PINK, "#bc8cff", "#79c0ff", "#56d364", "#ffa657"]

fig = make_subplots(
    rows=4, cols=3,
    row_heights=[0.12, 0.28, 0.28, 0.32],
    subplot_titles=[
        "💰 Total Revenue", "📈 Total Profit", "📊 Profit Margin",
        "Revenue & Profit Trend (Monthly)", "", "",
        "Top 10 Products by Sales",        "", "",
        "Sales by Category", "Sales by Region", "Sales by Segment",
    ],
    specs=[
        [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
        [{"colspan": 3, "type": "xy"},  None, None],
        [{"colspan": 3, "type": "xy"},  None, None],
        [{"type": "xy"}, {"type": "domain"}, {"type": "domain"}],
    ],
    vertical_spacing=0.06,
    horizontal_spacing=0.05,
)

# ── Row 1: KPI Indicators ────────────────────
for col, val, disp, color, title in [
    (1, total_sales,  f"${total_sales/1e6:.2f}M",  GREEN,  "💰 Total Revenue"),
    (2, total_profit, f"${total_profit/1e6:.2f}M", ACCENT, "📈 Total Profit"),
    (3, margin_pct,   f"{margin_pct:.1f}%",         ORANGE, "📊 Profit Margin"),
]:
    fig.add_trace(go.Indicator(
        mode="number",
        value=val,
        number={"font": {"size": 36, "color": color, "family": "Arial Black"}},
        title={"text": f"<b>{title}</b><br><span style='font-size:22px;color:{color}'>{disp}</span>",
               "font": {"size": 12, "color": MUTED}},
    ), row=1, col=col)

# ── Row 2: Monthly Trend ─────────────────────
if date_col and sales_col:
    monthly = df.groupby("Month").agg(Sales=(sales_col, "sum")).reset_index()
    if profit_col:
        monthly = monthly.merge(df.groupby("Month")[profit_col].sum().reset_index(), on="Month")

    fig.add_trace(go.Scatter(
        x=monthly["Month"], y=monthly["Sales"],
        name="Revenue", line=dict(color=ACCENT, width=2.5),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.12)",
        mode="lines+markers", marker=dict(size=4, color=ACCENT),
    ), row=2, col=1)

    if profit_col:
        fig.add_trace(go.Scatter(
            x=monthly["Month"], y=monthly[profit_col],
            name="Profit", line=dict(color=GREEN, width=2.5, dash="dot"),
            mode="lines+markers", marker=dict(size=4, color=GREEN),
        ), row=2, col=1)

# ── Row 3: Top 10 Products ───────────────────
if product_col and sales_col:
    top_products = (df.groupby(product_col)[sales_col].sum()
                    .nlargest(10).sort_values().reset_index())
    bar_colors = [COLORS[i % len(COLORS)] for i in range(len(top_products))]
    fig.add_trace(go.Bar(
        x=top_products[sales_col], y=top_products[product_col],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"  ${v:,.0f}" for v in top_products[sales_col]],
        textposition="outside",
        textfont=dict(color=TEXT, size=10),
        name="Top Products",
    ), row=3, col=1)

# ── Row 4: Category / Region / Segment ───────
if category_col and sales_col:
    cat = (df.groupby(category_col)[sales_col].sum()
           .reset_index().sort_values(sales_col, ascending=False))
    fig.add_trace(go.Bar(
        x=cat[category_col], y=cat[sales_col],
        marker_color=COLORS[:len(cat)],
        text=[f"${v:,.0f}" for v in cat[sales_col]],
        textposition="outside",
        textfont=dict(color=TEXT, size=10),
        name="Category",
    ), row=4, col=1)

if region_col and sales_col:
    reg = df.groupby(region_col)[sales_col].sum().reset_index()
    fig.add_trace(go.Pie(
        labels=reg[region_col], values=reg[sales_col],
        marker=dict(colors=COLORS, line=dict(color=BG, width=2)),
        hole=0.45, name="Region", textfont=dict(color=TEXT),
    ), row=4, col=2)

if segment_col and sales_col:
    seg = df.groupby(segment_col)[sales_col].sum().reset_index()
    fig.add_trace(go.Pie(
        labels=seg[segment_col], values=seg[sales_col],
        marker=dict(colors=COLORS[2:], line=dict(color=BG, width=2)),
        hole=0.45, name="Segment", textfont=dict(color=TEXT),
    ), row=4, col=3)

# ── Global Layout ─────────────────────────────
fig.update_layout(
    title=dict(
        text=f"<b>🚀 Business Sales Performance Dashboard</b><br>"
             f"<span style='font-size:13px;color:{MUTED}'>"
             f"{total_orders:,} Transactions  ·  Revenue: ${total_sales/1e6:.1f}M  ·  "
             f"Profit Margin: {margin_pct:.1f}%</span>",
        font=dict(size=24, color=TEXT, family="Arial"),
        x=0.5, xanchor="center", y=0.99,
    ),
    height=1300,
    paper_bgcolor=BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="Arial, sans-serif", color=TEXT),
    showlegend=True,
    legend=dict(bgcolor="rgba(22,27,34,0.85)", bordercolor=MUTED,
                borderwidth=1, font=dict(color=TEXT)),
    margin=dict(t=90, b=40, l=60, r=60),
    hoverlabel=dict(bgcolor=CARD_BG, bordercolor=MUTED, font=dict(color=TEXT)),
)

fig.update_xaxes(gridcolor="#21262d", linecolor="#21262d", tickfont=dict(color=MUTED))
fig.update_yaxes(gridcolor="#21262d", linecolor="#21262d", tickfont=dict(color=MUTED))

for ann in fig.layout.annotations:
    ann.font.color = TEXT
    ann.font.size  = 12

# ─────────────────────────────────────────────
# 6. SAVE  ← FIX: include_plotlyjs='cdn' added
#           This was the cause of "Plotly is not defined" error
# ─────────────────────────────────────────────
fig.write_html(
    "sales_dashboard_real.html",
    include_plotlyjs="cdn",     # ← THE FIX
    config={"displayModeBar": True, "displaylogo": False},
)
print("\n✅ Dashboard saved → sales_dashboard_real.html")
print("   Open in any browser — Plotly loads from CDN, no local install needed.")