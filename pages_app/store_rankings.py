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

STORE_COLORS  = {"Woolworths": GREEN, "Coles": RED}
DEFAULT_COLOR = NEON


def _sc(store):
    return STORE_COLORS.get(store, DEFAULT_COLOR)


def _label(store):
    c = _sc(store)
    return f'<span style="color:{c};font-weight:700">{store}</span>'


def show(db):
    st.title("📊 Store Rankings")
    st.caption("How Woolworths and Coles compare across every tracked item in Brisbane.")

    prices = db["prices"]

    if prices.count_documents({}) == 0:
        st.info("No data yet — run Auto-Scrape to populate.")
        return

    # Load all data (no user filters)
    docs = list(prices.find(
        {},
        {"_id": 0, "item_name": 1, "price": 1, "store": 1,
         "suburb": 1, "submitted_at": 1},
    ))
    df = pd.DataFrame(docs)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    df["week"] = df["submitted_at"].dt.to_period("W").apply(lambda p: p.start_time.date())

    # Fetch category map
    items_map = {
        d["name"]: d.get("category", "Other")
        for d in db["items"].find({}, {"name": 1, "category": 1, "_id": 0})
    }
    df["category"] = df["item_name"].map(items_map).fillna("Other")

    ww_df  = df[df["store"] == "Woolworths"]
    col_df = df[df["store"] == "Coles"]

    # ── Overall winner banner ─────────────────────────────────────────────────
    overall = (
        df.groupby("store")["price"].mean()
        .reset_index().sort_values("price")
    )
    if len(overall) >= 1:
        winner = overall.iloc[0]
        loser  = overall.iloc[1] if len(overall) > 1 else None
        diff   = (loser["price"] - winner["price"]) if loser is not None else 0
        st.markdown(
            f'### 🥇 Overall cheapest: {_label(winner["store"])} '
            f'— avg **${winner["price"]:.2f}**',
            unsafe_allow_html=True,
        )
        if loser is not None:
            st.markdown(
                f'🥈 {_label(loser["store"])} avg **${loser["price"]:.2f}** '
                f'— <span style="color:{AMBER}">+${diff:.2f} more expensive</span>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 1. OVERALL AVG PRICE — Woolworths vs Coles
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🏪 Overall Average Price: Woolworths vs Coles")

    avg_df = (
        df.groupby("store")["price"]
        .agg(["mean", "median", "min", "max", "count"])
        .reset_index()
        .rename(columns={"mean": "Mean", "median": "Median",
                         "min": "Min", "max": "Max", "count": "Records"})
        .sort_values("Mean")
    )

    c1, c2 = st.columns(2)
    for col, row in zip([c1, c2], avg_df.itertuples()):
        color = _sc(row.store)
        col.markdown(
            f'<div style="border:1px solid {color};border-radius:8px;padding:14px;text-align:center">'
            f'<div style="color:{color};font-size:1.3em;font-weight:700">{row.store}</div>'
            f'<div style="color:{NEON};font-size:2em;font-weight:700">${row.Mean:.2f}</div>'
            f'<div style="color:{NEON};font-size:0.85em">avg &nbsp;|&nbsp; '
            f'median ${row.Median:.2f} &nbsp;|&nbsp; '
            f'{row.Records:,} records</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 2. HEAD-TO-HEAD BY CATEGORY
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📂 Head-to-Head by Category")
    st.caption("Average price per category. Which store wins each category?")

    cat_df = (
        df[df["store"].isin(["Woolworths", "Coles"]) & (df["category"] != "Fuel")]
        .groupby(["category", "store"])["price"]
        .mean().reset_index()
    )
    if not cat_df.empty:
        fig_cat = px.bar(
            cat_df.sort_values("category"),
            x="price", y="category",
            color="store",
            barmode="group",
            orientation="h",
            color_discrete_map={"Woolworths": GREEN, "Coles": RED},
            height=max(300, cat_df["category"].nunique() * 50 + 80),
            labels={"price": "Avg Price ($)", "category": "", "store": "Store"},
            text=cat_df["price"].apply(lambda x: f"${x:.2f}"),
        )
        fig_cat.update_traces(textposition="outside", textfont=dict(color=NEON))
        fig_cat.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            margin=dict(l=0, r=80, t=10, b=0),
            legend=dict(orientation="h", y=-0.15),
            xaxis=dict(tickprefix="$", gridcolor=GRID),
            yaxis=dict(tickfont=dict(color=NEON)),
        )
        st.plotly_chart(fig_cat, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 3. ITEM-LEVEL PRICE GAP — where the biggest savings are
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("💰 Biggest Price Gaps Between Stores")
    st.caption("Items where Woolworths and Coles differ the most. Green = Woolworths cheaper, Red = Coles cheaper.")

    pivot_item = (
        df[df["store"].isin(["Woolworths", "Coles"])]
        .groupby(["item_name", "store"])["price"]
        .mean().unstack("store")
        .dropna()
        .reset_index()
    )
    if not pivot_item.empty and "Woolworths" in pivot_item and "Coles" in pivot_item:
        pivot_item["gap"]      = pivot_item["Woolworths"] - pivot_item["Coles"]
        pivot_item["abs_gap"]  = pivot_item["gap"].abs()
        top_gaps = pivot_item.sort_values("abs_gap", ascending=False).head(15)
        bar_colors = [GREEN if g < 0 else RED for g in top_gaps["gap"]]
        text_labels = [
            f"WW ${row.Woolworths:.2f}  |  Coles ${row.Coles:.2f}"
            for row in top_gaps.itertuples()
        ]
        fig_gap = go.Figure(go.Bar(
            x=top_gaps["gap"].round(2),
            y=top_gaps["item_name"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"${abs(g):.2f}" for g in top_gaps["gap"]],
            textposition="outside",
            textfont=dict(color=NEON),
            customdata=text_labels,
            hovertemplate="<b>%{y}</b><br>%{customdata}<br>Gap: $%{x:+.2f}<extra></extra>",
        ))
        fig_gap.add_vline(x=0, line_color=NEON, line_width=1, opacity=0.5)
        fig_gap.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=max(320, len(top_gaps) * 34 + 80),
            margin=dict(l=0, r=80, t=10, b=20),
            xaxis=dict(tickprefix="$", gridcolor=GRID, title="Price difference (WW − Coles)"),
            yaxis=dict(tickfont=dict(color=NEON), categoryorder="total ascending"),
        )
        st.plotly_chart(fig_gap, width="stretch")
        st.caption("← Woolworths cheaper &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Coles cheaper →")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 4. PRICE TREND — Woolworths vs Coles over time
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("📈 Price Trend Over Time")

    weekly = (
        df[df["store"].isin(["Woolworths", "Coles"])]
        .groupby(["week", "store"])["price"]
        .mean().reset_index()
    )
    if not weekly.empty:
        fig_trend = go.Figure()
        for store, color in [("Woolworths", GREEN), ("Coles", RED)]:
            s = weekly[weekly["store"] == store]
            if not s.empty:
                fig_trend.add_trace(go.Scatter(
                    x=s["week"], y=s["price"].round(2),
                    mode="lines+markers",
                    name=store,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>{store}</b><br>%{{x}}<br>$%{{y:.2f}}<extra></extra>",
                ))
        fig_trend.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.3),
            xaxis=dict(gridcolor=GRID, title="Week"),
            yaxis=dict(gridcolor=GRID, tickprefix="$"),
        )
        st.plotly_chart(fig_trend, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 5. FULL ITEM HEATMAP
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🌡️ Price Heatmap — All Items by Store")
    st.caption("Green = cheaper, red = more expensive within each row.")

    pivot_all = (
        df.groupby(["store", "item_name"])["price"]
        .mean().reset_index()
    )
    if not pivot_all.empty:
        heat = pivot_all.pivot_table(index="store", columns="item_name", values="price")
        store_labels = heat.index.tolist()
        annotations = [
            dict(
                x=-0.005, xref="paper", xanchor="right",
                y=i, yref="y",
                text=f'<b>{s}</b>',
                font=dict(color=_sc(s), size=12),
                showarrow=False,
            )
            for i, s in enumerate(store_labels)
        ]
        fig_heat = go.Figure(go.Heatmap(
            z=heat.values,
            x=heat.columns.tolist(),
            y=heat.index.tolist(),
            colorscale="RdYlGn_r",
            hoverongaps=False,
            hovertemplate="Store: %{y}<br>Item: %{x}<br>Avg: $%{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(color=NEON),
                          title=dict(text="Avg $", font=dict(color=NEON))),
        ))
        fig_heat.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            margin=dict(l=120, r=0, t=10, b=0),
            xaxis=dict(tickangle=-40, tickfont=dict(color=NEON, size=9)),
            yaxis=dict(showticklabels=False),
            annotations=annotations,
            height=max(260, len(heat) * 45 + 100),
        )
        st.plotly_chart(fig_heat, width="stretch")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 6. SUBURB-LEVEL: which suburb is cheapest at each store
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🗺️ Average Price by Store Location")
    st.caption("Each bar is a specific store branch — compare within Woolworths or Coles.")

    loc_df = (
        df.groupby(["store", "suburb"])["price"]
        .mean().reset_index()
        .sort_values("price")
    )
    loc_df["label"] = loc_df["store"] + " · " + loc_df["suburb"]
    loc_df["color"] = loc_df["store"].map(lambda s: _sc(s))

    if not loc_df.empty:
        fig_loc = go.Figure(go.Bar(
            x=loc_df["label"],
            y=loc_df["price"].round(2),
            marker_color=loc_df["color"].tolist(),
            text=loc_df["price"].apply(lambda x: f"${x:.2f}"),
            textposition="outside",
            textfont=dict(color=NEON, size=9),
            hovertemplate="<b>%{x}</b><br>Avg: $%{y:.2f}<extra></extra>",
        ))
        fig_loc.update_layout(
            plot_bgcolor=BG, paper_bgcolor=BG, font=dict(color=NEON),
            height=420, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(tickangle=-40, tickfont=dict(color=NEON, size=9)),
            yaxis=dict(tickprefix="$", gridcolor=GRID),
        )
        st.plotly_chart(fig_loc, width="stretch")
