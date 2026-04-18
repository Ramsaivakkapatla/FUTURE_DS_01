"""
Sales Performance PDF Report  –  FIXED
Fix 1 : removed unused kagglehub imports
Fix 2 : replaced Plotly write_image (needs Chrome/kaleido) with matplotlib
Fix 3 : updated CSV path variable at the top
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os, tempfile

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image as RLImage,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ──────────────────────────────────────────────────────────────
# 0. CONFIG  ← change CSV_PATH to your file location
# ──────────────────────────────────────────────────────────────
CSV_PATH   = r"C:/Users/Ramsai vakkapatla/Downloads/product_sales_dataset_final.csv"
OUTPUT_PDF = "Sales_Performance_Report_Real.pdf"

# ──────────────────────────────────────────────────────────────
# 1. LOAD & CLEAN DATA
# ──────────────────────────────────────────────────────────────
print("📦 Loading dataset...")
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()

col_lower = {c.lower().replace(" ", "_"): c for c in df.columns}

def find_col(*candidates):
    for c in candidates:
        if c in col_lower:
            return col_lower[c]
    return None

date_col     = find_col("date", "order_date", "orderdate", "invoice_date", "sale_date")
sales_col    = find_col("sales", "revenue", "amount", "total", "total_sales", "sale_amount")
profit_col   = find_col("profit", "profit_amount", "net_profit")
qty_col      = find_col("quantity", "qty", "units")
category_col = find_col("category", "product_category", "cat")
product_col  = find_col("product", "product_name", "sub-category", "sub_category", "item")
region_col   = find_col("region", "area", "zone", "territory", "state", "city")

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    df = df.dropna(subset=[date_col])
    df["Month"] = df[date_col].dt.to_period("M").astype(str)
    df["Year"]  = df[date_col].dt.year

for col in [sales_col, profit_col, qty_col]:
    if col:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

total_sales  = df[sales_col].sum()  if sales_col  else 0
total_profit = df[profit_col].sum() if profit_col else 0
total_orders = len(df)
margin_pct   = (total_profit / total_sales * 100) if total_sales else 0

print(f"✅ Loaded | Revenue: ${total_sales:,.0f} | Profit: ${total_profit:,.0f} | Margin: {margin_pct:.1f}%")

# ──────────────────────────────────────────────────────────────
# 2. CHART COLOURS  (dark theme matching dashboard)
# ──────────────────────────────────────────────────────────────
BG     = "#0d1117"
CARD   = "#161b22"
ACCENT = "#58a6ff"
GREEN  = "#3fb950"
ORANGE = "#d29922"
PINK   = "#f78166"
TEXT   = "#e6edf3"
MUTED  = "#8b949e"
PALETTE = [ACCENT, GREEN, ORANGE, PINK, "#bc8cff", "#79c0ff", "#56d364", "#ffa657"]

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": CARD,
    "axes.edgecolor": "#21262d", "axes.labelcolor": TEXT,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": TEXT, "grid.color": "#21262d",
    "grid.linestyle": "--", "grid.alpha": 0.6,
})

chart_dir   = tempfile.mkdtemp()
chart_files = {}

def save(fig, name):
    path = os.path.join(chart_dir, f"{name}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    return path

# ── Chart 1: Monthly Revenue & Profit Trend ──
if date_col and sales_col:
    monthly = df.groupby("Month")[sales_col].sum()
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.fill_between(range(len(monthly)), monthly.values, alpha=0.15, color=ACCENT)
    ax.plot(range(len(monthly)), monthly.values, color=ACCENT, lw=2.5, label="Revenue")
    if profit_col:
        mon_p = df.groupby("Month")[profit_col].sum()
        ax.plot(range(len(mon_p)), mon_p.values, color=GREEN, lw=2, ls="--", label="Profit")
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly.index, rotation=45, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
    ax.set_title("Monthly Revenue & Profit Trend", color=TEXT, fontsize=12, pad=10)
    ax.legend(facecolor=CARD, edgecolor="#21262d"); ax.grid(True)
    chart_files["trend"] = save(fig, "trend")

# ── Chart 2: Top 10 Products ─────────────────
if product_col and sales_col:
    tp = df.groupby(product_col)[sales_col].sum().nlargest(10).sort_values()
    fig, ax = plt.subplots(figsize=(10, 4))
    colors_bar = [PALETTE[i % len(PALETTE)] for i in range(len(tp))]
    bars = ax.barh(tp.index, tp.values, color=colors_bar)
    for bar, val in zip(bars, tp.values):
        ax.text(bar.get_width() + tp.values.max()*0.01, bar.get_y()+bar.get_height()/2,
                f"${val:,.0f}", va="center", fontsize=8, color=TEXT)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
    ax.set_title("Top 10 Products by Sales", color=TEXT, fontsize=12, pad=10)
    ax.grid(True, axis="x")
    chart_files["products"] = save(fig, "products")

# ── Chart 3: Sales by Category ───────────────
if category_col and sales_col:
    cat = df.groupby(category_col)[sales_col].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    bars = ax.bar(cat.index, cat.values, color=PALETTE[:len(cat)], width=0.5)
    for bar, val in zip(bars, cat.values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+cat.values.max()*0.01,
                f"${val:,.0f}", ha="center", fontsize=9, color=TEXT)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
    ax.set_title("Sales by Category", color=TEXT, fontsize=12, pad=10)
    ax.grid(True, axis="y")
    chart_files["category"] = save(fig, "category")

# ── Chart 4: Region Pie ───────────────────────
if region_col and sales_col:
    reg = df.groupby(region_col)[sales_col].sum()
    fig, ax = plt.subplots(figsize=(7, 4))
    wedges, texts, autotexts = ax.pie(
        reg.values, labels=reg.index,
        colors=PALETTE[:len(reg)], autopct="%1.1f%%",
        pctdistance=0.75, startangle=90,
        wedgeprops=dict(linewidth=2, edgecolor=BG),
    )
    for t in texts + autotexts:
        t.set_color(TEXT); t.set_fontsize(9)
    # donut hole
    centre = plt.Circle((0,0), 0.5, color=CARD)
    ax.add_patch(centre)
    ax.set_title("Sales by Region", color=TEXT, fontsize=12, pad=10)
    chart_files["region"] = save(fig, "region")

print("✅ Charts rendered with matplotlib")

# ──────────────────────────────────────────────────────────────
# 3. PDF STYLES
# ──────────────────────────────────────────────────────────────
W, H = A4
styles = getSampleStyleSheet()

S = {
    "cover_title": ParagraphStyle("CoverTitle",
        fontSize=28, textColor=colors.HexColor("#58a6ff"),
        spaceAfter=8, alignment=TA_CENTER, fontName="Helvetica-Bold"),
    "cover_sub": ParagraphStyle("CoverSub",
        fontSize=13, textColor=colors.HexColor("#8b949e"),
        alignment=TA_CENTER, spaceAfter=4),
    "section": ParagraphStyle("Section",
        fontSize=16, textColor=colors.HexColor("#58a6ff"),
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("Body",
        fontSize=10, textColor=colors.HexColor("#c9d1d9"),
        leading=15, spaceAfter=6),
    "bullet": ParagraphStyle("Bullet",
        fontSize=10, textColor=colors.HexColor("#c9d1d9"),
        leading=15, leftIndent=14, spaceAfter=4, bulletIndent=4),
    "kpi_val": ParagraphStyle("KPIVal",
        fontSize=20, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#3fb950"), alignment=TA_CENTER),
    "kpi_label": ParagraphStyle("KPILabel",
        fontSize=9, textColor=colors.HexColor("#8b949e"), alignment=TA_CENTER),
    "footer": ParagraphStyle("Footer",
        fontSize=8, textColor=colors.HexColor("#8b949e"), alignment=TA_CENTER),
    "caption": ParagraphStyle("Caption",
        fontSize=8, textColor=colors.HexColor("#8b949e"),
        alignment=TA_CENTER, fontName="Helvetica-Oblique", spaceAfter=8),
}

# ──────────────────────────────────────────────────────────────
# 4. BUILD STORY
# ──────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT_PDF, pagesize=A4,
    topMargin=1.5*cm, bottomMargin=1.5*cm,
    leftMargin=1.8*cm, rightMargin=1.8*cm,
)

story = []

# ── COVER PAGE ────────────────────────────────
story.append(Spacer(1, 3*cm))
story.append(Paragraph("Business Sales", S["cover_title"]))
story.append(Paragraph("Performance Report", S["cover_title"]))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Dataset: product_sales_dataset_final.csv", S["cover_sub"]))
story.append(Paragraph("Prepared with Python  ·  pandas  ·  matplotlib  ·  ReportLab", S["cover_sub"]))
story.append(Spacer(1, 1.5*cm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.8*cm))

# KPI strip
kpi_table = Table([
    [Paragraph(f"${total_sales/1e6:.1f}M",   S["kpi_val"]),
     Paragraph(f"${total_profit/1e6:.1f}M",  S["kpi_val"]),
     Paragraph(f"{margin_pct:.1f}%",          S["kpi_val"]),
     Paragraph(f"{total_orders:,}",           S["kpi_val"])],
    [Paragraph("Total Revenue",  S["kpi_label"]),
     Paragraph("Total Profit",   S["kpi_label"]),
     Paragraph("Profit Margin",  S["kpi_label"]),
     Paragraph("Total Orders",   S["kpi_label"])],
], colWidths=[(W - 3.6*cm) / 4] * 4, rowHeights=[1.2*cm, 0.6*cm])
kpi_table.setStyle(TableStyle([
    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#161b22")),
    ("TOPPADDING",    (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("LINEAFTER",     (0, 0), (2, -1), 1, colors.HexColor("#21262d")),
    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(kpi_table)
story.append(PageBreak())

# ── SECTION 1: EXECUTIVE SUMMARY ─────────────
story.append(Paragraph("1. Executive Summary", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    f"This report presents a comprehensive sales performance analysis based on "
    f"<b>{total_orders:,}</b> transactions. The business generated total revenue of "
    f"<b>${total_sales:,.0f}</b> with a profit of <b>${total_profit:,.0f}</b>, "
    f"yielding a profit margin of <b>{margin_pct:.1f}%</b>.", S["body"]))

for item in [
    f"Total transactions analysed: {total_orders:,}",
    f"Gross Revenue: ${total_sales:,.0f}",
    f"Net Profit: ${total_profit:,.0f}",
    f"Profit Margin: {margin_pct:.1f}%",
]:
    story.append(Paragraph(f"• {item}", S["bullet"]))

if date_col:
    dr = f"{df[date_col].min().date()} to {df[date_col].max().date()}"
    story.append(Paragraph(f"• Date range covered: {dr}", S["bullet"]))

story.append(Spacer(1, 0.5*cm))

# ── SECTION 2: REVENUE TREND ─────────────────
story.append(Paragraph("2. Revenue Trend Analysis", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))

if "trend" in chart_files:
    story.append(RLImage(chart_files["trend"], width=16*cm, height=5.6*cm))
    story.append(Paragraph("Figure 1 – Monthly Revenue & Profit Trend", S["caption"]))

if date_col and sales_col:
    monthly = df.groupby("Month")[sales_col].sum()
    best_month = monthly.idxmax()
    best_val   = monthly.max()
    story.append(Paragraph(
        f"Peak revenue was recorded in <b>{best_month}</b> at <b>${best_val:,.0f}</b>. "
        f"Seasonal patterns visible in the trend can guide inventory and marketing planning.",
        S["body"]))

story.append(Spacer(1, 0.5*cm))

# ── SECTION 3: CATEGORY ANALYSIS ─────────────
story.append(Paragraph("3. Category Performance", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))

if "category" in chart_files:
    story.append(RLImage(chart_files["category"], width=15*cm, height=5.3*cm))
    story.append(Paragraph("Figure 2 – Sales by Category", S["caption"]))

if category_col and sales_col:
    cat_s = df.groupby(category_col).agg(Sales=(sales_col, "sum")).reset_index().sort_values("Sales", ascending=False)
    if profit_col:
        cat_s = cat_s.merge(df.groupby(category_col)[profit_col].sum().reset_index(), on=category_col)
        cat_s["Margin"] = (cat_s[profit_col] / cat_s["Sales"] * 100).round(1)

    headers = [category_col, "Sales ($)", "Profit ($)", "Margin (%)"] if profit_col else [category_col, "Sales ($)"]
    tdata = [[Paragraph(h, ParagraphStyle("th", fontSize=9, fontName="Helvetica-Bold",
              textColor=colors.HexColor("#58a6ff"), alignment=TA_CENTER)) for h in headers]]
    for _, row in cat_s.iterrows():
        r = [Paragraph(str(row[category_col]), S["body"]),
             Paragraph(f"${row['Sales']:,.0f}", S["body"])]
        if profit_col:
            r += [Paragraph(f"${row[profit_col]:,.0f}", S["body"]),
                  Paragraph(f"{row['Margin']}%", S["body"])]
        tdata.append(r)

    ct = Table(tdata, colWidths=[(W-3.6*cm)/len(headers)]*len(headers))
    ct.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  colors.HexColor("#21262d")),
        ("BACKGROUND",     (0,1),(-1,-1), colors.HexColor("#161b22")),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.HexColor("#161b22"), colors.HexColor("#0d1117")]),
        ("GRID",           (0,0),(-1,-1), 0.3, colors.HexColor("#21262d")),
        ("FONTSIZE",       (0,0),(-1,-1), 9),
        ("TOPPADDING",     (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 6),
        ("LEFTPADDING",    (0,0),(-1,-1), 8),
        ("ALIGN",          (1,0),(-1,-1), "CENTER"),
    ]))
    story.append(ct)

story.append(Spacer(1, 0.5*cm))

# ── SECTION 4: TOP PRODUCTS ───────────────────
story.append(Paragraph("4. Top-Performing Products", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))
if "products" in chart_files:
    story.append(RLImage(chart_files["products"], width=16*cm, height=6*cm))
    story.append(Paragraph("Figure 3 – Top 10 Products by Revenue", S["caption"]))
story.append(Spacer(1, 0.5*cm))

# ── SECTION 5: REGIONAL ───────────────────────
story.append(Paragraph("5. Regional Performance", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))
if "region" in chart_files:
    story.append(RLImage(chart_files["region"], width=10*cm, height=6*cm))
    story.append(Paragraph("Figure 4 – Sales by Region", S["caption"]))
if region_col and sales_col:
    reg_s = df.groupby(region_col)[sales_col].sum().sort_values(ascending=False)
    top_r = reg_s.index[0]
    story.append(Paragraph(
        f"The strongest region is <b>{top_r}</b> with total sales of <b>${reg_s.iloc[0]:,.0f}</b>. "
        f"Regional gaps present opportunities to replicate high-performing strategies.", S["body"]))
story.append(Spacer(1, 0.5*cm))

# ── SECTION 6: RECOMMENDATIONS ───────────────
story.append(Paragraph("6. Business Recommendations", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))

recs = []
if category_col and profit_col and sales_col:
    best_cat_m = df.groupby(category_col).apply(
        lambda x: x[profit_col].sum() / x[sales_col].sum() * 100 if x[sales_col].sum() else 0
    ).idxmax()
    recs.append(f"Double down on <b>{best_cat_m}</b> — it delivers the highest profit margin. Increase inventory and marketing investment here.")
if product_col and sales_col:
    best_p = df.groupby(product_col)[sales_col].sum().idxmax()
    recs.append(f"Expand the <b>{best_p}</b> product line — it is the top revenue driver. Consider bundling or upselling strategies around it.")
if region_col and sales_col:
    worst_r = df.groupby(region_col)[sales_col].sum().idxmin()
    recs.append(f"Investigate underperformance in the <b>{worst_r}</b> region. Run targeted promotions or assess distribution challenges.")
recs += [
    "Introduce seasonal promotions aligned with monthly peak periods to maintain revenue during slow months.",
    "Review SKUs with high sales but low margins — reduce costs or discontinue if margins cannot be improved.",
    "Strengthen retention with loyalty programmes for top-spending customer segments.",
]
for i, rec in enumerate(recs[:6], 1):
    story.append(Paragraph(f"{i}. {rec}", S["bullet"]))
    story.append(Spacer(1, 0.12*cm))

story.append(Spacer(1, 0.5*cm))

# ── SECTION 7: CONCLUSION ─────────────────────
story.append(Paragraph("7. Conclusion", S["section"]))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    f"This analysis of {total_orders:,} transactions confirms a business generating "
    f"${total_sales:,.0f} in revenue at a {margin_pct:.1f}% profit margin. "
    f"Clear opportunities exist through targeted category investment, regional expansion, "
    f"and product-level optimisation. Implementing the recommendations above can drive "
    f"meaningful improvement in both top-line growth and margin in the coming quarters.",
    S["body"]))

story.append(Spacer(1, 2*cm))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#21262d")))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "Generated with Python | pandas · matplotlib · ReportLab | For internship submission",
    S["footer"]))

# ── BUILD PDF ─────────────────────────────────
doc.build(story)
print(f"\n✅ PDF report saved → {OUTPUT_PDF}")