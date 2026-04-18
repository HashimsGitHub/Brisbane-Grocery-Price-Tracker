import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def show(db):
    st.title("🚨 Price Alerts")
    st.caption("Items with significant price rises in the past 7 days.")

    prices = db["prices"]

    threshold = st.slider("Alert threshold (%)", min_value=3, max_value=30, value=10, step=1)
    min_submissions = st.slider("Minimum submissions needed", min_value=2, max_value=10, value=2)

    week_ago      = datetime.utcnow() - timedelta(days=7)
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
                            "current",
                            "previous",
                        ]
                    },
                },
                "avg_price": {"$avg": "$price"},
                "count":     {"$sum": 1},
            }
        },
        {
            "$group": {
                "_id": "$_id.item",
                "data": {
                    "$push": {
                        "period": "$_id.period",
                        "avg":    "$avg_price",
                        "count":  "$count",
                    }
                },
            }
        },
    ]

    alerts = []
    for doc in prices.aggregate(pipeline):
        by_period = {x["period"]: x for x in doc["data"]}
        if "current" not in by_period or "previous" not in by_period:
            continue
        cur  = by_period["current"]
        prev = by_period["previous"]
        if cur["count"] < min_submissions:
            continue
        change_pct = (cur["avg"] - prev["avg"]) / prev["avg"] * 100
        if change_pct >= threshold:
            alerts.append({
                "Item":          doc["_id"],
                "Previous avg":  round(prev["avg"], 2),
                "Current avg":   round(cur["avg"], 2),
                "Change %":      round(change_pct, 1),
                "Submissions":   cur["count"],
            })

    if not alerts:
        st.success(f"No items have risen more than {threshold}% in the last 7 days. 🎉")
        return

    alerts_df = pd.DataFrame(alerts).sort_values("Change %", ascending=False)

    # ── Metrics ───────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Items flagged", len(alerts_df))
    c2.metric("Biggest rise",  f"{alerts_df['Change %'].max():.1f}%")
    c3.metric("Avg rise",      f"{alerts_df['Change %'].mean():.1f}%")

    # ── Chart ─────────────────────────────────────────────────────────────────
    fig = px.bar(
        alerts_df.head(12),
        x="Change %", y="Item", orientation="h",
        color="Change %", color_continuous_scale="reds",
        height=max(300, len(alerts_df) * 36),
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#00EEFF"),
        coloraxis_showscale=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=0, r=0, t=10, b=0),
    )
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(fig, width="stretch")

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    display = alerts_df.copy()
    display["Previous avg"] = display["Previous avg"].apply(lambda x: f"${x:.2f}")
    display["Current avg"]  = display["Current avg"].apply(lambda x: f"${x:.2f}")
    display["Change %"]     = display["Change %"].apply(lambda x: f"🔺 +{x:.1f}%")
    st.dataframe(display, width="stretch", hide_index=True)
