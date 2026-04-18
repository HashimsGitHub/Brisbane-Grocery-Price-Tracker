import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def show(db):
    st.title("📈 Price History")
    st.caption("Track how any item's price has changed over time.")

    prices = db["prices"]
    all_items = sorted(prices.distinct("item_name"))

    if not all_items:
        st.info("No price data yet. Submit some prices to see history!")
        return

    # ── Filters ──────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_item = st.selectbox("Select item", all_items)
    with col2:
        all_suburbs = ["All suburbs"] + sorted(prices.distinct("suburb"))
        selected_suburb = st.selectbox("Suburb", all_suburbs)
    with col3:
        all_stores = ["All stores"] + sorted(prices.distinct("store"))
        selected_store = st.selectbox("Store", all_stores)

    date_range = st.slider(
        "Date range (days back)",
        min_value=7, max_value=180, value=60, step=7,
    )

    # ── Query ────────────────────────────────────────────────────────────────
    since = datetime.utcnow() - timedelta(days=date_range)
    query = {"item_name": selected_item, "submitted_at": {"$gte": since}}
    if selected_suburb != "All suburbs":
        query["suburb"] = selected_suburb
    if selected_store != "All stores":
        query["store"] = selected_store

    docs = list(prices.find(query, {"_id": 0, "user_hash": 0, "location": 0})
                .sort("submitted_at", 1))

    if not docs:
        st.warning("No data for this combination. Try broadening your filters.")
        return

    df = pd.DataFrame(docs)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    df["date"] = df["submitted_at"].dt.date

    # ── Summary metrics ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Submissions", len(df))
    m2.metric("Current avg", f"${df['price'].mean():.2f}")
    m3.metric("Lowest seen",  f"${df['price'].min():.2f}")
    m4.metric("Highest seen", f"${df['price'].max():.2f}")

    st.markdown("---")

    # ── Trend chart ──────────────────────────────────────────────────────────
    st.subheader(f"Price trend — {selected_item}")

    # Daily average
    daily = df.groupby("date")["price"].agg(["mean", "min", "max"]).reset_index()
    daily.columns = ["date", "avg", "min", "max"]

    fig = go.Figure()

    # Shaded min-max band
    fig.add_trace(go.Scatter(
        x=list(daily["date"]) + list(daily["date"])[::-1],
        y=list(daily["max"]) + list(daily["min"])[::-1],
        fill="toself",
        fillcolor="rgba(29,158,117,0.1)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Price range",
        hoverinfo="skip",
    ))

    # Average line
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["avg"].round(2),
        mode="lines+markers",
        line=dict(color="#1D9E75", width=2),
        marker=dict(size=5),
        name="Daily avg",
    ))

    # Raw scatter
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["price"].round(2),
        mode="markers",
        marker=dict(color="#0F6E56", size=4, opacity=0.4),
        name="Individual submission",
    ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#00EEFF"),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=0, r=0, t=10, b=0),
        height=380,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.1)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.1)", tickprefix="$")
    st.plotly_chart(fig, width="stretch")

    # ── Price by store ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Average price by store")
    store_avg = df.groupby("store")["price"].mean().reset_index().sort_values("price")
    store_avg.columns = ["Store", "Avg Price"]

    fig2 = px.bar(
        store_avg, x="Store", y="Avg Price",
        color="Avg Price", color_continuous_scale="teal",
        height=280,
    )
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#00EEFF"),
        coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0),
    )
    fig2.update_yaxes(tickprefix="$")
    st.plotly_chart(fig2, width="stretch")

    # ── Raw data table ────────────────────────────────────────────────────────
    with st.expander("View raw submissions"):
        display_df = df.copy()
        display_df["submitted_at"] = display_df["submitted_at"].dt.strftime("%d %b %Y %H:%M")
        display_df["price"] = display_df["price"].apply(lambda x: f"${x:.2f}")
        st.dataframe(
            display_df.rename(columns={
                "item_name": "Item", "price": "Price", "unit": "Unit",
                "store": "Store", "suburb": "Suburb", "state": "State",
                "submitted_at": "Submitted",
            }),
            width="stretch", hide_index=True,
        )
