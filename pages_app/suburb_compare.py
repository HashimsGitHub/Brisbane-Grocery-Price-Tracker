import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def show(db):
    st.title("🗺️ Suburb Compare")
    st.caption("Compare average prices between two suburbs side by side.")

    prices = db["prices"]
    all_suburbs = sorted(prices.distinct("suburb"))

    if len(all_suburbs) < 2:
        st.info("Need data from at least 2 suburbs to compare. Submit more prices!")
        return

    col1, col2 = st.columns(2)
    with col1:
        suburb_a = st.selectbox("Suburb A", all_suburbs, index=0)
    with col2:
        default_b = 1 if len(all_suburbs) > 1 else 0
        suburb_b = st.selectbox("Suburb B", all_suburbs, index=default_b)

    if suburb_a == suburb_b:
        st.warning("Please select two different suburbs.")
        return

    # ── Aggregation: avg price per item per suburb ───────────────────────────
    pipeline = [
        {"$match": {"suburb": {"$in": [suburb_a, suburb_b]}}},
        {
            "$group": {
                "_id": {"item": "$item_name", "suburb": "$suburb"},
                "avg_price": {"$avg": "$price"},
                "count": {"$sum": 1},
            }
        },
    ]
    rows = list(prices.aggregate(pipeline))

    if not rows:
        st.info("No data for these suburbs yet.")
        return

    df = pd.DataFrame([{
        "item": r["_id"]["item"],
        "suburb": r["_id"]["suburb"],
        "avg_price": round(r["avg_price"], 2),
        "count": r["count"],
    } for r in rows])

    # Pivot to wide format
    pivot = df.pivot_table(index="item", columns="suburb", values="avg_price").reset_index()
    pivot.columns.name = None

    # Only keep items present in both
    if suburb_a in pivot.columns and suburb_b in pivot.columns:
        pivot = pivot.dropna(subset=[suburb_a, suburb_b])
    else:
        st.info("No common items found between these two suburbs yet.")
        return

    pivot["diff"] = pivot[suburb_b] - pivot[suburb_a]
    pivot["diff_pct"] = (pivot["diff"] / pivot[suburb_a] * 100).round(1)
    pivot = pivot.sort_values("diff_pct", ascending=False)

    # ── Summary ──────────────────────────────────────────────────────────────
    cheaper = suburb_a if pivot["diff"].mean() > 0 else suburb_b
    avg_diff = abs(pivot["diff_pct"].mean())

    st.info(f"On average, **{cheaper}** is **{avg_diff:.1f}% cheaper** across {len(pivot)} common items.")

    # ── Grouped bar chart ─────────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=suburb_a, x=pivot["item"], y=pivot[suburb_a],
        marker_color="#1D9E75",
    ))
    fig.add_trace(go.Bar(
        name=suburb_b, x=pivot["item"], y=pivot[suburb_b],
        marker_color="#378ADD",
    ))
    fig.update_layout(
        barmode="group",
        xaxis_tickangle=-35,
        yaxis_title="Avg price ($)",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#00EEFF"),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0),
        height=400,
    )
    fig.update_yaxes(tickprefix="$", gridcolor="rgba(128,128,128,0.1)")
    st.plotly_chart(fig, width="stretch")

    # ── Table ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Item-by-item comparison")

    display = pivot.copy()
    display[suburb_a] = display[suburb_a].apply(lambda x: f"${x:.2f}")
    display[suburb_b] = display[suburb_b].apply(lambda x: f"${x:.2f}")
    display["Difference"] = display["diff_pct"].apply(
        lambda x: f"🔺 {suburb_b} +{x:.1f}%" if x > 0 else f"🔻 {suburb_a} +{abs(x):.1f}%"
    )
    display = display.rename(columns={"item": "Item"})
    st.dataframe(
        display[["Item", suburb_a, suburb_b, "Difference"]],
        width="stretch", hide_index=True,
    )
