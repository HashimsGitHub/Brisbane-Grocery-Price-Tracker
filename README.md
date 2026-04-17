# 🛒 Aussie Community Price Tracker

Crowdsourced grocery & fuel price tracker built with Streamlit + MongoDB Atlas.

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure MongoDB
Edit `.streamlit/secrets.toml` and replace `YOUR_PASSWORD`:
```toml
MONGO_URI = "mongodb+srv://hashim_db_user:YOUR_PASSWORD@clusterh.1k0zic7.mongodb.net/price_tracker?appName=ClusterH"
```

### 3. Seed suburbs (optional but recommended for the map)
```bash
MONGO_URI="your-uri-here" python seed_suburbs.py
```

### 4. Run locally
```bash
streamlit run app.py
```

---

## Deploy to Streamlit Community Cloud (free)

1. Push this repo to GitHub (`.gitignore` already excludes `secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Point to your repo + `app.py`
4. Under **Advanced settings → Secrets**, paste:
   ```
   MONGO_URI = "mongodb+srv://hashim_db_user:YOUR_PASSWORD@clusterh.1k0zic7.mongodb.net/price_tracker?appName=ClusterH"
   ```

---

## Project structure

```
price_tracker/
├── app.py                  # Entry point + sidebar nav
├── db.py                   # MongoDB connection, indexes, item seeding
├── requirements.txt
├── seed_suburbs.py         # One-time suburb lat/lng seeder
├── .gitignore
├── .streamlit/
│   └── secrets.toml        # ← your password goes here (not committed)
└── pages_app/
    ├── dashboard.py        # Home: metrics, movers, map, recent feed
    ├── submit_price.py     # Form: submit a price
    ├── price_history.py    # Trend chart per item
    ├── suburb_compare.py   # Side-by-side suburb comparison
    ├── price_alerts.py     # Items with big price rises
    └── store_rankings.py   # Cheapest store + heatmap
```

## MongoDB collections

| Collection | Purpose |
|---|---|
| `prices` | Every submitted price entry (TTL: 6 months) |
| `items` | Canonical item list with fuzzy-match aliases |
| `suburbs` | Suburb → lat/lng lookup for map |

## Key MongoDB features used
- **TTL index** on `prices.submitted_at` — auto-deletes entries after 6 months
- **Text index** on `prices.item_name` — full-text search
- **2dsphere index** on `prices.location` — geo queries
- **Aggregation pipeline** — all trend/comparison charts
