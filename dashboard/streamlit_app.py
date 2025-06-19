import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --- 1. Data Loading ---
@st.cache_data
def load_data():
    """
    Loads all necessary dataframes.
    Handles cases where optional data files might not exist gracefully.
    """
    try:
        df_usage = pd.read_csv("data/usage_data.csv")
    except FileNotFoundError:
        st.error("Error: usage_data.csv not found. Please ensure the 'data' directory and file exist.")
        st.stop() # Stop the app if core data is missing

    try:
        df_funnel = pd.read_csv("data/funnel_data.csv")
    except FileNotFoundError:
        st.warning("funnel_data.csv not found. Funnel Analysis might be limited to df_usage only.")
        df_funnel = pd.DataFrame() # Provide empty df if file is missing

    df_elasticity = pd.read_csv("data/pricing_elasticity.csv") if Path("data/pricing_elasticity.csv").exists() else pd.DataFrame()
    df_treemap = pd.read_csv("data/ltv_treemap.csv") if Path("data/ltv_treemap.csv").exists() else pd.DataFrame()
    df_competition = pd.read_csv("data/competitive_pricing.csv") if Path("data/competitive_pricing.csv").exists() else pd.DataFrame()

    return df_usage, df_funnel, df_elasticity, df_treemap, df_competition

# Load dataframes once
df_usage, df_funnel, df_elasticity, df_treemap, df_competition = load_data()

# --- 2. Streamlit Page Configuration ---
st.set_page_config(page_title="Hub Monetization Insights", page_icon="💸", layout="wide")

# --- 3. Sidebar Filters ---
st.sidebar.title("Hub Filters")

# Check if 'hub' column exists before sorting and selecting
if not df_usage.empty and "hub" in df_usage.columns:
    unique_hubs = sorted(df_usage["hub"].unique())
    selected_hub = st.sidebar.selectbox("Choose a Hub", unique_hubs)
else:
    selected_hub = None
    st.sidebar.warning("No 'hub' data found in usage data.")

# Check if 'tier' column exists before sorting and selecting
if not df_usage.empty and "tier" in df_usage.columns:
    unique_tiers = sorted(df_usage["tier"].unique())
    selected_tier = st.sidebar.selectbox("Choose a Tier", unique_tiers)
else:
    selected_tier = None
    st.sidebar.warning("No 'tier' data found in usage data.")

# --- 4. Main Dashboard Title ---
st.title("💸 Hub Monetization Insights Dashboard")

# --- 5. Tab Navigation ---
tabs = st.tabs([
    "📊 Overview", "💵 Pricing Elasticity", "📈 LTV Treemap",
    "🌍 Geo View", "📉 Funnel Analysis", "🏁 Competitors", "🧠 Recommendations"
])

# --- 6. Tab Content: Overview ---
with tabs[0]:
    if selected_hub and selected_tier:
        st.subheader(f"📊 Overview Metrics – {selected_hub} / {selected_tier}")
        # Filter data based on sidebar selections
        filtered_overview = df_usage[
            (df_usage["hub"] == selected_hub) & (df_usage["tier"] == selected_tier)
        ]

        if not filtered_overview.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Customers", len(filtered_overview))
            col2.metric("Avg MRR", f"${filtered_overview['monthly_recurring_revenue'].mean():.2f}")
            col3.metric("Avg Lifetime (Months)", f"{filtered_overview['months_active'].mean():.1f}")

            # Customer Tenure Distribution Histogram
            # Added text_auto=True to show counts on bars for better visibility
            fig1 = px.histogram(filtered_overview, x="months_active", nbins=20,
                                title="Customer Tenure Distribution",
                                text_auto=True) # Added text_auto for labels
            fig1.update_layout(xaxis_title="Months Active", yaxis_title="Count")
            fig1.update_traces(textposition='outside') # Position text outside bars
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info(f"No data available for {selected_hub} / {selected_tier} in the overview.")
    else:
        st.info("Please select a Hub and Tier from the sidebar to view overview metrics.")

