import streamlit as st
import duckdb

st.set_page_config(page_title="Eorzea Market Analytics", layout="wide")
st.title("Eorzea Market Analytics")
st.caption("Live FFXIV Market Board data — powered by Flink, Hudi, dbt, and DuckDB")

con = duckdb.connect("eorzea_analytics/eorzea.duckdb", read_only=True)

tab_arbitrage, tab_prices, tab_hq, tab_velocity, tab_history = st.tabs([
    "Cross-World Arbitrage",
    "Price Summary",
    "HQ Premium",
    "Market Velocity",
    "Price History",
])

# --- Cross-World Arbitrage ---
with tab_arbitrage:
    st.header("Cross-World Arbitrage Opportunities")
    st.markdown("Items with the biggest price gaps between worlds — buy low, sell high.")

    min_margin = st.slider("Minimum profit margin %", 0, 500, 50, key="arb_margin")

    df_arb = con.execute(f"""
        SELECT item_name, world_name, is_hq, min_price, cheapest_price, priciest_price, profit_margin_pct
        FROM mart_cross_world_arbitrage
        WHERE profit_margin_pct >= {min_margin}
        ORDER BY profit_margin_pct DESC
        LIMIT 200
    """).fetchdf()

    st.metric("Opportunities Found", len(df_arb))
    st.dataframe(df_arb, use_container_width=True)

# --- Price Summary ---
with tab_prices:
    st.header("Price Summary by Item & World")
    st.markdown("Aggregate listing prices across all tracked items.")

    df_prices = con.execute("""
        SELECT item_name, world_name, is_hq, listing_count,
               ROUND(avg_price, 0) AS avg_price, min_price, max_price, total_quantity
        FROM mart_price_summary
        ORDER BY listing_count DESC
        LIMIT 200
    """).fetchdf()

    col1, col2 = st.columns(2)
    col1.metric("Unique Items", df_prices["item_name"].nunique())
    col2.metric("Total Listings", int(df_prices["listing_count"].sum()))

    st.dataframe(df_prices, use_container_width=True)

# --- HQ Premium ---
with tab_hq:
    st.header("HQ vs Normal Quality Premium")
    st.markdown("How much more do HQ items sell for compared to normal quality?")

    df_hq = con.execute("""
        SELECT item_name, world_name,
               ROUND(hq_avg_price, 0) AS hq_avg_price,
               ROUND(nq_avg_price, 0) AS nq_avg_price,
               hq_listings, nq_listings, hq_premium_pct
        FROM mart_hq_premium
        ORDER BY hq_premium_pct DESC
        LIMIT 200
    """).fetchdf()

    if not df_hq.empty:
        col1, col2 = st.columns(2)
        col1.metric("Avg HQ Premium", f"{df_hq['hq_premium_pct'].median():.0f}%")
        col2.metric("Items with HQ Data", len(df_hq))

        chart_data = df_hq.head(20).copy()
        chart_data["label"] = chart_data["item_name"].fillna("Unknown")
        st.bar_chart(chart_data.set_index("label")["hq_premium_pct"])
    st.dataframe(df_hq, use_container_width=True)

# --- Market Velocity ---
with tab_velocity:
    st.header("Market Velocity")
    st.markdown("How fast items are selling — sales count and volume per day.")

    df_vel = con.execute("""
        SELECT item_name, world_name, sale_date, sale_count, total_volume,
               ROUND(avg_price, 0) AS avg_price
        FROM mart_market_velocity
        ORDER BY sale_count DESC
        LIMIT 200
    """).fetchdf()

    if not df_vel.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total Sales Tracked", int(df_vel["sale_count"].sum()))
        col2.metric("Total Volume", int(df_vel["total_volume"].sum()))

    st.dataframe(df_vel, use_container_width=True)

# --- Price History ---
with tab_history:
    st.header("Price History")
    st.markdown("Historical sale prices over time.")

    df_hist = con.execute("""
        SELECT item_name, world_name, is_hq, sale_date, sale_count,
               ROUND(avg_price, 0) AS avg_price, min_price, max_price, total_volume
        FROM mart_price_history
        ORDER BY sale_date DESC
        LIMIT 500
    """).fetchdf()

    if not df_hist.empty:
        df_hist["label"] = df_hist["item_name"].fillna("Unknown")
        items = sorted(df_hist["label"].unique())
        selected = st.selectbox("Select an item to chart", items)

        item_data = df_hist[df_hist["label"] == selected].sort_values("sale_date")
        if not item_data.empty:
            st.line_chart(item_data.set_index("sale_date")["avg_price"])

    st.dataframe(df_hist, use_container_width=True)
