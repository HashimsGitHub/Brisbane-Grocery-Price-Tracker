<div align="center">

# 📊 Brisbane Grocery Price Tracker

### *Live prices. Zero effort. Real savings.*

**Automatically tracks grocery prices across Brisbane — scraped daily from Woolworths & Coles.**

[![Live App](https://img.shields.io/badge/🚀%20Live%20App-oz--price--tracker.streamlit.app-00EEFF?style=for-the-badge&labelColor=000000)](https://oz-price-tracker.streamlit.app/)
[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-00C853?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)

---

</div>

## 💡 What is this?

Brisbane Grocery Price Tracker **automatically scrapes live grocery prices** from Woolworths and Coles stores across Brisbane and turns them into an easy-to-read dashboard.

No manual entry. No crowdsourcing. Just real prices, updated on demand, across 17 Brisbane stores.

---

## ✨ Features

### 🏠 Dashboard
Your live snapshot of Brisbane grocery prices:
- **Biggest Price Movers** — visual chart showing which items rose or fell most this week vs last week, sourced directly from scraped data
- **Store Average Prices** — see at a glance which supermarket is cheaper overall
- **Most Tracked Items** — the groceries with the most price records
- **Recently Scraped Prices** — a live feed of the latest data collected

### 🤖 Auto-Scrape
The engine that powers everything:
- Fetches current prices from **Woolworths** and **Coles** using their own search APIs
- Covers **7 Woolworths** and **10 Coles** stores across Brisbane — CBD to Caboolture
- Uses Chrome TLS impersonation (`curl_cffi`) to bypass bot detection
- Deduplicates automatically — won't re-scrape the same store/item within 6 hours
- Run on demand with a single button click

### 📈 Price History
How has that item trended over time?
- Line chart showing price trends for any tracked item
- Filter by store and date range
- Spot long-term inflation or seasonal price changes

### 🗺️ Suburb Compare
Does your suburb pay more?
- Side-by-side average price comparison between any two Brisbane suburbs
- Useful for seeing whether store location affects pricing

### 📊 Store Rankings
Which supermarket actually wins?
- Overall average price ranking across all stores
- Per-item price heatmap — green = cheaper, red = more expensive
- Updated with every scrape run

---

## 🛍️ Items Tracked

118 common groceries across 13 categories:

| Category | Examples |
|---|---|
| 🥛 Dairy & Eggs | Full Cream Milk, Greek Yoghurt, Eggs, Butter, Cheese |
| 🍞 Bakery | White Bread, Sourdough, Croissants, Plain Flour |
| 🥩 Meat & Seafood | Chicken Breast, Beef Mince, Salmon, Bacon, Prawns |
| 🥦 Produce | Bananas, Avocado, Broccoli, Tomatoes, Mushrooms |
| 🍚 Pantry | Vegemite, Milo, Weet-Bix, Pasta, Olive Oil, Honey |
| 🧊 Frozen | Frozen Peas, Chips, Ice Cream, Pizza |
| 🍫 Snacks | Tim Tams, Shapes, Chips, Chocolate Block |
| 🥤 Drinks | OJ, Coke, Beer, Wine, Sparkling Water |
| 🏠 Household | Toilet Paper, Dishwashing Liquid, Laundry Powder |
| 💊 Health | Sunscreen, Paracetamol, Shampoo, Toothpaste |
| ⛽ Fuel | Unleaded, Premium, Diesel |

---

## 🗺️ Brisbane Stores Covered

**Woolworths:** Brisbane CBD · Toowong · Chermside · Mount Gravatt · Sunnybank · Redcliffe · Caboolture

**Coles:** Brisbane CBD · South Brisbane · Toowong · Chermside · Mount Gravatt · Indooroopilly · Sunnybank · Nundah · Strathpine · Caboolture

---

## 🌐 Live App

👉 **[oz-price-tracker.streamlit.app](https://oz-price-tracker.streamlit.app/)**

Free to use. No account needed.

---

<div align="center">

Built for Brisbane shoppers · Prices retained for 5 years · 100% automated

</div>
