<div align="center">

# 🛒 Aussie Price Tracker

### *Real prices. Real suburbs. Real savings.*

**Track grocery prices across Brisbane — powered by the community and live supermarket data.**

[![Live App](https://img.shields.io/badge/🚀%20Live%20App-oz--price--tracker.streamlit.app-00EEFF?style=for-the-badge&labelColor=000000)](https://oz-price-tracker.streamlit.app/)
[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-00C853?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)

---

</div>

## 💡 What is this?

Aussie Price Tracker is a **free, community-driven price comparison tool** built for Brisbane shoppers.

Tired of not knowing whether Woolworths or Coles has cheaper milk this week? Wondering if your suburb pays more than the next one over? This app gives you the answers — in real time, for free, no account needed.

Prices come from **two sources**:
- 🤝 **You and your neighbours** — anyone can submit a price they've spotted in-store
- 🤖 **Automatic scraping** — the app periodically fetches live prices directly from Woolworths and Coles

---

## ✨ Features

### 🏠 Dashboard
Your live snapshot of what's happening right now across Brisbane:
- See which items have had the **biggest price jumps** this week
- Browse the **most tracked groceries** across the community
- View a **suburb heat map** showing where people are submitting prices
- Scroll through the **latest price submissions** as they come in

### 📝 Submit a Price
Spotted a great deal — or a rip-off? **Tell the community in seconds.**
- Pick from a list of common items or type your own
- Select your store and Brisbane suburb
- Anonymous — no account, no sign-up, no tracking

### 🤖 Auto-Scrape *(new!)*
Can't be bothered submitting manually? Neither can we.
- Automatically fetches current prices from **Woolworths** and **Coles** across Brisbane
- Covers 7 Woolworths stores and 10 Coles stores from CBD to Caboolture
- Runs on demand — just hit the button and watch it go
- All auto-scraped prices are clearly labelled so you always know the source

### 📈 Price History
Has that item been getting more expensive over time?
- Line charts showing **price trends** for any item
- Compare how prices have moved week by week
- Spot seasonal patterns and creeping inflation before it hits your wallet

### 🗺️ Suburb Compare
Does your suburb pay more than the one down the road?
- Side-by-side comparison of average prices between **any two Brisbane suburbs**
- Find out if it's worth the drive to a different area

### 🚨 Price Alerts
Be the first to know when something spikes.
- Automatically flags items with the **biggest price rises** in the past week
- Never get caught off guard at the checkout again

### 📊 Store Rankings
The big question: **which supermarket is actually cheapest?**
- Overall average price ranking across all tracked stores
- Per-item price heatmap — see exactly where each store wins or loses
- Updated every time new prices come in

---

## 🛍️ Items We Track

| Category | Items |
|----------|-------|
| 🥛 Dairy | Full Cream Milk 2L, Free Range Eggs 12pk, Cheddar Cheese 500g, Butter 500g |
| 🍞 Bakery | White Bread Loaf |
| 🥩 Meat | Chicken Breast, Beef Mince 500g |
| 🥦 Produce | Bananas, Tomatoes, Potatoes 2kg, Carrots 1kg |
| 🍚 Pantry | White Rice 1kg, Pasta 500g, Tinned Tomatoes 400g, Olive Oil 750ml |
| 🥤 Drinks | Orange Juice 2L, Coca-Cola 1.25L |
| ⛽ Fuel | Unleaded Petrol, Premium Petrol, Diesel |

---

## 🗺️ Brisbane Coverage

We cover suburbs from the CBD all the way out to the fringe — including:

> Brisbane CBD · South Brisbane · Fortitude Valley · West End · Toowong · St Lucia · Indooroopilly · Paddington · Chermside · Aspley · Kedron · Nundah · Sandgate · Redcliffe · Mount Gravatt · Sunnybank · Carindale · Strathpine · Caboolture · and more

---

## 🙋 How to Contribute a Price

1. Open the app at **[oz-price-tracker.streamlit.app](https://oz-price-tracker.streamlit.app/)**
2. Click **📝 Submit a Price** in the sidebar
3. Choose your item, enter the price you saw, pick your store and suburb
4. Hit **Submit** — that's it. Takes about 10 seconds.

Your submission is **completely anonymous**. We store a one-way hash to prevent duplicate submissions within an hour — that's all. No name, no email, no account.

---

## 📊 Data Quality

We take data quality seriously:

- ✅ **Canonical item list** — all submissions map to standardised item names so comparisons are apples-to-apples
- ✅ **Fuzzy matching** — typos and alternate names (e.g. "coke" → "Coca-Cola 1.25L") are automatically corrected
- ✅ **Duplicate prevention** — the same user can't submit the same item more than once per hour
- ✅ **Smart scraping** — auto-scraped prices use keyword matching and a blocklist to reject irrelevant products (shopping bags, toys, etc.)
- ✅ **Price sanity checks** — prices outside a plausible range ($0.50–$150) are automatically rejected
- ✅ **5-year retention** — price history is kept for 5 years so you can see long-term trends

---

## 🌐 Live App

👉 **[oz-price-tracker.streamlit.app](https://oz-price-tracker.streamlit.app/)**

Free to use. No account needed. Open to all Brisbane residents.

---

<div align="center">

Built with ❤️ for Brisbane shoppers · Data retained for 5 years · 100% free

</div>
