import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
df_pricing = pd.read_csv("data/pricing_plans.csv")
df_usage = pd.read_csv("data/usage_data.csv")
df_elasticity = pd.read_csv("data/pricing_elasticity.csv")
df_ltv = pd.read_csv("data/churn_retention.csv")
df_competition = pd.read_csv("data/competitive_pricing.csv")

st.set_page_config(page_title="Hub Monetization Insights", layout="wide")
st.title("💸 Hub Monetization Insights Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Revenue & LTV", "📈 Price Elasticity", "🏁 Competitive Benchmarking"])

with tab1:
    st.subheader("Revenue & LTV by Hub and Tier")
    selected_hub = st.selectbox("Select a Hub", df_usage["hub"].unique())
    filtered = df_usage[df_usage["hub"] == selected_hub]
    fig1 = px.box(filtered, x="tier", y="monthly_recurring_revenue", title="MRR Distribution")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(df_ltv[df_ltv["hub"] == selected_hub], x="tier", y="avg_ltv", color="tier", title="Average LTV")
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Pricing Elasticity Simulation")
    selected_hub = st.selectbox("Hub for Elasticity", df_elasticity["hub"].unique())
    selected_tier = st.selectbox("Tier for Elasticity", df_elasticity["tier"].unique())
    subset = df_elasticity[(df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)]
    fig3 = px.line(subset, x="price", y="adoption_rate", title="Adoption Rate vs. Price")
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Competitive Pricing Comparison")
    selected_hub = st.selectbox("Hub for Comparison", df_competition["product_hub"].unique())
    selected_tier = st.selectbox("Tier for Comparison", df_competition["tier"].unique())
    subset = df_competition[(df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)]
    fig4 = px.bar(subset, x="vendor", y="price_usd", color="vendor", title="Competitor Pricing Comparison")
    st.plotly_chart(fig4, use_container_width=True)
