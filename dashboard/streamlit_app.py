import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------
# Load Data
# ------------------------------
@st.cache_data
def load_data():
    df_pricing = pd.read_csv("data/pricing_plans.csv")
    df_usage = pd.read_csv("data/usage_data.csv")
    df_elasticity = pd.read_csv("data/pricing_elasticity.csv")
    df_ltv = pd.read_csv("data/churn_retention.csv")
    df_competition = pd.read_csv("data/competitive_pricing.csv")
    df_funnel = pd.read_csv("data/funnel_data.csv")
    df_treemap = pd.read_csv("data/ltv_treemap.csv")
    return df_pricing, df_usage, df_elasticity, df_ltv, df_competition, df_funnel, df_treemap

df_pricing, df_usage, df_elasticity, df_ltv, df_competition, df_funnel, df_treemap = load_data()

# ------------------------------
# Config
# ------------------------------
st.set_page_config(page_title="Hub Monetization Insights", page_icon="💸", layout="wide")

# Sidebar Filters
st.sidebar.title("Hub Filters")
selected_hub = st.sidebar.selectbox("Choose a Hub", sorted(df_usage["hub"].unique()))
selected_tier = st.sidebar.selectbox("Choose a Tier", sorted(df_usage["tier"].unique()))
theme = st.sidebar.radio("Theme", ["Light", "Dark"])

if theme == "Dark":
    st.markdown("<style>body { background-color: #111; color: #eee; }</style>", unsafe_allow_html=True)

# ------------------------------
# Header
# ------------------------------
st.title("💸 Hub Monetization Insights Dashboard")
st.caption("Analyze LTV, churn, price elasticity, and competitor positioning by product hub")

# ------------------------------
# Tabs
# ------------------------------
tabs = st.tabs([
    "📊 Overview", "💵 Pricing Elasticity", "📈 LTV Treemap",
    "🌍 Geo View", "📉 Funnel Analysis", "🏁 Competitors", "🧠 Recommendations"
])

# ------------------------------
# Tab 1: Overview KPIs
# ------------------------------
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

# ------------------------------
# Tab 2: Price Elasticity
# ------------------------------
with tabs[1]:
    st.subheader("💵 Price Elasticity Curve")
    elastic_filtered = df_elasticity[
        (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
    ]
    fig2 = px.line(elastic_filtered, x="price", y="adoption_rate", markers=True,
                   title="Adoption Rate vs Price")
    fig2.update_layout(xaxis_title="Price (USD)", yaxis_title="Adoption Rate")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------
# Tab 3: LTV Treemap
# ------------------------------
with tabs[2]:
    st.subheader("📈 Lifetime Value Treemap")
    fig3 = px.treemap(df_treemap, path=["hub", "tier"], values="avg_ltv",
                      title="Average LTV Contribution by Product Line")
    st.plotly_chart(fig3, use_container_width=True)

# ------------------------------
# Tab 4: Geo View
# ------------------------------
with tabs[3]:
    st.subheader("🌍 Geographic Customer Distribution")

    geo_mode = st.radio("Map Mode", ["Global", "USA States"], horizontal=True)

    if geo_mode == "Global":
        geo_data_global = df_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
        fig4 = px.choropleth(
            geo_data_global,
            locations="country",
            locationmode="country names",
            color="customers",
            color_continuous_scale="Blues",
            title="Customer Count by Country"
        )
        fig4.update_layout(geo=dict(bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig4, use_container_width=True)

    elif geo_mode == "USA States":
        geo_data_us = df_usage.groupby("state").agg(customers=("customer_id", "count")).reset_index()
        fig4 = px.choropleth(
            geo_data_us,
            locations="state",
            locationmode="USA-states",
            scope="usa",
            color="customers",
            color_continuous_scale="Blues",
            title="Customer Count by U.S. State"
        )
        fig4.update_layout(geo=dict(bgcolor='rgba(0,0,0,0)'))
        st.plotly_chart(fig4, use_container_width=True)

# ------------------------------
# Tab 5: Funnel Analysis
# ------------------------------
with tabs[4]:
    st.subheader("📉 Conversion Funnel by Hub")
    funnel_order = ["Visitor", "Signup", "Trial", "Paid"]
    funnel_filtered = df_funnel[df_funnel["hub"] == selected_hub]
    funnel_filtered["stage"] = pd.Categorical(funnel_filtered["stage"], categories=funnel_order, ordered=True)
    funnel_sorted = funnel_filtered.sort_values("stage")
    fig5 = px.funnel(funnel_sorted, x="count", y="stage", title="Customer Funnel")
    fig5.update_layout(yaxis_title="Funnel Stage", xaxis_title="User Count")
    st.plotly_chart(fig5, use_container_width=True)

# ------------------------------
# Tab 6: Competitor Pricing
# ------------------------------
with tabs[5]:
    st.subheader("🏁 Competitive Price Benchmark")
    df_comp = df_competition[
        (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
    ]
    fig6 = px.bar(df_comp, x="vendor", y="price_usd", color="vendor", title="Vendor Pricing")
    fig6.update_layout(xaxis_title="Vendor", yaxis_title="Price (USD)")
    st.plotly_chart(fig6, use_container_width=True)

# ------------------------------
# Tab 7: Recommendations
# ------------------------------
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
