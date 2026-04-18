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

# Neon colour palette for multi-suburb charts
SUBURB_PALETTE = [
    "#00EEFF", "#00C853", "#FF1744", "#FFD700", "#FF6D00",
    "#AA00FF", "#00B0FF", "#76FF03", "#FF4081", "#18FFFF",
    "#FFAB40", "#B388FF", "#69F0AE", "#FF6E40", "#40C4FF",
]


def show(db):
    st.title("🗺️ Suburb Compare")
    st.caption("How grocery prices vary across Brisbane suburbs — scraped from Woolworths & Coles.")

    prices = db["prices"]

    if prices.count_documents({}) == 0:
        st.info("No data yet — run Auto-Scrape to populate.")
        return

    # Load suburb-level aggregated data
    docs = list(prices.find(
        {},
        {"_id": 0, "item_name": 1, "price": 1, "store": 1,
         "suburb": 1, "submitted_at": 1},
    ))
    if not docs:
        st.info("No data yet — run Auto-Scrape to populate.")
        return

    df = pd.DataFrame(docs)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    df["week"] = df["submitted_at"].dt.to_period("W").apply(lambda p: p.start_time.date())

    # Category map
    items_map = {
        d["name"]: d.get("category", "Other")
        for d in db["items"].find({}, {"name": 1, "category": 1, "_id": 0})
    }
    df["category"] = df["item_name"].map(items_map).fillna("Other")

    all_suburbs = sorted(df["suburb"].unique())
    n_suburbs   = len(all_suburbs)

    # ── Top metrics ───────────────────────────────────────────────────────────
    suburb_avg = df.groupby("suburb")["price"].mean()
    cheapest   = suburb_avg.idxmin()
    dearest    = suburb_avg.idxmax()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Suburbs tracked",  n_suburbs)
    c2.metric("Avg across all",   f"${suburb_avg.mean():.2f}")
    c3.metric("🟢 Cheapest suburb", cheapest, f"${suburb_avg[cheapest]:.2f}")
    c4.metric("🔴 Priciest suburb", dearest,  f"${suburb_avg[dearest]:.2f}")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 1. SUBURB PRICE RANKING — all suburbs sorted by avg price
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🏆 Suburb Price Ranking")
    st.caption("Average price across all tracked items, sorted cheapest to most expensive.")

    rank_df = (
        df.groupby("suburb")
        .agg(avg=("price", "mean"), records=("price", "count"))
        .reset_index()
        .sort_values("avg")
    )
    # Colour: cheapest quartile green → most expensive quartile red
    n  = len(rank_df)
    colors = []
    for i in range(n):
        if i < n // 4:      colors.append(GREEN)
        elif i < n // 2:    colors.append(NEON)
        elif i < 3 * n // 4: colors.append(AMBER)
        else:               colors.append(RED)

    fig_rank = go.Figure(go.Bar(
        x=rank_df["avg"].round(2),
        y=rank_df["suburb"],
        orientation="h",
        marker_color=colors,
        text=rank_df["avg"].apply(lambda x: f"${x:.2f}"),
        textposition="outside",
        textfont=dict(color=NEON, size=10),
        customdata=rank_df["records"],
        hovertemplate="<b>%{y}</b><br>Avg: $%{x:.2f}<br>Records: %{customdata}<extra></extra>",
    ))
    fig_rank.update_layout(
        plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
        height=max(400, n * 28 + 80),
        margin=dict(l=0, r=90, t=10, b=0),
        xaxis=dict(tickprefix="$", gridcolor=GRID),
        yaxis=dict(tickfont=dict(color=NEON, size=10)),
    )
    st.plotly_chart(fig_rank, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 2. WOOLWORTHS vs COLES PRICE GAP PER SUBURB
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🏪 Woolworths vs Coles Price Gap by Suburb")
    st.caption("Which store is cheaper in each suburb? Green = Woolworths cheaper, Red = Coles cheaper.")

    store_suburb = (
        df[df["store"].isin(["Woolworths", "Coles"])]
        .groupby(["suburb", "store"])["price"]
        .mean().unstack("store").dropna()
        .reset_index()
    )
    if not store_suburb.empty and "Woolworths" in store_suburb and "Coles" in store_suburb:
        store_suburb["gap"] = store_suburb["Woolworths"] - store_suburb["Coles"]
        store_suburb = store_suburb.sort_values("gap")
        gap_colors = [GREEN if g < 0 else RED for g in store_suburb["gap"]]

        fig_gap = go.Figure(go.Bar(
            x=store_suburb["gap"].round(2),
            y=store_suburb["suburb"],
            orientation="h",
            marker_color=gap_colors,
            text=store_suburb["gap"].apply(lambda x: f"{'WW' if x<0 else 'Coles'} ${abs(x):.2f} cheaper"),
            textposition="outside",
            textfont=dict(color=NEON, size=9),
            customdata=list(zip(store_suburb["Woolworths"].round(2), store_suburb["Coles"].round(2))),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Woolworths: $%{customdata[0]:.2f}<br>"
                "Coles: $%{customdata[1]:.2f}<br>"
                "Gap: $%{x:+.2f}<extra></extra>"
            ),
        ))
        fig_gap.add_vline(x=0, line_color=NEON, line_width=1, opacity=0.4)
        fig_gap.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=max(300, len(store_suburb) * 32 + 80),
            margin=dict(l=0, r=140, t=10, b=20),
            xaxis=dict(tickprefix="$", gridcolor=GRID, title="Price gap (WW − Coles)"),
            yaxis=dict(tickfont=dict(color=NEON, size=10)),
        )
        st.plotly_chart(fig_gap, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 3. PRICE HEATMAP — suburb × category
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🌡️ Price Heatmap — Suburb × Category")
    st.caption("Average price per category in each suburb. Green = cheaper, Red = more expensive.")

    heat_df = (
        df[df["category"] != "Fuel"]
        .groupby(["suburb", "category"])["price"]
        .mean().reset_index()
    )
    if not heat_df.empty:
        heat_pivot = heat_df.pivot_table(index="suburb", columns="category", values="price")
        fig_heat = go.Figure(go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            colorscale="RdYlGn_r",
            hoverongaps=False,
            hovertemplate="Suburb: %{y}<br>Category: %{x}<br>Avg: $%{z:.2f}<extra></extra>",
            colorbar=dict(
                tickfont=dict(color=NEON),
                title=dict(text="Avg $", font=dict(color=NEON)),
            ),
        ))
        fig_heat.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=max(320, len(heat_pivot) * 30 + 100),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(tickfont=dict(color=NEON), tickangle=-30),
            yaxis=dict(tickfont=dict(color=NEON, size=9)),
        )
        st.plotly_chart(fig_heat, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 4. TOP 5 CHEAPEST & DEAREST SUBURBS PER CATEGORY
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📂 Cheapest & Most Expensive Suburb per Category")

    cat_suburb = (
        df[df["category"] != "Fuel"]
        .groupby(["category", "suburb"])["price"]
        .mean().reset_index()
    )
    categories = sorted(cat_suburb["category"].unique())

    # Display 3 categories per row
    for i in range(0, len(categories), 3):
        cols = st.columns(3)
        for j, cat in enumerate(categories[i:i+3]):
            cat_data = (
                cat_suburb[cat_suburb["category"] == cat]
                .sort_values("price")
            )
            if len(cat_data) < 2:
                continue
            with cols[j]:
                st.markdown(f"**{cat}**")
                top3    = cat_data.head(3)
                bottom3 = cat_data.tail(3)

                mini_fig = go.Figure()
                mini_fig.add_trace(go.Bar(
                    x=top3["price"].round(2),
                    y=top3["suburb"],
                    orientation="h",
                    marker_color=GREEN,
                    name="Cheapest",
                    hovertemplate="%{y}: $%{x:.2f}<extra></extra>",
                ))
                mini_fig.add_trace(go.Bar(
                    x=bottom3["price"].round(2),
                    y=bottom3["suburb"],
                    orientation="h",
                    marker_color=RED,
                    name="Priciest",
                    hovertemplate="%{y}: $%{x:.2f}<extra></extra>",
                ))
                mini_fig.update_layout(
                    plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON, size=9),
                    height=200, margin=dict(l=0, r=60, t=5, b=0),
                    barmode="overlay",
                    showlegend=False,
                    xaxis=dict(tickprefix="$", gridcolor=GRID, tickfont=dict(size=8)),
                    yaxis=dict(tickfont=dict(color=NEON, size=8)),
                )
                st.plotly_chart(mini_fig, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 5. WEEKLY PRICE TREND — top 6 suburbs by record count
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📈 Weekly Price Trend — Top Suburbs")
    st.caption("The 6 most-tracked suburbs over time.")

    top_suburbs = (
        df.groupby("suburb")["price"].count()
        .sort_values(ascending=False).head(6).index.tolist()
    )
    weekly_df = (
        df[df["suburb"].isin(top_suburbs)]
        .groupby(["week", "suburb"])["price"]
        .mean().reset_index()
    )
    if not weekly_df.empty:
        fig_trend = go.Figure()
        for idx, suburb in enumerate(top_suburbs):
            s = weekly_df[weekly_df["suburb"] == suburb]
            if s.empty:
                continue
            color = SUBURB_PALETTE[idx % len(SUBURB_PALETTE)]
            fig_trend.add_trace(go.Scatter(
                x=s["week"], y=s["price"].round(2),
                mode="lines+markers",
                name=suburb,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"<b>{suburb}</b><br>%{{x}}<br>$%{{y:.2f}}<extra></extra>",
            ))
        fig_trend.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=340, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
            xaxis=dict(gridcolor=GRID, title="Week"),
            yaxis=dict(gridcolor=GRID, tickprefix="$"),
        )
        st.plotly_chart(fig_trend, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 6. PRICE SPREAD BOX PLOT PER SUBURB
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📊 Price Spread per Suburb")
    st.caption("Distribution of all scraped prices in each suburb — shows variance and outliers.")

    box_colors = {s: SUBURB_PALETTE[i % len(SUBURB_PALETTE)] for i, s in enumerate(all_suburbs)}
    fig_box = go.Figure()
    for suburb in sorted(all_suburbs):
        s_data = df[df["suburb"] == suburb]["price"]
        fig_box.add_trace(go.Box(
            y=s_data,
            name=suburb,
            marker_color=box_colors[suburb],
            line_color=box_colors[suburb],
            boxmean=True,
        ))
    fig_box.update_layout(
        plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
        height=420, margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        xaxis=dict(tickangle=-35, tickfont=dict(color=NEON, size=9)),
        yaxis=dict(tickprefix="$", gridcolor=GRID),
    )
    st.plotly_chart(fig_box, width="stretch")
