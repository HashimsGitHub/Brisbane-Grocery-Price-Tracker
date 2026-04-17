import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show(db):
    st.title("📊 Store Rankings")
    st.caption("Which supermarket or service station has the lowest prices overall?")

    prices = db["prices"]
    all_items  = sorted(prices.distinct("item_name"))
    all_states = ["All states"] + sorted(prices.distinct("state"))

    col1, col2 = st.columns(2)
    with col1:
        state_filter = st.selectbox("Filter by state", all_states)
    with col2:
        selected_items = st.multiselect(
            "Limit to specific items (blank = all)",
            all_items,
            placeholder="All items",
        )

    # ── Aggregation ──────────────────────────────────────────────────────────
    match = {}
    if state_filter != "All states":
        match["state"] = state_filter
    if selected_items:
        match["item_name"] = {"$in": selected_items}

    pipeline = [
        *([ {"$match": match} ] if match else []),
        {
            "$group": {
                "_id": "$store",
                "avg_price":   {"$avg": "$price"},
                "submissions": {"$sum": 1},
                "items":       {"$addToSet": "$item_name"},
            }
        },
        {"$addFields": {"item_count": {"$size": "$items"}}},
        {"$sort": {"avg_price": 1}},
    ]

    docs = list(prices.aggregate(pipeline))
    if not docs:
        st.info("No data yet. Submit some prices!")
        return

    df = pd.DataFrame([{
        "Store":       d["_id"],
        "Avg price":   round(d["avg_price"], 2),
        "Submissions": d["submissions"],
        "Items tracked": d["item_count"],
    } for d in docs])

    # ── Medals ───────────────────────────────────────────────────────────────
    if len(df) >= 1:
        st.success(f"🥇 Cheapest overall: **{df.iloc[0]['Store']}** (avg ${df.iloc[0]['Avg price']:.2f})")
    if len(df) >= 2:
        st.info(f"🥈 Runner-up: **{df.iloc[1]['Store']}** (avg ${df.iloc[1]['Avg price']:.2f})")

    st.markdown("---")

    # ── Bar chart ─────────────────────────────────────────────────────────────
    fig = px.bar(
        df, x="Store", y="Avg price",
        color="Avg price", color_continuous_scale="teal",
        height=360, text="Avg price",
    )
    fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_tickangle=-25,
    )
    fig.update_yaxes(tickprefix="$", gridcolor="rgba(128,128,128,0.1)")
    st.plotly_chart(fig, width="stretch")

    # ── Per-item heatmap ──────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Price heatmap by store & item")
    st.caption("Green = cheaper, red = more expensive (relative to other stores for the same item).")

    pivot_pipeline = [
        *([ {"$match": match} ] if match else []),
        {
            "$group": {
                "_id": {"store": "$store", "item": "$item_name"},
                "avg": {"$avg": "$price"},
            }
        },
    ]
    pivot_docs = list(prices.aggregate(pivot_pipeline))

    if pivot_docs:
        pv = pd.DataFrame([{
            "store": d["_id"]["store"],
            "item":  d["_id"]["item"],
            "avg":   round(d["avg"], 2),
        } for d in pivot_docs])

        heat = pv.pivot_table(index="store", columns="item", values="avg")

        fig2 = go.Figure(data=go.Heatmap(
            z=heat.values,
            x=heat.columns.tolist(),
            y=heat.index.tolist(),
            colorscale="RdYlGn_r",
            hoverongaps=False,
            hovertemplate="Store: %{y}<br>Item: %{x}<br>Avg: $%{z:.2f}<extra></extra>",
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_tickangle=-35,
            height=max(300, len(heat) * 40 + 100),
        )
        st.plotly_chart(fig2, width="stretch")

    # ── Table ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    display = df.copy()
    display["Avg price"] = display["Avg price"].apply(lambda x: f"${x:.2f}")
    st.dataframe(display, width="stretch", hide_index=True)
