import streamlit as st

st.set_page_config(
    page_title="Aussie Price Tracker",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from db import get_db
from pages_app import dashboard, submit_price, price_history, suburb_compare, price_alerts, store_rankings

# ── Sidebar navigation ──────────────────────────────────────────────────────
st.sidebar.title("🛒 Aussie Price Tracker")
st.sidebar.caption("Crowdsourced grocery & fuel prices")

pages = {
    "🏠 Dashboard":        dashboard.show,
    "📝 Submit a Price":   submit_price.show,
    "📈 Price History":    price_history.show,
    "🗺️ Suburb Compare":  suburb_compare.show,
    "🚨 Price Alerts":     price_alerts.show,
    "📊 Store Rankings":   store_rankings.show,
}

selection = st.sidebar.radio("Navigate", list(pages.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("Data contributed by the community.\nPrices auto-expire after 6 months.")

# ── Render selected page ─────────────────────────────────────────────────────
db = get_db()
pages[selection](db)
