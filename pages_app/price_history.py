import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

NEON  = "#00EEFF"
GREEN = "#00C853"
RED   = "#FF1744"
AMBER = "#FFD700"
BG    = "rgba(0,0,0,0)"
GRID  = "rgba(0,238,255,0.07)"

STORE_COLORS = {"Woolworths": GREEN, "Coles": RED}


def _store_color(name):
    return STORE_COLORS.get(name, NEON)


def show(db):
    st.title("📈 Price History")
    st.caption("Automated price trends scraped from Woolworths & Coles across Brisbane.")

    prices = db["prices"]

    if prices.count_documents({}) == 0:
        st.info("No price data yet — run Auto-Scrape to populate.")
        return

    # ── Date range selector (only control on the page) ───────────────────────
    days = st.select_slider(
        "Time window",
        options=[7, 14, 30, 60, 90, 180],
        value=30,
        format_func=lambda x: f"Last {x} days",
    )
    since = datetime.utcnow() - timedelta(days=days)

    # Load all data for the window once
    docs = list(prices.find(
        {"submitted_at": {"$gte": since}},
        {"_id": 0, "item_name": 1, "price": 1, "store": 1,
         "suburb": 1, "submitted_at": 1, "category": 1},
    ))

    if not docs:
        st.info("No data in this time window — try a wider range or run Auto-Scrape.")
        return

    df = pd.DataFrame(docs)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    df["date"]         = df["submitted_at"].dt.date
    df["week"]         = df["submitted_at"].dt.to_period("W").apply(lambda p: p.start_time.date())

    # ── Top metrics ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price records",    f"{len(df):,}")
    c2.metric("Items tracked",    df["item_name"].nunique())
    c3.metric("Stores covered",   df.groupby(["store","suburb"]).ngroups)
    c4.metric("Avg price",        f"${df['price'].mean():.2f}")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 1. WOOLWORTHS vs COLES — average price over time
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🏪 Woolworths vs Coles — Average Price Over Time")
    st.caption("Daily average across all tracked items.")

    retailer_daily = (
        df[df["store"].isin(["Woolworths", "Coles"])]
        .groupby(["date", "store"])["price"]
        .mean()
        .reset_index()
    )

    if not retailer_daily.empty:
        fig_rv = go.Figure()
        for store, color in [("Woolworths", GREEN), ("Coles", RED)]:
            s = retailer_daily[retailer_daily["store"] == store]
            if not s.empty:
                fig_rv.add_trace(go.Scatter(
                    x=s["date"], y=s["price"].round(2),
                    mode="lines+markers",
                    name=store,
                    line=dict(color=color, width=2),
                    marker=dict(size=5),
                    hovertemplate=f"<b>{store}</b><br>%{{x}}<br>Avg: $%{{y:.2f}}<extra></extra>",
                ))
        fig_rv.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=320, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.25),
            xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID, tickprefix="$"),
        )
        st.plotly_chart(fig_rv, width="stretch")
    else:
        st.info("Need both Woolworths and Coles data to compare.")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 2. PRICE TREND per category
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📂 Average Price by Category Over Time")

    # Fetch category from items collection
    items_map = {
        d["name"]: d.get("category", "Other")
        for d in db["items"].find({}, {"name": 1, "category": 1, "_id": 0})
    }
    df["category"] = df["item_name"].map(items_map).fillna("Other")

    # Exclude Fuel (prices on different scale)
    cat_df = df[df["category"] != "Fuel"]
    cat_weekly = (
        cat_df.groupby(["week", "category"])["price"]
        .mean().reset_index()
    )

    if not cat_weekly.empty:
        fig_cat = px.line(
            cat_weekly, x="week", y="price", color="category",
            height=360,
            labels={"week": "Week", "price": "Avg Price ($)", "category": "Category"},
        )
        fig_cat.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            margin=dict(l=0, r=0, t=10, b=30),
            legend=dict(orientation="h", y=-0.3),
            xaxis=dict(gridcolor=GRID),
            yaxis=dict(gridcolor=GRID, tickprefix="$"),
        )
        st.plotly_chart(fig_cat, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 3. TOP 10 MOST EXPENSIVE items (current avg)
    # ════════════════════════════════════════════════════════════════════════
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("💸 10 Most Expensive Items")
        top10 = (
            df.groupby("item_name")["price"].mean()
            .sort_values(ascending=False).head(10)
            .reset_index()
        )
        top10.columns = ["Item", "Avg ($)"]
        fig_top = go.Figure(go.Bar(
            x=top10["Avg ($)"].round(2),
            y=top10["Item"],
            orientation="h",
            marker_color=RED,
            text=top10["Avg ($)"].apply(lambda x: f"${x:.2f}"),
            textposition="outside",
            textfont=dict(color=NEON),
        ))
        fig_top.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=360, margin=dict(l=0, r=120, t=10, b=0),
            xaxis=dict(tickprefix="$", gridcolor=GRID),
            yaxis=dict(categoryorder="total ascending"),
        )
        st.plotly_chart(fig_top, width="stretch")

    # ── Top 10 cheapest items ────────────────────────────────────────────────
    with col_r:
        st.subheader("🤑 10 Cheapest Items")
        bot10 = (
            df.groupby("item_name")["price"].mean()
            .sort_values(ascending=True).head(10)
            .reset_index()
        )
        bot10.columns = ["Item", "Avg ($)"]
        fig_bot = go.Figure(go.Bar(
            x=bot10["Avg ($)"].round(2),
            y=bot10["Item"],
            orientation="h",
            marker_color=GREEN,
            text=bot10["Avg ($)"].apply(lambda x: f"${x:.2f}"),
            textposition="outside",
            textfont=dict(color=NEON),
        ))
        fig_bot.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=360, margin=dict(l=0, r=120, t=10, b=0),
            xaxis=dict(tickprefix="$", gridcolor=GRID),
            yaxis=dict(categoryorder="total descending"),
        )
        st.plotly_chart(fig_bot, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 4. PRICE HEATMAP — category vs store (avg price)
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🌡️ Price Heatmap — Category vs Store")
    st.caption("Average price per category at each store. Green = cheaper, Red = more expensive.")

    heat_df = (
        df.groupby(["category", "store"])["price"]
        .mean().reset_index()
    )
    if not heat_df.empty:
        heat_pivot = heat_df.pivot_table(
            index="category", columns="store", values="price"
        )
        fig_heat = go.Figure(go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            colorscale="RdYlGn_r",
            hoverongaps=False,
            hovertemplate="Category: %{y}<br>Store: %{x}<br>Avg: $%{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(color=NEON), title=dict(text="Avg $", font=dict(color=NEON))),
        ))
        fig_heat.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=max(280, len(heat_pivot) * 38 + 80),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(tickfont=dict(color=NEON)),
            yaxis=dict(tickfont=dict(color=NEON)),
        )
        st.plotly_chart(fig_heat, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 5. PRICE DISTRIBUTION — box plot per category
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📊 Price Distribution by Category")
    st.caption("Spread of prices within each category — shows outliers and typical ranges.")

    box_df = df[df["category"] != "Fuel"]
    if not box_df.empty:
        fig_box = px.box(
            box_df.sort_values("category"),
            x="category", y="price",
            color="store",
            color_discrete_map={"Woolworths": GREEN, "Coles": RED},
            height=400,
            labels={"category": "Category", "price": "Price ($)", "store": "Store"},
            points="outliers",
        )
        fig_box.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.25),
            xaxis=dict(gridcolor=GRID, tickangle=-30),
            yaxis=dict(gridcolor=GRID, tickprefix="$"),
        )
        st.plotly_chart(fig_box, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 6. SUBURB PRICE COMPARISON — top 15 suburbs by avg price
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🗺️ Average Price by Brisbane Suburb")
    st.caption("Top 15 suburbs with the most price records.")

    suburb_df = (
        df.groupby("suburb")
        .agg(avg_price=("price", "mean"), count=("price", "count"))
        .reset_index()
        .sort_values("count", ascending=False)
        .head(15)
        .sort_values("avg_price", ascending=True)
    )

    if not suburb_df.empty:
        fig_sub = go.Figure(go.Bar(
            x=suburb_df["avg_price"].round(2),
            y=suburb_df["suburb"],
            orientation="h",
            marker_color=NEON,
            text=suburb_df["avg_price"].apply(lambda x: f"${x:.2f}"),
            textposition="outside",
            textfont=dict(color=NEON),
            customdata=suburb_df["count"],
            hovertemplate="<b>%{y}</b><br>Avg: $%{x:.2f}<br>Records: %{customdata}<extra></extra>",
        ))
        fig_sub.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=460, margin=dict(l=0, r=100, t=10, b=0),
            xaxis=dict(tickprefix="$", gridcolor=GRID),
            yaxis=dict(tickfont=dict(color=NEON)),
        )
        st.plotly_chart(fig_sub, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 7. WEEKLY SCRAPE VOLUME — how much data we're collecting
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📥 Weekly Scrape Volume")
    st.caption("Number of price records collected each week.")

    vol_df = (
        df.groupby(["week", "store"])
        .size().reset_index(name="count")
    )
    fig_vol = px.bar(
        vol_df, x="week", y="count",
        color="store",
        color_discrete_map={"Woolworths": GREEN, "Coles": RED},
        barmode="stack",
        height=280,
        labels={"week": "Week", "count": "Records", "store": "Store"},
    )
    fig_vol.update_layout(
        plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.3),
        xaxis=dict(gridcolor=GRID),
        yaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(fig_vol, width="stretch")
