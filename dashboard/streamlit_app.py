import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_data():
    df_usage = pd.read_csv("data/usage_data.csv")
    df_funnel = pd.read_csv("data/funnel_data.csv")
    return df_usage, df_funnel

df_usage, df_funnel = load_data()

st.set_page_config(page_title="Hub Monetization Insights", page_icon="💸", layout="wide")

st.sidebar.title("Hub Filters")
selected_hub = st.sidebar.selectbox("Choose a Hub", sorted(df_usage["hub"].unique()))

st.title("💸 Hub Monetization Insights Dashboard")

tabs = st.tabs(["📊 Overview", "🌍 Geo View", "📉 Funnel Analysis"])

# Tab 1: Overview
with tabs[0]:
    st.subheader(f"📊 Overview Metrics – {selected_hub}")
    df_filtered = df_usage[df_usage["hub"] == selected_hub]
    col1, col2, col3 = st.columns(3)
    col1.metric("Customers", len(df_filtered))
    col2.metric("Avg MRR", f"${df_filtered['monthly_recurring_revenue'].mean():.2f}")
    col3.metric("Avg Lifetime (Months)", f"{df_filtered['months_active'].mean():.1f}")
    fig = px.histogram(df_filtered, x="months_active", nbins=20)
    fig.update_layout(xaxis_title="Months Active", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Geo View
with tabs[1]:
    st.subheader("🌍 Geographic Customer Distribution")
    geo_mode = st.radio("Map Mode", ["Global", "USA States"], horizontal=True)

    if geo_mode == "Global":
        df_geo = df_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
        fig_map = go.Figure(data=go.Scattergeo(
            locations=df_geo["country"],
            locationmode="country names",
            text=df_geo["customers"],
            marker=dict(size=df_geo["customers"] / 10, color='rgba(44,102,180,0.6)', line=dict(width=0.5, color="black"))
        ))
        fig_map.update_layout(geo=dict(showland=True, landcolor='lightgray', lakecolor='white', showlakes=True), title="Customer Distribution by Country")
        st.plotly_chart(fig_map, use_container_width=True)

    else:
        df_us = df_usage.groupby("state").agg(customers=("customer_id", "count")).reset_index()
        fig_map = go.Figure(data=go.Scattergeo(
            locations=df_us["state"],
            locationmode="USA-states",
            scope="usa",
            text=df_us["customers"],
            marker=dict(size=df_us["customers"] / 10, color='rgba(44,102,180,0.6)', line=dict(width=0.5, color="black"))
        ))
        fig_map.update_layout(geo=dict(showland=True, landcolor='lightgray', lakecolor='white', showlakes=True), title="Customer Distribution by U.S. State")
        st.plotly_chart(fig_map, use_container_width=True)

# Tab 3: Funnel
with tabs[2]:
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

    fig_funnel = px.funnel(df_sorted, x="count", y="stage", title=f"Customer Funnel – {selected_val}")
    fig_funnel.update_layout(yaxis_title="Funnel Stage", xaxis_title="User Count")
    st.plotly_chart(fig_funnel, use_container_width=True)
