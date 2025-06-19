import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path  

@st.cache_data
def load_data():
    df_usage = pd.read_csv("data/usage_data.csv")
    df_funnel = pd.read_csv("data/funnel_data.csv")
    df_elasticity = pd.read_csv("data/pricing_elasticity.csv") if Path("data/pricing_elasticity.csv").exists() else pd.DataFrame()
    df_treemap = pd.read_csv("data/ltv_treemap.csv") if Path("data/ltv_treemap.csv").exists() else pd.DataFrame()
    df_competition = pd.read_csv("data/competitive_pricing.csv") if Path("data/competitive_pricing.csv").exists() else pd.DataFrame()
    return df_usage, df_funnel, df_elasticity, df_treemap, df_competition

df_usage, df_funnel, df_elasticity, df_treemap, df_competition = load_data()

st.set_page_config(page_title="Hub Monetization Insights", page_icon="💸", layout="wide")

st.sidebar.title("Hub Filters")
selected_hub = st.sidebar.selectbox("Choose a Hub", sorted(df_usage["hub"].unique()))
selected_tier = st.sidebar.selectbox("Choose a Tier", sorted(df_usage["tier"].unique()))

st.title("💸 Hub Monetization Insights Dashboard")

tabs = st.tabs([
    "📊 Overview", "💵 Pricing Elasticity", "📈 LTV Treemap",
    "🌍 Geo View", "📉 Funnel Analysis", "🏁 Competitors", "🧠 Recommendations"
])

with tabs[0]:
    st.subheader(f"📊 Overview Metrics – {selected_hub} / {selected_tier}")
    filtered = df_usage[(df_usage["hub"] == selected_hub) & (df_usage["tier"] == selected_tier)]
    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", len(filtered))
    col2.metric("Avg MRR", f"${filtered['monthly_recurring_revenue'].mean():.2f}")
    col3.metric("Avg Lifetime (Months)", f"{filtered['months_active'].mean():.1f}")
    fig1 = px.histogram(filtered, x="months_active", nbins=20,
                        title="Customer Tenure Distribution")
    fig1.update_layout(xaxis_title="Months Active", yaxis_title="Count")
    st.plotly_chart(fig1, use_container_width=True)

with tabs[1]:
    st.subheader("💵 Price Elasticity Curve")
    if not df_elasticity.empty:
        elastic_filtered = df_elasticity[
            (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
        ]
        fig2 = px.line(elastic_filtered, x="price", y="adoption_rate", markers=True,
                       title="Adoption Rate vs Price")
        fig2.update_layout(xaxis_title="Price (USD)", yaxis_title="Adoption Rate")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Elasticity data not available.")

with tabs[2]:
    st.subheader("📈 Lifetime Value Treemap")
    if not df_treemap.empty:
        fig3 = px.treemap(df_treemap, path=["hub", "tier"], values="avg_ltv",
                          title="Average LTV Contribution by Product Line")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Treemap data not available.")

with tabs[3]:
    st.subheader("🌍 Geographic Customer Distribution")
    geo_mode = st.radio("Map Mode", ["Global", "USA States"], horizontal=True)

    if geo_mode == "Global":
        geo_data = df_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
        fig4 = go.Figure(data=go.Scattergeo(
            locations=geo_data['country'],
            locationmode="country names",
            text=geo_data['customers'],
            marker=dict(
                size=geo_data['customers'] / 10,
                color='rgba(44, 102, 180, 0.6)',
                line=dict(color='black', width=0.5)
            )
        ))
        fig4.update_layout(title_text="Customer Distribution by Country", geo=dict(
            showland=True, landcolor='lightgray', showlakes=True, lakecolor='white'
        ))
        st.plotly_chart(fig4, use_container_width=True)

    else:
        geo_data = df_usage.groupby("state").agg(customers=("customer_id", "count")).reset_index()
        fig4 = go.Figure(data=go.Scattergeo(
            locations=geo_data['state'],
            locationmode="USA-states",
            scope="usa",
            text=geo_data['customers'],
            marker=dict(
                size=geo_data['customers'] / 10,
                color='rgba(44, 102, 180, 0.6)',
                line=dict(color='black', width=0.5)
            )
        ))
        fig4.update_layout(title_text="Customer Distribution by U.S. State", geo=dict(
            showland=True, landcolor='lightgray', showlakes=True, lakecolor='white'
        ))
        st.plotly_chart(fig4, use_container_width=True)

with tabs[4]:
    st.subheader("📉 Conversion Funnel by Hub")
    compare_by = st.radio("Compare Funnel By:", ["Tier", "Country"], horizontal=True)
    col = "tier" if compare_by == "Tier" else "country"
    funnel_data = df_usage.groupby([col, "stage"]).size().reset_index(name="count")
    selected_val = st.selectbox(f"Select {col.title()} to Compare", sorted(funnel_data[col].unique()))
    df_filtered = funnel_data[funnel_data[col] == selected_val]

    stage_order = ["Visitor", "Signup", "Trial", "Paid"]
    df_filtered["stage"] = pd.Categorical(df_filtered["stage"], categories=stage_order, ordered=True)
    df_sorted = df_filtered.sort_values("stage")

    stage_counts = df_sorted.set_index("stage")["count"].reindex(stage_order).fillna(0)
    signup_rate = (stage_counts["Signup"] / stage_counts["Visitor"]) if stage_counts["Visitor"] > 0 else 0
    trial_rate = (stage_counts["Trial"] / stage_counts["Signup"]) if stage_counts["Signup"] > 0 else 0
    paid_rate = (stage_counts["Paid"] / stage_counts["Trial"]) if stage_counts["Trial"] > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Signup Rate", f"{signup_rate*100:.1f}%")
    k2.metric("Trial Rate", f"{trial_rate*100:.1f}%")
    k3.metric("Paid Rate", f"{paid_rate*100:.1f}%")

    fig5 = px.funnel(df_sorted, x="count", y="stage", title=f"Customer Funnel – {selected_val}")
    fig5.update_layout(yaxis_title="Funnel Stage", xaxis_title="User Count")
    st.plotly_chart(fig5, use_container_width=True)

with tabs[5]:
    st.subheader("🏁 Competitive Price Benchmark")
    if not df_competition.empty:
        df_comp = df_competition[
            (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
        ]
        fig6 = px.bar(df_comp, x="vendor", y="price_usd", color="vendor", title="Vendor Pricing")
        fig6.update_layout(xaxis_title="Vendor", yaxis_title="Price (USD)")
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.info("Competitive pricing data not available.")

with tabs[6]:
    st.subheader("🧠 Pricing Strategy Recommendations")
    st.markdown(f"""
    Based on selected filters: **{selected_hub} – {selected_tier}**

    - 💡 Avoid price increases > $10 if adoption drops >15%
    - 📦 Bundle with CMS for Starter tier retention
    - 📈 Expand enterprise upsells in {selected_hub}
    - 🌍 Consider regional discounts in price-sensitive countries

    _Insights derived from LTV, churn, elasticity, and funnel behavior._
    """)
