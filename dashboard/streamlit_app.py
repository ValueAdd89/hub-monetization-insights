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
    return df_pricing, df_usage, df_elasticity, df_ltv, df_competition

df_pricing, df_usage, df_elasticity, df_ltv, df_competition = load_data()

# ------------------------------
# Page Configuration
# ------------------------------
st.set_page_config(
    page_title="Hub Monetization Insights",
    page_icon="💸",
    layout="wide"
)

# ------------------------------
# Sidebar
# ------------------------------
st.sidebar.title("Hub Filters")
selected_hub = st.sidebar.selectbox("Choose a Hub", sorted(df_usage["hub"].unique()))
selected_tier = st.sidebar.selectbox("Choose a Tier", sorted(df_usage["tier"].unique()))
theme = st.sidebar.radio("Theme", ["Light", "Dark"])

# ------------------------------
# Theming
# ------------------------------
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", "💵 Pricing Elasticity", "📊 LTV & Retention", 
    "🏁 Competitor Intelligence", "🧠 Recommendations"
])

# ------------------------------
# Tab 1: Overview KPIs
# ------------------------------
with tab1:
    st.subheader(f"📊 Overview KPIs - {selected_hub} / {selected_tier}")
    filtered = df_usage[(df_usage["hub"] == selected_hub) & (df_usage["tier"] == selected_tier)]

    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", len(filtered))
    col2.metric("Avg MRR", f"${filtered['monthly_recurring_revenue'].mean():.2f}")
    col3.metric("Avg Lifetime (months)", f"{filtered['months_active'].mean():.1f}")

    fig1 = px.histogram(filtered, x="months_active", nbins=20, title="Customer Tenure Distribution")
    st.plotly_chart(fig1, use_container_width=True)

# ------------------------------
# Tab 2: Price Elasticity
# ------------------------------
with tab2:
    st.subheader("💵 Price Elasticity Curve")
    df_elasticity_filtered = df_elasticity[
        (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
    ]
    fig2 = px.line(df_elasticity_filtered, x="price", y="adoption_rate",
                   markers=True, title="Adoption Rate vs Price")
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------
# Tab 3: LTV & Retention
# ------------------------------
with tab3:
    st.subheader("📊 LTV & Churn by Tier")
    df_ltv_filtered = df_ltv[df_ltv["hub"] == selected_hub]
    fig3 = px.bar(df_ltv_filtered, x="tier", y="avg_ltv", color="tier", title="Average Lifetime Value")
    st.plotly_chart(fig3, use_container_width=True)

    fig4 = px.bar(df_ltv_filtered, x="tier", y="churn_rate", color="tier", title="Churn Rate by Tier")
    st.plotly_chart(fig4, use_container_width=True)

# ------------------------------
# Tab 4: Competitive Intelligence
# ------------------------------
with tab4:
    st.subheader("🏁 Competitive Price Benchmark")
    df_comp = df_competition[
        (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
    ]
    fig5 = px.bar(df_comp, x="vendor", y="price_usd", color="vendor", title="Vendor Pricing")
    st.plotly_chart(fig5, use_container_width=True)

# ------------------------------
# Tab 5: Auto Recommendations
# ------------------------------
with tab5:
    st.subheader("🧠 Pricing Strategy Recommendations")
    st.markdown(f"""
    Based on selected filters: **{selected_hub} – {selected_tier}**

    - 📉 If adoption drops significantly with price ↑, avoid increases > $10/year
    - 📦 Consider bundling {selected_tier} with CMS for higher retention
    - 🧮 Expand annual renewal offers for enterprise customers

    _These recommendations are derived from LTV, churn, and elasticity insights._
    """)