# --- 7. Tab Content: Pricing Elasticity ---
with tabs[1]:
    st.subheader("💵 Price Elasticity Curve")
    if not df_elasticity.empty and selected_hub and selected_tier:
        elastic_filtered = df_elasticity[
            (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
        ]
        if not elastic_filtered.empty:
            # Added text_auto=True to show adoption rates on the line points
            fig2 = px.line(elastic_filtered, x="price", y="adoption_rate", markers=True,
                           title=f"Adoption Rate vs Price for {selected_hub} - {selected_tier}",
                           text_auto=True) # Added text_auto for labels on line chart
            fig2.update_layout(xaxis_title="Price (USD)", yaxis_title="Adoption Rate")
            fig2.update_traces(textposition='top center') # Position text above markers
            st.plotly_chart(fig2, use_container_width=True)

            # Optional: Display elasticity coefficient if available
            if 'elasticity_coefficient' in elastic_filtered.columns and not elastic_filtered['elasticity_coefficient'].isna().all():
                st.info(f"💡 **Price Elasticity Coefficient**: {elastic_filtered['elasticity_coefficient'].iloc[0]:.2f} "
                        f"(A value less than -1 suggests elastic demand, where price changes significantly impact adoption.)")
        else:
            st.info(f"No elasticity data available for {selected_hub} / {selected_tier}.")
    else:
        st.info("Elasticity data not available or Hub/Tier not selected.")

# --- 8. Tab Content: LTV Treemap ---
with tabs[2]:
    st.subheader("📈 Lifetime Value Treemap")
    if not df_treemap.empty:
        fig3 = px.treemap(df_treemap, path=["hub", "tier"], values="avg_ltv",
                          title="Average LTV Contribution by Product Line")
        # Ensure textinfo shows both label and value clearly
        fig3.update_traces(textinfo="label+value", texttemplate="%{label}<br>$%{value:.2s}")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("""
        **LTV Treemap Insights:**
        - Larger rectangles indicate higher Average Lifetime Value.
        - Click on a 'Hub' to drill down into its 'Tiers'.
        - Use this to identify your most valuable product segments.
        """)
    else:
        st.info("LTV Treemap data not available.")

# --- 9. Tab Content: Geo View ---
with tabs[3]:
    st.subheader("🌍 Geographic Customer Distribution")
    geo_mode = st.radio("Map Mode", ["Global", "USA States"], horizontal=True)

    if geo_mode == "Global":
        if not df_usage.empty and "country" in df_usage.columns:
            geo_data = df_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
            fig4 = go.Figure(data=go.Scattergeo(
                locations=geo_data['country'],
                locationmode="country names",
                text=geo_data['customers'].astype(str) + ' customers', # Added descriptive text for hover
                marker=dict(
                    size=geo_data['customers'] / 10 + 5,  # Add minimum size for small counts
                    color='rgba(44, 102, 180, 0.6)',
                    line=dict(color='black', width=0.5)
                ),
                hovertemplate="<b>%{location}</b><br>Customers: %{text}<extra></extra>" # Improved hover template
            ))
            fig4.update_layout(title_text="Customer Distribution by Country", geo=dict(
                showland=True, landcolor='lightgray', showlakes=True, lakecolor='white'
            ))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No global geographic data available in usage data.")

    else:  # USA States mode
        if not df_usage.empty and "country" in df_usage.columns:
            us_only_data = df_usage[df_usage["country"] == "United States"]

            if not us_only_data.empty:
                if "state" in us_only_data.columns:
                    us_only_data.loc[:, "state"] = us_only_data["state"].astype(str).str.strip().str.upper()

                geo_data = us_only_data[us_only_data["state"].notna()]
                geo_data = geo_data.groupby("state").agg(customers=("customer_id", "count")).reset_index()

                valid_states = {
                    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
                }

                geo_data = geo_data[
                    (geo_data["state"].str.len() == 2) &
                    (geo_data["state"].isin(valid_states))
                ]

                if not geo_data.empty:
                    geo_data.loc[:, "state"] = geo_data["state"].str.upper()

                    fig4 = go.Figure(data=go.Scattergeo(
                        locations=geo_data['state'],
                        locationmode="USA-states",
                        text=geo_data['customers'].astype(str) + ' customers', # Added descriptive text for hover
                        marker=dict(
                            size=geo_data['customers'] / 2 + 8,
                            color='rgba(44, 102, 180, 0.6)',
                            line=dict(color='black', width=0.5)
                        ),
                        hovertemplate="<b>%{location}</b><br>Customers: %{text}<extra></extra>" # Improved hover template
                    ))
                    fig4.update_layout(
                        title_text="Customer Distribution by U.S. State",
                        geo=dict(
                            scope="usa",
                            showland=True,
                            landcolor='lightgray',
                            showlakes=True,
                            lakecolor='white'
                        )
                    )
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.warning("No valid U.S. state data available for visualization after filtering.")
            else:
                st.warning("No customer data for 'United States' found for state-level visualization.")
        else:
            st.info("No geographic data available in usage data.")

# --- 10. Tab Content: Funnel Analysis ---
with tabs[4]:
    st.subheader("📉 Conversion Funnel Analysis")

    compare_by = st.radio("Compare Funnel By:", ["Hub", "Tier", "Country"], horizontal=True)

    stage_order = ["Visitor", "Signup", "Trial", "Paid"]

    if compare_by == "Hub":
        if not df_funnel.empty and "hub" in df_funnel.columns:
            selected_hub_funnel = st.selectbox("Select Hub to Analyze", sorted(df_funnel["hub"].unique()), key="funnel_hub_select")
            funnel_filtered = df_funnel[df_funnel["hub"] == selected_hub_funnel].copy()

            funnel_filtered.loc[:, "stage"] = pd.Categorical(funnel_filtered["stage"], categories=stage_order, ordered=True)
            funnel_sorted = funnel_filtered.sort_values("stage")

            if not funnel_sorted.empty:
                stage_counts = funnel_sorted.set_index("stage")["count"]

                visitor_count = stage_counts.get("Visitor", 0)
                signup_count = stage_counts.get("Signup", 0)
                trial_count = stage_counts.get("Trial", 0)
                paid_count = stage_counts.get("Paid", 0)

                signup_rate = (signup_count / visitor_count * 100) if visitor_count > 0 else 0
                trial_rate = (trial_count / signup_count * 100) if signup_count > 0 else 0
                paid_rate = (paid_count / trial_count * 100) if trial_count > 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric("Visitor → Signup", f"{signup_rate:.1f}%",
                            help="Percentage of unique visitors who complete signup.")
                col2.metric("Signup → Trial", f"{trial_rate:.1f}%",
                            help="Percentage of signed-up users who start a trial.")
                col3.metric("Trial → Paid", f"{paid_rate:.1f}%",
                            help="Percentage of trial users who convert to paid customers.")

                # Added text_auto=True to show counts on funnel bars
                fig5 = px.funnel(funnel_sorted, x="count", y="stage",
                                 title=f"Customer Acquisition Funnel – {selected_hub_funnel}",
                                 text_auto=True) # Added text_auto for labels
                fig5.update_layout(
                    yaxis_title="Funnel Stage",
                    xaxis_title="Customer Count",
                    yaxis={'categoryorder': 'array', 'categoryarray': stage_order}
                )
                st.plotly_chart(fig5, use_container_width=True)

                overall_conversion = (paid_count / visitor_count * 100) if visitor_count > 0 else 0
                st.info(f"📊 **Overall Conversion Rate**: {overall_conversion:.2f}% of visitors become paid customers.")
            else:
                st.info(f"No funnel data available for '{selected_hub_funnel}' in the 'funnel_data.csv' file.")
        else:
            st.info("Funnel data by Hub is not available (funnel_data.csv might be empty or missing 'hub' column).")

    elif compare_by == "Tier":
        if not df_usage.empty and "tier" in df_usage.columns and "stage" in df_usage.columns:
            selected_tier_funnel = st.selectbox("Select Tier to Analyze", sorted(df_usage["tier"].unique()), key="funnel_tier_select")

            tier_data = df_usage[df_usage["tier"] == selected_tier_funnel].copy()
            tier_funnel = tier_data.groupby("stage").size().reset_index(name="count")
            tier_funnel.loc[:, "stage"] = pd.Categorical(tier_funnel["stage"], categories=stage_order, ordered=True)
            tier_funnel = tier_funnel.sort_values("stage")

            if not tier_funnel.empty:
                stage_counts = tier_funnel.set_index("stage")["count"]

                visitor_count = stage_counts.get("Visitor", 0)
                signup_count = stage_counts.get("Signup", 0)
                trial_count = stage_counts.get("Trial", 0)
                paid_count = stage_counts.get("Paid", 0)

                signup_rate = (signup_count / visitor_count * 100) if visitor_count > 0 else 0
                trial_rate = (trial_count / signup_count * 100) if signup_count > 0 else 0
                paid_rate = (paid_count / trial_count * 100) if trial_count > 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric("Visitor → Signup", f"{signup_rate:.1f}%")
                col2.metric("Signup → Trial", f"{trial_rate:.1f}%")
                col3.metric("Trial → Paid", f"{paid_rate:.1f}%")

                # Added text_auto=True to show counts on funnel bars
                fig5 = px.funnel(tier_funnel, x="count", y="stage",
                                 title=f"Conversion Funnel – {selected_tier_funnel} Tier",
                                 text_auto=True) # Added text_auto for labels
                fig5.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': stage_order})
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info(f"No usage data available for '{selected_tier_funnel}' tier to build a funnel.")
        else:
            st.info("Usage data is required for Tier funnel analysis and is either empty or missing 'tier'/'stage' columns.")

    else:  # Country analysis
        if not df_usage.empty and "country" in df_usage.columns and "stage" in df_usage.columns:
            selected_country_funnel = st.selectbox("Select Country to Analyze", sorted(df_usage["country"].unique()), key="funnel_country_select")

            country_data = df_usage[df_usage["country"] == selected_country_funnel].copy()
            country_funnel = country_data.groupby("stage").size().reset_index(name="count")
            country_funnel.loc[:, "stage"] = pd.Categorical(country_funnel["stage"], categories=stage_order, ordered=True)
            country_funnel = country_funnel.sort_values("stage")

            if not country_funnel.empty:
                stage_counts = country_funnel.set_index("stage")["count"]

                visitor_count = stage_counts.get("Visitor", 0)
                signup_count = stage_counts.get("Signup", 0)
                trial_count = stage_counts.get("Trial", 0)
                paid_count = stage_counts.get("Paid", 0)

                signup_rate = (signup_count / visitor_count * 100) if visitor_count > 0 else 0
                trial_rate = (trial_count / signup_count * 100) if signup_count > 0 else 0 # Corrected: should be from signup_count
                paid_rate = (paid_count / trial_count * 100) if trial_count > 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric("Visitor → Signup", f"{signup_rate:.1f}%")
                col2.metric("Signup → Trial", f"{trial_rate:.1f}%")
                col3.metric("Trial → Paid", f"{paid_rate:.1f}%")

                # Added text_auto=True to show counts on funnel bars
                fig5 = px.funnel(country_funnel, x="count", y="stage",
                                 title=f"Conversion Funnel – {selected_country_funnel}",
                                 text_auto=True) # Added text_auto for labels
                fig5.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': stage_order})
                st.plotly_chart(fig5, use_container_width=True)

                # Show geographic insights
                if selected_country_funnel == "United States":
                    st.info("🇺🇸 US market shows strong trial adoption - consider premium tier promotions.")
                elif selected_country_funnel in ["United Kingdom", "Germany"]:
                    st.info("🇪🇺 European markets - consider GDPR-compliant onboarding optimizations.")
                elif selected_country_funnel in ["India", "Australia"]:
                    st.info("🌏 Asia-Pacific regions - evaluate pricing sensitivity and local payment methods.")
            else:
                st.info(f"No usage data available for '{selected_country_funnel}' to build a funnel.")
        else:
            st.info("Usage data is required for Country funnel analysis and is either empty or missing 'country'/'stage' columns.")


# --- 11. Tab Content: Competitive Price Benchmark ---
with tabs[5]:
    st.subheader("🏁 Competitive Price Benchmark")
    if not df_competition.empty and selected_hub and selected_tier:
        df_comp = df_competition[
            (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
        ].copy() # Use .copy() to avoid SettingWithCopyWarning

        if not df_comp.empty:
            # Ensure 'price_usd' is numeric
            df_comp['price_usd'] = pd.to_numeric(df_comp['price_usd'], errors='coerce')
            df_comp.dropna(subset=['price_usd'], inplace=True)

            if not df_comp.empty:
                # Added text_auto=True to show price values on bars
                fig6 = px.bar(df_comp, x="vendor", y="price_usd", color="vendor",
                              title=f"Vendor Pricing for {selected_hub} - {selected_tier}",
                              text_auto=True) # Added text_auto for labels
                fig6.update_layout(xaxis_title="Vendor", yaxis_title="Price (USD)")
                st.plotly_chart(fig6, use_container_width=True)

                st.markdown(f"""
                **Competitive Pricing Insights for {selected_hub} - {selected_tier}:**
                - Compare your product's price against competitors for the selected hub and tier.
                - Are you priced competitively? Higher pricing might require strong value proposition.
                """)
            else:
                st.info(f"No valid competitive pricing data for {selected_hub} / {selected_tier} after cleaning.")
        else:
            st.info(f"No competitive pricing data available for {selected_hub} / {selected_tier}.")
    else:
        st.info("Competitive pricing data not available or Hub/Tier not selected.")

# --- 12. Tab Content: Recommendations ---
with tabs[6]:
    st.subheader("🧠 Pricing Strategy Recommendations")
    st.markdown(f"""
    Based on selected filters: **{selected_hub or 'N/A'} – {selected_tier or 'N/A'}**

    - 💡 **Elasticity Analysis**: If your product's price elasticity is high (e.g., coefficient < -1), even small price increases can significantly reduce adoption. Consider the optimal price point indicated by the elasticity curve.
    - 📦 **Bundling & Upselling**: For the **{selected_tier or 'Starter'}** tier, consider bundling with complementary features (e.g., CMS) to increase perceived value and improve retention. For **{selected_hub or 'your products'}**, explore opportunities for enterprise upsells if the LTV analysis shows higher value in larger accounts.
    - 📈 **Market Expansion**: In regions with high visitor but low conversion rates (from Funnel Analysis), investigate localized marketing, user experience improvements, or regional pricing adjustments.
    - 🌍 **Geographic Discounts**: If the Geo View shows strong customer presence in price-sensitive countries, evaluate implementing regional discounts or localized payment methods to boost conversion.

    _These are general strategic recommendations. For precise actions, further deep-dive analysis into specific data segments is advised._
    """)
