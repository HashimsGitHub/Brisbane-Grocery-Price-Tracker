import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

NEON   = "#00EEFF"
GREEN  = "#00C853"
RED    = "#FF1744"
AMBER  = "#FFD700"
BG     = "rgba(0,0,0,0)"


def show(db):
    st.title("🏠 Dashboard")
    st.caption("Automatically scraped from Woolworths & Coles stores across Brisbane")

    prices = db["prices"]

    # ── Top-level metrics ────────────────────────────────────────────────────
    total        = prices.count_documents({})
    week_ago     = datetime.utcnow() - timedelta(days=7)
    this_week    = prices.count_documents({"submitted_at": {"$gte": week_ago}})
    unique_items = len(prices.distinct("item_name"))
    unique_stores = len(prices.distinct("store"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total prices tracked", f"{total:,}")
    c2.metric("Added this week",      f"{this_week:,}")
    c3.metric("Items tracked",        unique_items)
    c4.metric("Stores covered",       unique_stores)

    st.markdown("---")

    # ── Biggest movers ───────────────────────────────────────────────────────
    st.subheader("📈 Biggest Price Movers — This Week vs Last Week")
    st.caption("Comparing average scraped price this week against the prior week across all Brisbane stores.")

    two_weeks_ago = datetime.utcnow() - timedelta(days=14)

    pipeline = [
        {"$match": {"submitted_at": {"$gte": two_weeks_ago}, "source": "auto_scrape"}},
        {
            "$group": {
                "_id": {
                    "item": "$item_name",
                    "period": {
                        "$cond": [
                            {"$gte": ["$submitted_at", week_ago]},
                            "this_week",
                            "last_week",
                        ]
                    },
                },
                "avg_price": {"$avg": "$price"},
                "n":         {"$sum": 1},
            }
        },
        {
            "$group": {
                "_id": "$_id.item",
                "periods": {
                    "$push": {
                        "period": "$_id.period",
                        "avg":    "$avg_price",
                        "n":      "$n",
                    }
                },
            }
        },
    ]

    movers = []
    for doc in prices.aggregate(pipeline):
        p = {x["period"]: x["avg"] for x in doc["periods"]}
        if "this_week" in p and "last_week" in p and p["last_week"] > 0:
            change_pct = (p["this_week"] - p["last_week"]) / p["last_week"] * 100
            movers.append({
                "item":      doc["_id"],
                "last_week": round(p["last_week"], 2),
                "this_week": round(p["this_week"], 2),
                "change":    round(change_pct, 1),
            })

    if movers:
        df = (pd.DataFrame(movers)
                .sort_values("change", key=abs, ascending=False)
                .head(12))

        # Colour each bar: green = cheaper, red = more expensive
        bar_colors = [GREEN if c < 0 else RED for c in df["change"]]
        text_labels = [
            f"{'▲' if c > 0 else '▼'} {abs(c):.1f}%  (${tw:.2f})"
            for c, tw in zip(df["change"], df["this_week"])
        ]

        fig = go.Figure(go.Bar(
            x=df["change"],
            y=df["item"],
            orientation="h",
            marker_color=bar_colors,
            text=text_labels,
            textposition="outside",
            textfont=dict(color=NEON, size=11),
            customdata=list(zip(df["last_week"], df["this_week"])),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Last week: $%{customdata[0]:.2f}<br>"
                "This week: $%{customdata[1]:.2f}<br>"
                "Change: %{x:+.1f}%<extra></extra>"
            ),
        ))

        # Vertical zero line
        fig.add_vline(x=0, line_color=NEON, line_width=1, opacity=0.4)

        fig.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG,
            font=dict(color=NEON),
            height=max(320, len(df) * 42 + 60),
            margin=dict(l=10, r=160, t=20, b=20),
            xaxis=dict(
                title="% change",
                ticksuffix="%",
                gridcolor="rgba(0,238,255,0.08)",
                zerolinecolor=NEON,
                tickfont=dict(color=NEON),
            ),
            yaxis=dict(
                tickfont=dict(color=NEON),
                categoryorder="total ascending",
            ),
        )

        st.plotly_chart(fig, width="stretch")

        # Mini summary below chart
        rises  = df[df["change"] > 0]
        falls  = df[df["change"] < 0]
        col_r, col_f = st.columns(2)
        with col_r:
            if not rises.empty:
                top = rises.iloc[-1]
                st.markdown(
                    f'<span style="color:{RED}">⬆ Biggest rise: </span>'
                    f'<span style="color:{NEON}"><b>{top["item"]}</b> +{top["change"]:.1f}%</span>',
                    unsafe_allow_html=True,
                )
        with col_f:
            if not falls.empty:
                top = falls.iloc[0]
                st.markdown(
                    f'<span style="color:{GREEN}">⬇ Biggest drop: </span>'
                    f'<span style="color:{NEON}"><b>{top["item"]}</b> {top["change"]:.1f}%</span>',
                    unsafe_allow_html=True,
                )
    else:
        st.info(
            "Not enough data yet — run Auto-Scrape for at least two consecutive weeks "
            "to see price movement comparisons."
        )

    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    # ── Most tracked items ───────────────────────────────────────────────────
    with col_left:
        st.subheader("📦 Most Tracked Items")
        pipeline2 = [
            {"$group": {"_id": "$item_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        top_items = list(prices.aggregate(pipeline2))
        if top_items:
            df_items = (pd.DataFrame(top_items)
                          .rename(columns={"_id": "Item", "count": "Price records"}))
            fig2 = px.bar(
                df_items, x="Price records", y="Item",
                orientation="h", height=340,
                color="Price records",
                color_continuous_scale=[[0, "#003344"], [1, NEON]],
            )
            fig2.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"},
                plot_bgcolor=BG, paper_bgcolor=BG,
                font=dict(color=NEON),
            )
            fig2.update_traces(
                texttemplate="%{x:,}",
                textposition="outside",
                textfont=dict(color=NEON),
            )
            st.plotly_chart(fig2, width="stretch")
        else:
            st.info("No data yet — run Auto-Scrape to populate.")

    # ── Cheapest vs dearest store this week ─────────────────────────────────
    with col_right:
        st.subheader("🏆 Store Avg Price This Week")
        pipeline3 = [
            {"$match": {"submitted_at": {"$gte": week_ago}}},
            {"$group": {"_id": "$store", "avg": {"$avg": "$price"}, "n": {"$sum": 1}}},
            {"$sort": {"avg": 1}},
        ]
        store_docs = list(prices.aggregate(pipeline3))
        if store_docs:
            df_stores = pd.DataFrame([
                {"Store": d["_id"], "Avg ($)": round(d["avg"], 2), "Records": d["n"]}
                for d in store_docs
            ])
            bar_cols = [GREEN if "Woolworths" in s else RED if "Coles" in s else NEON
                        for s in df_stores["Store"]]
            fig3 = go.Figure(go.Bar(
                x=df_stores["Store"],
                y=df_stores["Avg ($)"],
                marker_color=bar_cols,
                text=df_stores["Avg ($)"].apply(lambda x: f"${x:.2f}"),
                textposition="outside",
                textfont=dict(color=NEON),
                hovertemplate="<b>%{x}</b><br>Avg: $%{y:.2f}<extra></extra>",
            ))
            fig3.update_layout(
                plot_bgcolor=BG, paper_bgcolor=BG,
                font=dict(color=NEON),
                margin=dict(l=0, r=0, t=10, b=0),
                height=340,
                yaxis=dict(tickprefix="$", gridcolor="rgba(0,238,255,0.08)",
                           tickfont=dict(color=NEON)),
                xaxis=dict(tickfont=dict(color=NEON)),
            )
            st.plotly_chart(fig3, width="stretch")
        else:
            st.info("No data this week yet.")

    st.markdown("---")

    # ── Suburb activity map ──────────────────────────────────────────────────
    st.subheader("🗺️ Price Activity by Suburb")
    pipeline4 = [
        {"$match": {"lat": {"$exists": True}}},
        {
            "$group": {
                "_id": {"suburb": "$suburb", "lat": "$lat", "lng": "$lng"},
                "count":     {"$sum": 1},
                "avg_price": {"$avg": "$price"},
            }
        },
    ]
    geo_docs = list(prices.aggregate(pipeline4))
    if geo_docs:
        geo_df = pd.DataFrame([{
            "suburb":    d["_id"]["suburb"],
            "lat":       d["_id"]["lat"],
            "lon":       d["_id"]["lng"],
            "count":     d["count"],
            "avg_price": round(d["avg_price"], 2),
        } for d in geo_docs])
        st.map(geo_df, size="count", color="#1D9E75")
    else:
        st.info("Map populates once scraped prices include location data.")

    # ── Recent prices feed ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🕐 Recently Scraped Prices")
    recent = list(
        prices.find({}, {"_id": 0, "user_hash": 0, "location": 0,
                         "store_id": 0, "source": 0})
               .sort("submitted_at", -1).limit(20)
    )
    if recent:
        df_recent = pd.DataFrame(recent)
        df_recent["submitted_at"] = (pd.to_datetime(df_recent["submitted_at"])
                                       .dt.strftime("%d %b %Y %H:%M"))
        df_recent["price"] = df_recent["price"].apply(lambda x: f"${x:.2f}")
        st.dataframe(
            df_recent.rename(columns={
                "item_name":   "Item",
                "price":       "Price",
                "unit":        "Unit",
                "store":       "Store",
                "suburb":      "Suburb",
                "state":       "State",
                "submitted_at":"Scraped At",
            }),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No data yet — run Auto-Scrape to populate.")
