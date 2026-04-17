import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def show(db):
    st.title("🏠 Dashboard")
    st.caption("Live snapshot of community-submitted prices")

    prices = db["prices"]

    # ── Top-level metrics ────────────────────────────────────────────────────
    total = prices.count_documents({})
    week_ago = datetime.utcnow() - timedelta(days=7)
    this_week = prices.count_documents({"submitted_at": {"$gte": week_ago}})
    unique_items = len(prices.distinct("item_name"))
    unique_suburbs = len(prices.distinct("suburb"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total submissions", f"{total:,}")
    c2.metric("This week", f"{this_week:,}")
    c3.metric("Items tracked", unique_items)
    c4.metric("Suburbs covered", unique_suburbs)

    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    # ── Biggest price movers (last 7 days vs prior 7 days) ───────────────────
    with col_left:
        st.subheader("🚨 Biggest movers this week")
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)

        pipeline = [
            {"$match": {"submitted_at": {"$gte": two_weeks_ago}}},
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
                }
            },
            {
                "$group": {
                    "_id": "$_id.item",
                    "prices": {
                        "$push": {
                            "period": "$_id.period",
                            "avg": "$avg_price",
                        }
                    },
                }
            },
        ]

        movers = []
        for doc in prices.aggregate(pipeline):
            p = {x["period"]: x["avg"] for x in doc["prices"]}
            if "this_week" in p and "last_week" in p and p["last_week"] > 0:
                change_pct = (p["this_week"] - p["last_week"]) / p["last_week"] * 100
                movers.append({
                    "Item": doc["_id"],
                    "Last week": f"${p['last_week']:.2f}",
                    "This week": f"${p['this_week']:.2f}",
                    "Change": round(change_pct, 1),
                })

        if movers:
            movers_df = pd.DataFrame(movers).sort_values("Change", ascending=False).head(8)
            movers_df["Change %"] = movers_df["Change"].apply(
                lambda x: f"🔺 +{x:.1f}%" if x > 0 else f"🔻 {x:.1f}%"
            )
            st.dataframe(
                movers_df[["Item", "Last week", "This week", "Change %"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Not enough data yet — submit some prices to see movers!")

    # ── Most submitted items ─────────────────────────────────────────────────
    with col_right:
        st.subheader("📦 Most tracked items")
        pipeline2 = [
            {"$group": {"_id": "$item_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        top_items = list(prices.aggregate(pipeline2))
        if top_items:
            df_items = pd.DataFrame(top_items).rename(columns={"_id": "Item", "count": "Submissions"})
            fig = px.bar(
                df_items,
                x="Submissions",
                y="Item",
                orientation="h",
                height=320,
                color="Submissions",
                color_continuous_scale="teal",
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"},
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet!")

    st.markdown("---")

    # ── Suburb activity map ──────────────────────────────────────────────────
    st.subheader("🗺️ Submission activity by suburb")

    pipeline3 = [
        {"$match": {"lat": {"$exists": True}}},
        {
            "$group": {
                "_id": {"suburb": "$suburb", "lat": "$lat", "lng": "$lng"},
                "count": {"$sum": 1},
                "avg_price": {"$avg": "$price"},
            }
        },
    ]
    geo_docs = list(prices.aggregate(pipeline3))

    if geo_docs:
        geo_df = pd.DataFrame([{
            "suburb": d["_id"]["suburb"],
            "lat": d["_id"]["lat"],
            "lon": d["_id"]["lng"],
            "submissions": d["count"],
            "avg_price": round(d["avg_price"], 2),
        } for d in geo_docs])
        st.map(geo_df, size="submissions", color="#1D9E75")
    else:
        st.info("Suburb map will populate once prices with location data are submitted.")

    # ── Recent submissions feed ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🕐 Recent submissions")
    recent = list(prices.find({}, {"_id": 0, "user_hash": 0, "location": 0})
                  .sort("submitted_at", -1).limit(20))
    if recent:
        df_recent = pd.DataFrame(recent)
        df_recent["submitted_at"] = pd.to_datetime(df_recent["submitted_at"]).dt.strftime("%d %b %Y %H:%M")
        df_recent["price"] = df_recent["price"].apply(lambda x: f"${x:.2f}")
        st.dataframe(
            df_recent.rename(columns={
                "item_name": "Item", "price": "Price", "unit": "Unit",
                "store": "Store", "suburb": "Suburb", "state": "State",
                "submitted_at": "Submitted",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No submissions yet — be the first!")
