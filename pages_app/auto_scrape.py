"""
pages_app/auto_scrape.py  –  Auto-Scrape Prices page
─────────────────────────────────────────────────────
Lets an admin (or any user) trigger a background scrape of Woolworths &
Coles Brisbane prices for all canonical items in the database.

Features
  • Select which retailers / suburbs to include
  • Live progress bar + log during scraping
  • Summary table of results once complete
  • Toggle to show/hide auto-scraped prices on other pages
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
import pandas as pd

from scraper import (
    run_scrape,
    WOOLWORTHS_SAMPLE_STORES,
    COLES_BRISBANE_STORES,
)


def show(db):
    st.title("🤖 Auto-Scrape Prices")
    st.caption(
        "Automatically fetch current prices from **Woolworths** and **Coles** "
        "for all tracked items across Brisbane stores. "
        "Results are saved to the database just like community submissions."
    )

    # ── Info banner ────────────────────────────────────────────────────────────
    with st.expander("ℹ️  How it works", expanded=False):
        st.markdown(
            """
- Prices are fetched from the **Woolworths** and **Coles** online catalogues via their search APIs.
- Only items already in the database are scraped (same canonical item list used across the app).
- **Fuel prices** are excluded (they change hourly and require a dedicated source like FuelWatch).
- A scrape run is **deduplicated**: if the same store + item was scraped within the last 6 hours, it is skipped.
- All auto-scraped records are tagged `source = auto_scrape` so they can be filtered separately.
- Please don't run more than once every few hours to avoid hammering the retailers' servers.
            """
        )

    st.divider()

    # ── Store selection ────────────────────────────────────────────────────────
    st.subheader("🏪 Select Stores to Scrape")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Woolworths Brisbane stores**")
        woolies_options = {f"Woolworths – {suburb}": (sid, suburb) for sid, suburb in WOOLWORTHS_SAMPLE_STORES}
        woolies_selected = st.multiselect(
            "Woolworths stores",
            options=list(woolies_options.keys()),
            default=list(woolies_options.keys()),
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**Coles Brisbane stores**")
        coles_options = {f"Coles – {suburb}": (sid, suburb) for sid, suburb in COLES_BRISBANE_STORES}
        coles_selected = st.multiselect(
            "Coles stores",
            options=list(coles_options.keys()),
            default=list(coles_options.keys())[:5],   # default to first 5 so it's not overwhelming
            label_visibility="collapsed",
        )

    selected_stores = []
    for label in woolies_selected:
        sid, suburb = woolies_options[label]
        selected_stores.append({"retailer": "woolworths", "store_id": sid, "suburb": suburb})
    for label in coles_selected:
        sid, suburb = coles_options[label]
        selected_stores.append({"retailer": "coles", "store_id": sid, "suburb": suburb})

    # Item count preview
    items = list(db["items"].find({"category": {"$ne": "Fuel"}}, {"name": 1, "_id": 0}))
    n_items = len(items)
    n_combinations = n_items * len(selected_stores)
    est_minutes = round(n_combinations * 1.0 / 60, 1)

    st.info(
        f"**{n_items}** items × **{len(selected_stores)}** stores = "
        f"**{n_combinations}** requests  (~{est_minutes} min at ~1 req/s)"
    )

    # ── Last scrape status ─────────────────────────────────────────────────────
    last_scrape = db["prices"].find_one(
        {"source": "auto_scrape"},
        sort=[("submitted_at", -1)],
    )
    if last_scrape:
        ts = last_scrape["submitted_at"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - ts
        age_str = _format_age(age)
        st.success(f"✅ Last scrape: **{age_str} ago** ({ts.strftime('%d %b %Y %H:%M')} UTC)")
    else:
        st.warning("No auto-scraped data in the database yet.")

    st.divider()

    # ── Trigger button ─────────────────────────────────────────────────────────
    if not selected_stores:
        st.error("Please select at least one store.")
        return

    run_btn = st.button(
        f"🚀 Start Scraping ({n_combinations} requests)",
        type="primary",
        use_container_width=True,
        disabled=(n_combinations == 0),
    )

    if run_btn:
        _run_scrape_with_ui(db, selected_stores)

    # ── Recent auto-scraped prices table ───────────────────────────────────────
    st.divider()
    st.subheader("📋 Recent Auto-Scraped Prices")

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = list(
        db["prices"].find(
            {"source": "auto_scrape", "submitted_at": {"$gte": since}},
            {"_id": 0, "item_name": 1, "price": 1, "unit": 1, "store": 1, "suburb": 1, "submitted_at": 1},
        ).sort("submitted_at", -1).limit(200)
    )

    if recent:
        df = pd.DataFrame(recent)
        df["submitted_at"] = pd.to_datetime(df["submitted_at"]).dt.strftime("%d %b %H:%M")
        df = df.rename(columns={
            "item_name": "Item", "price": "Price ($)", "unit": "Unit",
            "store": "Store", "suburb": "Suburb", "submitted_at": "Scraped At",
        })
        df["Price ($)"] = df["Price ($)"].map("${:.2f}".format)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Showing last 200 auto-scraped records (past 24 h). Total: {len(recent)}")
    else:
        st.info("No auto-scraped prices in the last 24 hours.")

    # ── Manage / clear auto-scraped data ──────────────────────────────────────
    with st.expander("🗑️  Manage auto-scraped data"):
        total_auto = db["prices"].count_documents({"source": "auto_scrape"})
        st.write(f"Total auto-scraped records in database: **{total_auto}**")
        if st.button("Delete all auto-scraped records", type="secondary"):
            db["prices"].delete_many({"source": "auto_scrape"})
            st.success("All auto-scraped records deleted.")
            st.rerun()


# ── Private helpers ────────────────────────────────────────────────────────────

def _run_scrape_with_ui(db, selected_stores):
    """Run the scraper with a live Streamlit progress UI."""
    progress_bar = st.progress(0, text="Starting scrape…")
    log_area = st.empty()
    log_lines = []

    def progress_callback(current, total, message):
        pct = int(current / total * 100)
        progress_bar.progress(pct, text=f"{message} ({current}/{total})")
        log_lines.append(f"`{message}`")
        if len(log_lines) > 12:
            log_lines.pop(0)
        log_area.markdown("\n\n".join(log_lines[-8:]))

    with st.spinner("Scraping in progress…"):
        try:
            results = run_scrape(db, progress_callback=progress_callback, stores=selected_stores)
        except Exception as e:
            st.error(f"Scrape failed: {e}")
            return

    progress_bar.progress(100, text="Done!")
    log_area.empty()

    # Results summary
    st.balloons()
    st.success(
        f"✅ Scrape complete!  "
        f"**{results['inserted']}** new prices saved, "
        f"**{results['skipped']}** skipped (duplicate / no match), "
        f"**{results['errors']}** errors."
    )

    if results["items_scraped"]:
        with st.expander(f"View {len(results['items_scraped'])} new records"):
            for line in results["items_scraped"]:
                st.write(f"• {line}")


def _format_age(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s"
    if total_seconds < 3600:
        return f"{total_seconds // 60}m"
    if total_seconds < 86400:
        return f"{total_seconds // 3600}h {(total_seconds % 3600) // 60}m"
    return f"{total_seconds // 86400}d"
