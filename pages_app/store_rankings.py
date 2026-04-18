import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Brand colours
STORE_COLORS = {
    "Woolworths": "#00C853",   # green
    "Coles":      "#FF1744",   # red
}
DEFAULT_COLOR = "#00EEFF"      # neon blue for everything else


def _bar_colors(stores: list) -> list:
    return [STORE_COLORS.get(s, DEFAULT_COLOR) for s in stores]


def _store_label(name: str) -> str:
    """Return HTML-coloured store name for markdown."""
    if "Woolworths" in name:
        return f'<span style="color:#00C853;font-weight:700">{name}</span>'
    if "Coles" in name:
        return f'<span style="color:#FF1744;font-weight:700">{name}</span>'
    return f'<span style="color:#00EEFF">{name}</span>'


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

    match = {}
    if state_filter != "All states":
        match["state"] = state_filter
    if selected_items:
        match["item_name"] = {"$in": selected_items}

    pipeline = [
        *([{"$match": match}] if match else []),
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
        "Store":         d["_id"],
        "Avg price":     round(d["avg_price"], 2),
        "Submissions":   d["submissions"],
        "Items tracked": d["item_count"],
    } for d in docs])

    # Medals with brand colours
    if len(df) >= 1:
        st.markdown(
            f'🥇 Cheapest overall: {_store_label(df.iloc[0]["Store"])} '
            f'(avg ${df.iloc[0]["Avg price"]:.2f})',
            unsafe_allow_html=True,
        )
    if len(df) >= 2:
        st.markdown(
            f'🥈 Runner-up: {_store_label(df.iloc[1]["Store"])} '
            f'(avg ${df.iloc[1]["Avg price"]:.2f})',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Bar chart with brand colours
    bar_colors = _bar_colors(df["Store"].tolist())
    fig = go.Figure(go.Bar(
        x=df["Store"],
        y=df["Avg price"],
        marker_color=bar_colors,
        text=df["Avg price"].apply(lambda x: f"${x:.2f}"),
        textposition="outside",
        textfont=dict(color=bar_colors),
        hovertemplate="<b>%{x}</b><br>Avg: $%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_tickangle=-25,
        xaxis=dict(tickfont=dict(color="#00EEFF")),
        yaxis=dict(tickprefix="$", gridcolor="rgba(0,238,255,0.1)",
                   tickfont=dict(color="#00EEFF")),
        height=360,
    )
    st.plotly_chart(fig, width="stretch")

    # Per-item heatmap
    st.markdown("---")
    st.subheader("Price heatmap by store & item")
    st.caption("Green = cheaper, red = more expensive (relative to other stores for same item).")

    pivot_pipeline = [
        *([{"$match": match}] if match else []),
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
            xaxis=dict(tickfont=dict(color="#00EEFF")),
            yaxis=dict(tickfont=dict(color=[ STORE_COLORS.get(s, DEFAULT_COLOR)
                                             for s in heat.index.tolist() ])),
            height=max(300, len(heat) * 40 + 100),
        )
        st.plotly_chart(fig2, width="stretch")

    st.markdown("---")
    display = df.copy()
    display["Avg price"] = display["Avg price"].apply(lambda x: f"${x:.2f}")
    st.dataframe(display, width="stretch", hide_index=True)
