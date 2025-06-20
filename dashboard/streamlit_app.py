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

# Initialize filter variables
selected_hub = None
selected_tier = None
selected_country = "All Countries" # Default value
min_mrr, max_mrr = None, None
min_months, max_months = None, None
selected_vendors = [] # Default empty list

# Hub selection
if not df_usage.empty and "hub" in df_usage.columns:
    unique_hubs = sorted(df_usage["hub"].unique())
    selected_hub = st.sidebar.selectbox("Choose a Hub", unique_hubs)
else:
    st.sidebar.warning("No 'hub' data found in usage data.")

# Tier selection
if not df_usage.empty and "tier" in df_usage.columns:
    unique_tiers = sorted(df_usage["tier"].unique())
    selected_tier = st.sidebar.selectbox("Choose a Tier", unique_tiers)
else:
    st.sidebar.warning("No 'tier' data found in usage data.")

# New: Country Filter (Global)
if not df_usage.empty and "country" in df_usage.columns:
    unique_countries = sorted(df_usage["country"].unique())
    selected_country = st.sidebar.selectbox(
        "Choose a Country",
        ["All Countries"] + unique_countries # Add "All Countries" option
    )
else:
    st.sidebar.info("Country data not available for filtering.")


# Monthly Recurring Revenue (MRR) Filter
if not df_usage.empty and "monthly_recurring_revenue" in df_usage.columns:
    df_usage['monthly_recurring_revenue'] = pd.to_numeric(df_usage['monthly_recurring_revenue'], errors='coerce')
    df_usage.dropna(subset=['monthly_recurring_revenue'], inplace=True)

    if not df_usage.empty:
        min_mrr_val = float(df_usage["monthly_recurring_revenue"].min())
        max_mrr_val = float(df_usage["monthly_recurring_revenue"].max())
        mrr_range = st.sidebar.slider(
            "MRR Range ($)",
            min_value=min_mrr_val,
            max_value=max_mrr_val,
            value=(min_mrr_val, max_mrr_val),
            format="$%.2f"
        )
        min_mrr, max_mrr = mrr_range
    else:
        st.sidebar.info("MRR data not available for filtering after cleaning.")
else:
    st.sidebar.info("MRR data not available for filtering.")

# Months Active Filter
if not df_usage.empty and "months_active" in df_usage.columns:
    df_usage['months_active'] = pd.to_numeric(df_usage['months_active'], errors='coerce')
    df_usage.dropna(subset=['months_active'], inplace=True)

    if not df_usage.empty:
        min_months_val = int(df_usage["months_active"].min())
        max_months_val = int(df_usage["months_active"].max())
        months_active_range = st.sidebar.slider(
            "Months Active Range",
            min_value=min_months_val,
            max_value=max_months_val,
            value=(min_months_val, max_months_val)
        )
        min_months, max_months = months_active_range
    else:
        st.sidebar.info("Months Active data not available for filtering after cleaning.")
else:
    st.sidebar.info("Months Active data not available for filtering.")

# New: Vendor Filter (for Competitive Pricing)
if not df_competition.empty and "vendor" in df_competition.columns:
    unique_vendors = sorted(df_competition["vendor"].unique())
    selected_vendors = st.sidebar.multiselect(
        "Select Vendors (Competitive Pricing)",
        unique_vendors,
        default=unique_vendors # Default to all selected
    )
else:
    st.sidebar.info("Vendor data not available for filtering.")

# --- 4. Main Dashboard Title ---
st.title("💸 Hub Monetization Insights Dashboard")

# --- 5. Tab Navigation ---
tabs = st.tabs([
    "📊 Overview", "💵 Pricing Elasticity", "📈 LTV Treemap",
    "🌍 Geo View", "📉 Funnel Analysis", "🏁 Competitors", "🧠 Recommendations"
])

# --- Helper function to apply global filters to df_usage ---
def apply_global_filters(dataframe):
    filtered_df = dataframe.copy()

    if selected_hub and "hub" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["hub"] == selected_hub]
    if selected_tier and "tier" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["tier"] == selected_tier]
    # Apply new Country filter
    if selected_country != "All Countries" and "country" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["country"] == selected_country]
    if min_mrr is not None and max_mrr is not None and "monthly_recurring_revenue" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["monthly_recurring_revenue"] >= min_mrr) &
            (filtered_df["monthly_recurring_revenue"] <= max_mrr)
        ]
    if min_months is not None and max_months is not None and "months_active" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["months_active"] >= min_months) &
            (filtered_df["months_active"] <= max_months)
        ]
    return filtered_df


# --- 6. Tab Content: Overview ---
with tabs[0]:
    st.subheader(f"📊 Overview Metrics – {selected_hub or 'All Hubs'} / {selected_tier or 'All Tiers'}")

    filtered_overview = apply_global_filters(df_usage)

    if not filtered_overview.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Customers", len(filtered_overview))
        col2.metric("Avg MRR", f"${filtered_overview['monthly_recurring_revenue'].mean():.2f}")
        col3.metric("Avg Lifetime (Months)", f"{filtered_overview['months_active'].mean():.1f}")

        fig1 = px.histogram(filtered_overview, x="months_active", nbins=20,
                            title="Customer Tenure Distribution",
                            text_auto=True)
        fig1.update_layout(xaxis_title="Months Active", yaxis_title="Count")
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available with the selected filters for Overview.")

