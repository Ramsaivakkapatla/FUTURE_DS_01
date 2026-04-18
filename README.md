# FUTURE_DS_01
# 📊 Business Sales Performance Analysis

> Internship Analytics Project | Python + Plotly + ReportLab

---

## 🔍 Overview

A full end-to-end sales performance analysis built on the **vinothkannaece/sales-dataset** from Kaggle.
Includes an interactive HTML dashboard and a client-ready PDF report with insights and recommendations.

## 📁 Project Structure

```
├── dashboard_real.py          # Interactive Plotly dashboard
├── report_real.py             # PDF report generator
├── sales_dashboard_real.html  # Output: Interactive dashboard
└── Sales_Performance_Report_Real.pdf  # Output: Client-ready PDF report
```

## 📊 What's Analysed

| Area | Details |
|------|---------|
| KPIs | Total Revenue, Profit, Margin %, Order Count |
| Trend | Monthly Revenue & Profit over time |
| Products | Top 10 sub-categories by sales |
| Categories | Sales & margin comparison across categories |
| Regions | Geographic performance breakdown |
| Segments | Customer segment revenue split |

## 🚀 How to Run

### 1. Install dependencies

```bash
pip install pandas plotly kagglehub reportlab kaleido
```

### 2. Set up Kaggle credentials

Create `~/.kaggle/kaggle.json`:
```json
{ "username": "YOUR_KAGGLE_USERNAME", "key": "YOUR_KAGGLE_API_KEY" }
```
Get your key from: https://www.kaggle.com/settings → API → Create New Token

### 3. Run the dashboard

```bash
python dashboard_real.py
```
Opens `sales_dashboard_real.html` — view in any browser.

### 4. Generate the PDF report

```bash
python report_real.py
```
Creates `Sales_Performance_Report_Real.pdf`.

## 🛠️ Tools Used

- **Python** — data processing & scripting
- **Pandas** — data cleaning & aggregation
- **Plotly** — interactive charts & dashboard
- **ReportLab** — professional PDF report generation
- **KaggleHub** — dataset loading

## 💡 Key Insights

*(Auto-generated from real data when you run the scripts)*

- Top revenue category identified
- Best-performing region highlighted
- Seasonal trends mapped month-by-month
- Profit margin benchmarks per category
- 6 actionable business recommendations included in PDF

---

*Project submitted as part of internship data analytics task.*
