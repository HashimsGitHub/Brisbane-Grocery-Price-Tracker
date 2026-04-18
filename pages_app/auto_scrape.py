"""
pages_app/auto_scrape.py  –  Auto-Scrape Prices page
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
import pandas as pd

from scraper import run_scrape, WOOLWORTHS_SAMPLE_STORES, COLES_BRISBANE_STORES


def show(db):
    st.title("🤖 Auto-Scrape Prices")
    st.caption(
        "Automatically fetch current prices from **Woolworths** and **Coles** "
        "for all tracked items across Brisbane stores."
    )

    st.divider()

    # ── Store selection ────────────────────────────────────────────────────────
    st.subheader("🏪 Select Stores to Scrape")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Woolworths Brisbane**")
        woolies_opts = {f"Woolworths – {s}": (sid, s) for sid, s in WOOLWORTHS_SAMPLE_STORES}
        woolies_sel = st.multiselect(
            "wsel", list(woolies_opts.keys()), default=list(woolies_opts.keys()),
            label_visibility="collapsed",
        )

    with col2:
        st.markdown("**Coles Brisbane**")
        coles_opts = {f"Coles – {s}": (sid, s) for sid, s in COLES_BRISBANE_STORES}
        coles_sel = st.multiselect(
            "csel", list(coles_opts.keys()), default=list(coles_opts.keys())[:5],
            label_visibility="collapsed",
        )

    selected_stores = (
        [{"retailer": "woolworths", "store_id": sid, "suburb": sub}
         for k in woolies_sel for sid, sub in [woolies_opts[k]]]
        + [{"retailer": "coles", "store_id": sid, "suburb": sub}
           for k in coles_sel for sid, sub in [coles_opts[k]]]
    )

    items = list(db["items"].find({"category": {"$ne": "Fuel"}}, {"name": 1, "_id": 0}))
    n_items = len(items)
    n_req    = n_items * len(selected_stores)
    # 8 parallel workers (4 Woolworths + 4 Coles), ~0.5s avg per request
    est_min  = round(n_req * 0.5 / 8 / 60, 1)
    st.info(f"**{n_items}** items × **{len(selected_stores)}** stores = **{n_req}** requests (~{est_min} min with parallel scraping)")

    # ── Last scrape status ─────────────────────────────────────────────────────
    last = db["prices"].find_one({"source": "auto_scrape"}, sort=[("submitted_at", -1)])
    if last:
        ts = last["submitted_at"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - ts
        st.success(f"✅ Last scrape: **{_fmt_age(age)} ago** ({ts.strftime('%d %b %Y %H:%M')} UTC)")
    else:
        st.warning("No auto-scraped data yet.")

    st.divider()

    if not selected_stores:
        st.error("Select at least one store.")
        return

    if st.button(f"🚀 Start Scraping ({n_req} requests)", type="primary", width="stretch"):
        _run_with_ui(db, selected_stores)

    # ── Recent results table ───────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Recent Auto-Scraped Prices (last 24 h)")
    since  = datetime.utcnow() - timedelta(hours=24)
    recent = list(
        db["prices"].find(
            {"source": "auto_scrape", "submitted_at": {"$gte": since}},
            {"_id": 0, "item_name": 1, "price": 1, "unit": 1,
             "store": 1, "suburb": 1, "submitted_at": 1},
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
        st.dataframe(df, width="stretch", hide_index=True)
        st.caption(f"{len(recent)} records shown (max 200).")
    else:
        st.info("No auto-scraped prices in the last 24 hours.")

    with st.expander("🗑️  Manage auto-scraped data"):
        total_auto = db["prices"].count_documents({"source": "auto_scrape"})
        st.write(f"Total auto-scraped records: **{total_auto}**")
        if st.button("Delete ALL auto-scraped records", type="secondary"):
            db["prices"].delete_many({"source": "auto_scrape"})
            st.success("Deleted.")
            st.rerun()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_proxy() -> str | None:
    try:
        return st.secrets.get("SCRAPER_PROXY") or None
    except Exception:
        return None


def _run_with_ui(db, selected_stores):
    progress_bar = st.progress(0, text="Starting…")
    log_area     = st.empty()
    log_lines    = []

    def cb(current, total, msg):
        pct = int(current / total * 100)
        progress_bar.progress(pct, text=f"{msg} ({current}/{total})")
        log_lines.append(msg)
        log_area.markdown("\n\n".join(f"`{l}`" for l in log_lines[-10:]))

    with st.spinner("Scraping in progress…"):
        try:
            results = run_scrape(db, progress_callback=cb, stores=selected_stores)
        except Exception as e:
            st.error(f"Fatal error: {e}")
            return

    progress_bar.progress(100, text="Done!")
    log_area.empty()

    if results["inserted"] > 0:
        st.success(
            f"✅ Done!  **{results['inserted']}** new prices saved, "
            f"**{results['skipped']}** skipped, **{results['errors']}** errors."
        )
        st.balloons()
    elif results["errors"] > 0:
        st.error(
            f"**Scrape failed** — {results['errors']} errors, 0 prices saved. "
            "See details below."
        )
    else:
        st.warning(
            f"Finished but 0 prices saved. "
            f"Skipped: {results['skipped']}, Errors: {results['errors']}."
        )

    if results.get("error_messages"):
        with st.expander(f"⚠️  {len(results['error_messages'])} error(s)", expanded=True):
            for msg in results["error_messages"]:
                if msg.startswith("⛔") or msg.startswith("⚠️"):
                    st.warning(msg)
                else:
                    st.code(msg, language=None)

    if results["items_scraped"]:
        with st.expander(f"✅ {len(results['items_scraped'])} new records"):
            for line in results["items_scraped"]:
                st.write(f"• {line}")


def _fmt_age(delta: timedelta) -> str:
    s = int(delta.total_seconds())
    if s < 60:    return f"{s}s"
    if s < 3600:  return f"{s // 60}m"
    if s < 86400: return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d"
