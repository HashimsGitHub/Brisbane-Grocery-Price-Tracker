<div align="center">

# 📊 Brisbane Grocery Price Tracker

### *Live prices. Zero effort. Real savings.*

**Automatically scrapes and visualises grocery prices across Brisbane — Woolworths & Coles.**

[![Live App](https://img.shields.io/badge/🚀%20Live%20App-oz--price--tracker.streamlit.app-00EEFF?style=for-the-badge&labelColor=000000)](https://oz-price-tracker.streamlit.app/)
[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-00C853?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

---

</div>

## 💡 What is this?

Brisbane Grocery Price Tracker is a **fully automated price intelligence dashboard** for Brisbane shoppers. It scrapes live prices directly from Woolworths and Coles, stores them in MongoDB, and renders them as rich interactive visualisations.

No manual entry. No crowdsourcing. No user input required — just run a scrape and explore the data.

---

## 🗂️ Pages & Features

### 🏠 Dashboard
A live snapshot of the Brisbane grocery market:
- **Biggest Price Movers** — diverging bar chart comparing this week vs last week across all items
- **Store Average Price This Week** — brand-coloured bar chart (green/red) for Woolworths vs Coles
- **Most Tracked Items** — neon gradient bar chart of the most frequently scraped groceries
- **Suburb Activity Map** — geographic heatmap of price data density across Brisbane
- **Recently Scraped Prices** — live scrollable feed of the latest records

### 🤖 Auto-Scrape
The data engine that powers the entire app:
- Fetches current prices from **Woolworths** and **Coles** via their own search APIs
- Covers **7 Woolworths** + **10 Coles** stores — Brisbane CBD to Caboolture
- Uses **Chrome TLS impersonation** (`curl_cffi`) to bypass bot detection
- **Parallel scraping** — 4 Woolworths + 4 Coles concurrent workers (~3–4 min for full run)
- **Smart deduplication** — skips any store/item scraped within the last 6 hours
- Checkbox store selector with live search and dynamic request count estimate
- Run on demand with a single button click

### 📈 Price History
Seven automated charts across a selectable time window (7–180 days):
- Woolworths vs Coles average price over time (line chart, brand colours)
- Average price by category over time (weekly multi-line)
- Top 10 most expensive & 10 cheapest items (side-by-side bars)
- Price heatmap — category × store (RdYlGn colour scale)
- Price distribution box plots by category, split by store
- Average price by Brisbane suburb (top 15 by record count)
- Weekly scrape volume stacked bar (Woolworths/Coles)

### 🗺️ Suburb Compare
Six automated suburb-level charts — no suburb selection needed:
- Suburb price ranking — all suburbs colour-coded green → red by quartile
- Woolworths vs Coles price gap per suburb — diverging bar chart
- Suburb × category price heatmap
- Cheapest & priciest suburb per category — mini 3-column grid
- Weekly price trend for the 6 most-tracked suburbs
- Price spread box plot — distribution and outliers for every suburb

### 📊 Store Rankings
Six automated retailer comparison charts:
- Overall winner score cards (avg, median, record count)
- Head-to-head by category — grouped bars, Woolworths vs Coles
- Biggest price gaps per item — diverging bar (green = WW cheaper, red = Coles cheaper)
- Weekly price trend line (Woolworths green vs Coles red)
- Full item × store price heatmap
- Average price by individual store branch and suburb

---

## 🛍️ Items Tracked

**118 common groceries** across 13 categories — all stocked by both Woolworths and Coles:

| Category | Count | Examples |
|---|---|---|
| 🥛 Dairy & Eggs | 13 | Full Cream Milk, Oat Milk, Greek Yoghurt, Eggs, Butter |
| 🍞 Bakery | 6 | White Bread, Sourdough, Croissants, Plain Flour |
| 🥩 Meat | 8 | Chicken Breast, Beef Mince, Lamb Chops, Bacon |
| 🐟 Seafood | 4 | Salmon, Barramundi, Prawns, Frozen Fish |
| 🥗 Deli | 2 | Shaved Ham, Salami |
| 🥦 Produce | 24 | Bananas, Avocado, Broccoli, Sweet Potato, Mushrooms |
| 🍚 Pantry | 26 | Vegemite, Milo, Weet-Bix, Pasta, Olive Oil, Honey |
| 🧊 Frozen | 5 | Frozen Peas, Chips, Ice Cream, Pizza |
| 🍫 Snacks | 5 | Tim Tams, Shapes, Chips, Chocolate Block |
| 🥤 Drinks | 8 | OJ, Coke, Beer, Wine, Sparkling Water |
| 🏠 Household | 5 | Toilet Paper, Dishwashing Liquid, Laundry Powder |
| 💊 Health | 7 | Sunscreen, Paracetamol, Shampoo, Toothpaste |
| ⛽ Fuel | 3 | Unleaded, Premium, Diesel |

---

## 🗺️ Brisbane Stores Covered

| Retailer | Stores |
|---|---|
| 🟢 **Woolworths** | Brisbane CBD · Toowong · Chermside · Mount Gravatt · Sunnybank · Redcliffe · Caboolture |
| 🔴 **Coles** | Brisbane CBD · South Brisbane · Toowong · Chermside · Mount Gravatt · Indooroopilly · Sunnybank · Nundah · Strathpine · Caboolture |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit · Plotly |
| Scraping | curl_cffi (Chrome TLS impersonation) · ThreadPoolExecutor |
| Database | MongoDB Atlas (5-year data retention) |
| Hosting | Streamlit Community Cloud |
| Language | Python 3.11+ |

---

## 🔄 How Scraping Works

1. Click **🚀 Start Scraping** on the Auto-Scrape page
2. The scraper hits Woolworths and Coles search APIs using 8 parallel workers
3. Each result is validated — irrelevant products (bags, toys, etc.) and implausible prices ($0.50–$150 range check) are filtered out
4. New price records are batch-inserted into MongoDB with a timestamp
5. All dashboards update automatically with the new data

Run it weekly to build a rich historical dataset — trend charts, biggest movers, and suburb comparisons all become more meaningful over time.

---

## 🌐 Live App

👉 **[oz-price-tracker.streamlit.app](https://oz-price-tracker.streamlit.app/)**

Free to use. No account needed. Read-only dashboards — scraping is triggered manually.

---

<div align="center">

Built for Brisbane shoppers · 118 items · 17 stores · 5-year data retention · 100% automated

</div>