# --- 7. Tab Content: Pricing Elasticity ---
with tabs[1]:
    st.subheader("💵 Price Elasticity Curve")
    if not df_elasticity.empty and selected_hub and selected_tier:
        # Elasticity data is often pre-calculated or not directly tied to individual customer MRR/months_active/country.
        # We apply hub/tier filter but not MRR/Months Active or Country to this specific data.
        elastic_filtered = df_elasticity[
            (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
        ]
        if not elastic_filtered.empty:
            fig2 = px.line(elastic_filtered, x="price", y="adoption_rate", markers=True,
                           title=f"Adoption Rate vs Price for {selected_hub} - {selected_tier}",
                           text=elastic_filtered['adoption_rate'].round(2))
            fig2.update_layout(xaxis_title="Price (USD)", yaxis_title="Adoption Rate")
            fig2.update_traces(textposition='top center')
            st.plotly_chart(fig2, use_container_width=True)

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
        # LTV treemap is typically for overall product lines, not filtered by customer-level MRR/Months Active/Country
        fig3 = px.treemap(df_treemap, path=["hub", "tier"], values="avg_ltv",
                          title="Average LTV Contribution by Product Line")
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

    # Apply global filters to df_usage before processing for geo data
    filtered_geo_usage = apply_global_filters(df_usage)

    if geo_mode == "Global":
        if not filtered_geo_usage.empty and "country" in filtered_geo_usage.columns:
            geo_data = filtered_geo_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
            if not geo_data.empty:
                fig4 = go.Figure(data=go.Scattergeo(
                    locations=geo_data['country'],
                    locationmode="country names",
                    text=geo_data['customers'].astype(str) + ' customers',
                    marker=dict(
                        size=geo_data['customers'] / 10 + 5,
                        color='rgba(44, 102, 180, 0.6)',
                        line=dict(color='black', width=0.5)
                    ),
                    hovertemplate="<b>%{location}</b><br>Customers: %{text}<extra></extra>"
                ))
                fig4.update_layout(title_text="Customer Distribution by Country", geo=dict(
                    showland=True, landcolor='lightgray', showlakes=True, lakecolor='white'
                ))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No global geographic data available with the selected filters.")
        else:
            st.info("No geographic data available in usage data after applying filters.")

    else:  # USA States mode
        if not filtered_geo_usage.empty and "country" in filtered_geo_usage.columns:
            us_only_data = filtered_geo_usage[filtered_geo_usage["country"] == "United States"]

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
                        text=geo_data['customers'].astype(str) + ' customers',
                        marker=dict(
                            size=geo_data['customers'] / 2 + 8,
                            color='rgba(44, 102, 180, 0.6)',
                            line=dict(color='black', width=0.5)
                        ),
                        hovertemplate="<b>%{location}</b><br>Customers: %{text}<extra></extra>"
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
                st.warning("No customer data for 'United States' found after applying filters.")
        else:
            st.info("No geographic data available in usage data after applying filters.")

# --- 10. Tab Content: Funnel Analysis ---
with tabs[4]:
    st.subheader("📉 Conversion Funnel Analysis")

    compare_by = st.radio("Compare Funnel By:", ["Hub", "Tier", "Country"], horizontal=True)

    stage_order = ["Visitor", "Signup", "Trial", "Paid"]

    if compare_by == "Hub":
        # Funnel data by Hub uses df_funnel directly, which is assumed to be pre-aggregated
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

                fig5 = px.funnel(funnel_sorted, x="count", y="stage",
                                 title=f"Customer Acquisition Funnel – {selected_hub_funnel}",
                                 text_auto=True)
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
        # Funnel data by Tier uses df_usage, so apply global filters
        filtered_funnel_usage = apply_global_filters(df_usage) # This now includes the global country filter
        if not filtered_funnel_usage.empty and "tier" in filtered_funnel_usage.columns and "stage" in filtered_funnel_usage.columns:
            selected_tier_funnel = st.selectbox("Select Tier to Analyze", sorted(filtered_funnel_usage["tier"].unique()), key="funnel_tier_select")

            tier_data = filtered_funnel_usage[filtered_funnel_usage["tier"] == selected_tier_funnel].copy()
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

                fig5 = px.funnel(tier_funnel, x="count", y="stage",
                                 title=f"Conversion Funnel – {selected_tier_funnel} Tier",
                                 text_auto=True)
                fig5.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': stage_order})
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info(f"No usage data available for '{selected_tier_funnel}' tier with the selected filters to build a funnel.")
        else:
            st.info("Usage data is required for Tier funnel analysis and is either empty or missing 'tier'/'stage' columns, or no data after filters.")

    else:  # Country analysis
        # Funnel data by Country uses df_usage, so apply global filters
        filtered_funnel_usage = apply_global_filters(df_usage) # This now includes the global country filter
        if not filtered_funnel_usage.empty and "country" in filtered_funnel_usage.columns and "stage" in filtered_funnel_usage.columns:
            # The local selectbox for country should only show options from the already filtered data
            available_countries = sorted(filtered_funnel_usage["country"].unique())
            selected_country_funnel = st.selectbox("Select Country to Analyze", available_countries, key="funnel_country_select")

            country_data = filtered_funnel_usage[filtered_funnel_usage["country"] == selected_country_funnel].copy()
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
                trial_rate = (trial_count / signup_count * 100) if signup_count > 0 else 0
                paid_rate = (paid_count / trial_count * 100) if trial_count > 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric("Visitor → Signup", f"{signup_rate:.1f}%")
                col2.metric("Signup → Trial", f"{trial_rate:.1f}%")
                col3.metric("Trial → Paid", f"{paid_rate:.1f}%")

                fig5 = px.funnel(country_funnel, x="count", y="stage",
                                 title=f"Conversion Funnel – {selected_country_funnel}",
                                 text_auto=True)
                fig5.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': stage_order})
                st.plotly_chart(fig5, use_container_width=True)

                if selected_country_funnel == "United States":
                    st.info("🇺🇸 US market shows strong trial adoption - consider premium tier promotions.")
                elif selected_country_funnel in ["United Kingdom", "Germany"]:
                    st.info("🇪🇺 European markets - consider GDPR-compliant onboarding optimizations.")
                elif selected_country_funnel in ["India", "Australia"]:
                    st.info("🌏 Asia-Pacific regions - evaluate pricing sensitivity and local payment methods.")
            else:
                st.info(f"No usage data available for '{selected_country_funnel}' with the selected filters to build a funnel.")
        else:
            st.info("Usage data is required for Country funnel analysis and is either empty or missing 'country'/'stage' columns, or no data after filters.")


# --- 11. Tab Content: Competitive Price Benchmark ---
with tabs[5]:
    st.subheader("🏁 Competitive Price Benchmark")
    if not df_competition.empty and selected_hub and selected_tier:
        df_comp = df_competition[
            (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
        ].copy()

        # Apply Vendor filter
        if selected_vendors and "vendor" in df_comp.columns:
            df_comp = df_comp[df_comp["vendor"].isin(selected_vendors)]
        elif not selected_vendors and not df_competition.empty and "vendor" in df_competition.columns:
             # If no vendors are selected in multiselect, show no data
             df_comp = pd.DataFrame()

        if not df_comp.empty:
            df_comp['price_usd'] = pd.to_numeric(df_comp['price_usd'], errors='coerce')
            df_comp.dropna(subset=['price_usd'], inplace=True)

            if not df_comp.empty:
                fig6 = px.bar(df_comp, x="vendor", y="price_usd", color="vendor",
                              title=f"Vendor Pricing for {selected_hub} - {selected_tier}",
                              text_auto=True)
                fig6.update_layout(xaxis_title="Vendor", yaxis_title="Price (USD)")
                st.plotly_chart(fig6, use_container_width=True)

                st.markdown(f"""
                **Competitive Pricing Insights for {selected_hub} - {selected_tier}:**
                - Compare your product's price against competitors for the selected hub and tier.
                - Are you priced competitively? Higher pricing might require strong value proposition.
                """)
            else:
                st.info(f"No valid competitive pricing data for {selected_hub} / {selected_tier} with selected vendors after cleaning.")
        else:
            st.info(f"No competitive pricing data available for {selected_hub} / {selected_tier} with selected vendors.")
    else:
        st.info("Competitive pricing data not available or Hub/Tier not selected.")

# --- 12. Tab Content: Recommendations ---
with tabs[6]:
    st.subheader("🧠 Pricing Strategy Recommendations")
    st.markdown(f"""
    Based on selected filters: **{selected_hub or 'N/A'} – {selected_tier or 'N/A'}**
    {(f" in **{selected_country}**" if selected_country != "All Countries" else "")}
    {(f" (MRR: ${min_mrr:.2f}-${max_mrr:.2f})" if min_mrr is not None else "")}
    {(f" (Months Active: {min_months}-{max_months})" if min_months is not None else "")}

    - 💡 **Elasticity Analysis**: If your product's price elasticity is high (e.g., coefficient < -1), even small price increases can significantly reduce adoption. Consider the optimal price point indicated by the elasticity curve.
    - 📦 **Bundling & Upselling**: For the **{selected_tier or 'Starter'}** tier, consider bundling with complementary features (e.g., CMS) to increase perceived value and improve retention. For **{selected_hub or 'your products'}**, explore opportunities for enterprise upsells if the LTV analysis shows higher value in larger accounts.
    - 📈 **Market Expansion**: In regions with high visitor but low conversion rates (from Funnel Analysis), investigate localized marketing, user experience improvements, or regional pricing adjustments.
    - 🌍 **Geographic Discounts**: If the Geo View shows strong customer presence in price-sensitive countries, evaluate implementing regional discounts or localized payment methods to boost conversion.

    _These are general strategic recommendations. For precise actions, further deep-dive analysis into specific data segments is advised._
    """)
