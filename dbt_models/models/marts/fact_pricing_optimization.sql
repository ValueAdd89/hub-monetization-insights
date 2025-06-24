import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

# --- iOS Style CSS ---
st.markdown("""
<style>
    /* Inter font is default, but adding SF Pro Display for true iOS feel */
    html, body, [class*="st-"] {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Overall app background */
    [data-testid="stAppViewContainer"] {
        background-color: #f0f2f6; /* Light gray for the entire app background */
    }
    [data-testid="stHeader"] {
        background-color: #f0f2f6; /* Ensure header matches app background */
    }
    /* Targeting specific Streamlit generated classes for content area to ensure light background */
    .st-emotion-cache-nahz7x, .st-emotion-cache-f1g6mh, .st-emotion-cache-1c7y2gy, .st-emotion-cache-q8sbsg,
    [data-testid="stVerticalBlock"] > div > div:not([data-testid="stMetric"]) {
        background-color: #f0f2f6;
        color: #333; /* Default text color for these containers */
    }
    body {
        color: #333; /* Dark gray for main text */
    }

    /* Custom iOS-style cards */
    .ios-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px); /* This will have effect in environments that support it */
    }
    
    /* Specific styling for the custom metric cards */
    .ios-metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .ios-metric-value {
        font-size: 2.2em;
        font-weight: 700;
        margin: 8px 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .ios-metric-label {
        font-size: 0.9em;
        opacity: 0.9;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .geo-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        box-shadow: 0 8px 25px rgba(116, 185, 255, 0.3);
    }
    
    .projection-card {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        box-shadow: 0 8px 25px rgba(0, 184, 148, 0.3);
    }
    
    /* Sidebar styling - applying the new gradient */
    .st-emotion-cache-10o5uaw.eczf16g1, [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); /* Added shadow for depth */
    }
    /* Sidebar specific elements text color */
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .st-emotion-cache-1jm6hrk.e1nzilhr0 {
        color: #333; /* Ensure sidebar text is dark and readable */
    }


    /* Tabs styling - applying the new gradients */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(145deg, #ffffff 0%, #f1f3f4 100%);
        border-radius: 12px;
        padding: 12px 20px;
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        color: #555; /* Default text color for inactive tabs */
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e9ecef; /* Slightly darker on hover */
    }


    /* Buttons */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 1em;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
        transition: background-color 0.2s, box-shadow 0.2s;
    }
    .stButton > button:hover {
        background-color: #0056b3;
        box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
    }
    .stButton > button:active {
        background-color: #004085;
    }

    /* Radio buttons */
    div.st-emotion-cache-1jm6hrk.e1nzilhr0 > label, .st-emotion-cache-1c7y2gy label { /* Label for radio buttons (general label target) */
        font-weight: 600;
        color: #555;
    }
    .st-emotion-cache-fzw1u6 { /* Container for radio buttons */
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #eee;
    }
    .st-emotion-cache-fzw1u6 label {
        font-weight: normal; /* Reset font weight for individual radio options */
        color: #333;
    }

    /* Slider styling */
    .stSlider > label {
        font-weight: 600;
        color: #555;
    }
    .st-emotion-cache-1j0rpk0.e1gf3k7h1, .st-emotion-cache-j9czj1 { /* Slider track */
        background: #e0e0e0;
        border-radius: 5px;
    }
    .st-emotion-cache-1gf9hbp.e1gf3k7h2, .st-emotion-cache-1kyx7h8 { /* Slider fill */
        background: #007bff;
        border-radius: 5px;
    }
    .st-emotion-cache-1ghx1h4.e1gf3k7h0, .st-emotion-cache-1xt02z6 { /* Slider thumb */
        background: #007bff;
        border: 3px solid #007bff;
        box-shadow: 0 0 0 5px rgba(0, 123, 255, 0.2);
    }

    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        font-size: 0.95em;
    }
    .stAlert > div > svg { /* Icon color */
        color: #007bff; /* Info icon */
    }
    .stAlert.st-emotion-cache-16279f0.e1f1d6z00.css-1f1d6z0.e16cqe02, .stAlert.st-emotion-cache-1dffz2m.e1f1d6z00 { /* Info box */
        background-color: #e0f2f7;
        color: #007bff;
        border-left: 5px solid #007bff;
    }
    .stAlert.st-emotion-cache-1g6x5c.e1f1d6z00.css-1f1d6z0.e16cqe02, .stAlert.st-emotion-cache-p2w9h4.e1f1d6z00 { /* Warning box */
        background-color: #fff3cd;
        color: #856404;
        border-left: 5px solid #ffc107;
    }
    .stAlert.st-emotion-cache-1s3t01j.e1f1d6z00.css-1f1d6z0.e16cqe02, .stAlert.st-emotion-cache-1g7i40m.e1f1d6z00 { /* Error box */
        background-color: #f8d7da;
        color: #721c24;
        border-left: 5px solid #dc3545;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #333;
        font-weight: 700;
        margin-bottom: 15px;
    }
    h1 { font-size: 2.2em; }
    h2 { font-size: 1.8em; }
    h3 { font-size: 1.5em; }
    /* Ensure the main title is not affected by a dark background */
    .st-emotion-cache-1vbkxwb.e1nzilhr5 { /* Class for st.title */
        color: #333 !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 1. Data Loading (incorporating new DFs and refactoring) ---
# Placeholder for connection if using actual DB. Not used for local CSVs.
# connection = None 

@st.cache_data
def load_data():
    """
    Loads all necessary dataframes, prioritizing CSVs for local development.
    Includes new dataframes: df_churn_retention and df_pricing_plans.
    """
    dfs = {}
    data_files = {
        "usage_data": "usage_data.csv",
        "funnel_data": "funnel_data.csv",
        "elasticity": "pricing_elasticity.csv",
        "competition": "competitive_pricing.csv",
        "churn_retention": "churn_retention.csv", # New
        "pricing_plans": "pricing_plans.csv",     # New
        "executive_summary": "executive_summary.csv", # New (for dbt concept)
        "customer_dimensions": "customer_dimensions.csv", # New (for dbt concept)
        "pricing_optimization": "pricing_optimization.csv", # New (for dbt concept)
        "data_quality": "data_quality.csv" # New (for dbt concept)
    }

    for df_name, file_name in data_files.items():
        file_path = Path("data") / file_name
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                # Basic cleaning for common columns
                if 'monthly_recurring_revenue' in df.columns:
                    df['monthly_recurring_revenue'] = pd.to_numeric(df['monthly_recurring_revenue'], errors='coerce')
                if 'months_active' in df.columns:
                    df['months_active'] = pd.to_numeric(df['months_active'], errors='coerce')
                if 'price_usd' in df.columns:
                    df['price_usd'] = pd.to_numeric(df['price_usd'], errors='coerce')
                # Ensure stage column is read for funnel if exists in usage_data
                if df_name == "usage_data" and "stage" not in df.columns:
                    df["stage"] = "Paid" # Default stage if not available, for funnel compatibility
                    st.warning(f"No 'stage' column in {file_name}. Defaulting all users to 'Paid' for funnel analysis.")
                
                df.dropna(inplace=True) # Drop rows with NaNs resulting from coerce
                dfs[df_name] = df
            except Exception as e:
                st.warning(f"Error loading {file_name}: {e}. Skipping this file.")
                dfs[df_name] = pd.DataFrame()
        else:
            # For specific crucial files, show an error and stop
            if df_name in ["usage_data"]:
                st.error(f"Error: {file_name} not found. Please ensure the 'data' directory and file exist.")
                st.stop()
            else:
                st.info(f"Info: {file_name} not found. Some features might be limited.")
                dfs[df_name] = pd.DataFrame()

    # Generate pricing strategy data if not found or empty after loading
    dfs['pricing_strategy'] = load_or_generate_pricing_data(dfs.get('pricing_strategy', pd.DataFrame()))
    
    return (dfs.get("usage_data"), dfs.get("funnel_data"), dfs.get("elasticity"), 
            dfs.get("competition"), dfs.get("churn_retention"), dfs.get("pricing_plans"),
            dfs.get("pricing_strategy"), dfs.get("customer_dimensions"), 
            dfs.get("subscription_metrics"), dfs.get("customer_ltv"), 
            dfs.get("pricing_optimization"), dfs.get("executive_summary"), dfs.get("data_quality"))

@st.cache_data
def load_or_generate_pricing_data(existing_df):
    """
    Load pricing strategy data or generate sample data if file doesn't exist or is invalid.
    """
    pricing_file_path = Path("data/pricing_strategy.csv")
    
    # Check if existing_df is valid or needs regeneration
    if existing_df is not None and not existing_df.empty and all(col in existing_df.columns for col in ['hub', 'tier', 'scenario', 'month', 'projected_mrr']):
        return existing_df
    
    # If not valid, attempt to load from file
    if pricing_file_path.exists():
        try:
            df = pd.read_csv(pricing_file_path)
            if not df.empty and all(col in df.columns for col in ['hub', 'tier', 'scenario', 'month', 'projected_mrr']):
                st.success("Loaded pricing_strategy.csv.")
                return df
            else:
                st.warning("pricing_strategy.csv found but appears empty or malformed. Generating new sample data.")
        except Exception as e:
            st.warning(f"Error reading pricing_strategy.csv: {e}. Generating new sample data.")
    
    # If file not found or invalid, generate new data
    return generate_sample_pricing_data_for_all()

def generate_sample_pricing_data_for_all():
    """Generates comprehensive sample pricing strategy data for all common hubs/tiers."""
    st.info("Generating new comprehensive sample pricing_strategy.csv...")
    np.random.seed(42) # Consistent seed for reproducible data

    hubs = ['CMS', 'Commerce', 'Marketing', 'Analytics', 'CRM', 'Marketing Hub', 'Sales Hub', 'Service Hub']
    tiers = ['Starter', 'Professional', 'Enterprise', 'Free', 'Basic', 'Premium']
    scenarios = ['Conservative', 'Optimistic', 'Aggressive']
    
    data = []
    base_date = datetime.now()
    
    for hub in hubs:
        for tier in tiers:
            current_price = np.random.uniform(29, 299)
            current_customers = np.random.randint(100, 1000)
            current_mrr = current_price * current_customers
            churn_rate = np.random.uniform(0.02, 0.08)
            
            for scenario in scenarios:
                if scenario == 'Conservative':
                    price_multiplier = np.random.uniform(1.0, 1.1)
                    adoption_impact = np.random.uniform(0.95, 1.02)
                elif scenario == 'Optimistic':
                    price_multiplier = np.random.uniform(1.1, 1.25)
                    adoption_impact = np.random.uniform(0.9, 1.05)
                else: # Aggressive
                    price_multiplier = np.random.uniform(1.25, 1.5)
                    adoption_impact = np.random.uniform(0.8, 0.95)
                
                projected_price_at_change = current_price * price_multiplier
                projected_customers_at_change = int(current_customers * adoption_impact)
                
                for month in range(1, 13):
                    growth_rate_monthly = (np.random.uniform(0.01, 0.05) if scenario == 'Optimistic' else 
                                           np.random.uniform(0.005, 0.03) if scenario == 'Conservative' else 
                                           np.random.uniform(0.03, 0.08))
                    
                    if month == 1:
                        monthly_customers = projected_customers_at_change
                    else:
                        # Simple compounding growth and churn
                        # To avoid relying on previous iteration in loop, recalculate for each month
                        # This is a simplified projection for sample data
                        monthly_customers = int(projected_customers_at_change * (1 + growth_rate_monthly)**(month-1) * (1-churn_rate)**(month-1))
                        monthly_customers = max(1, monthly_customers) # Ensure at least 1 customer

                    monthly_mrr = projected_price_at_change * monthly_customers
                    monthly_arr = monthly_mrr * 12
                    
                    avg_lifespan_months = 1 / churn_rate if churn_rate > 0 else 1000 # Avoid division by zero
                    ltv = projected_price_at_change * avg_lifespan_months
                    
                    cac = np.random.uniform(50, 200) * (1.2 if scenario == 'Aggressive' else 1.0)
                    ltv_cac_ratio = ltv / cac if cac > 0 else ltv # Avoid division by zero
                    
                    new_customer_revenue = np.random.uniform(0.1, 0.3) * monthly_mrr
                    expansion_revenue = np.random.uniform(0.05, 0.15) * monthly_mrr
                    
                    data.append({
                        'hub': hub,
                        'tier': tier,
                        'scenario': scenario,
                        'month': month,
                        'date': (base_date + timedelta(days=30*month)).strftime('%Y-%m-%d'),
                        'current_price': current_price, # Actual original price
                        'projected_price': projected_price_at_change, # Price after change is applied for scenario
                        'current_customers': current_customers, # Actual original customers
                        'projected_customers': monthly_customers,
                        'current_mrr': current_mrr, # Actual original MRR
                        'projected_mrr': monthly_mrr,
                        'projected_arr': monthly_arr,
                        'churn_rate': churn_rate,
                        'ltv': ltv,
                        'cac': cac,
                        'ltv_cac_ratio': ltv_cac_ratio,
                        'new_customer_revenue': new_customer_revenue,
                        'expansion_revenue': expansion_revenue,
                        'price_elasticity': np.random.uniform(-2.5, -0.5),
                        'market_penetration': np.random.uniform(0.05, 0.25),
                        'competitive_position': np.random.choice(['Leading', 'Competitive', 'Behind'])
                    })
    
    df = pd.DataFrame(data)
    Path("data").mkdir(exist_ok=True)
    df.to_csv(pricing_file_path, index=False)
    return df


# Load dataframes once
(df_usage, df_funnel, df_elasticity, df_competition, df_churn_retention, df_pricing_plans, 
 df_pricing_strategy, df_customer_dim, df_subscription_metrics, df_customer_ltv, 
 df_pricing_optimization, df_executive_summary, df_data_quality) = load_data()


# --- 2. Streamlit Page Configuration ---
st.set_page_config(page_title="Hub Monetization Insights", page_icon="💸", layout="wide")

# --- 3. Sidebar Filters ---
st.sidebar.title("🎛️ Hub Filters")

# Initialize filter variables
selected_hub = None
selected_tier = None
selected_country = "All Countries"
selected_vendor = "All Vendors"
min_mrr, max_mrr = None, None
min_months, max_months = None, None

# Combine unique hubs and tiers from available dataframes for sidebar filters
all_hubs_set = set()
if not df_usage.empty and "hub" in df_usage.columns:
    all_hubs_set.update(df_usage["hub"].unique())
if not df_pricing_strategy.empty and "hub" in df_pricing_strategy.columns:
    all_hubs_set.update(df_pricing_strategy["hub"].unique())
if not df_pricing_plans.empty and "hub" in df_pricing_plans.columns:
    all_hubs_set.update(df_pricing_plans["hub"].unique())
all_hubs = sorted(list(all_hubs_set))

all_tiers_set = set()
if not df_usage.empty and "tier" in df_usage.columns:
    all_tiers_set.update(df_usage["tier"].unique())
if not df_pricing_strategy.empty and "tier" in df_pricing_strategy.columns:
    all_tiers_set.update(df_pricing_strategy["tier"].unique())
if not df_pricing_plans.empty and "tier" in df_pricing_plans.columns:
    all_tiers_set.update(df_pricing_plans["tier"].unique())
all_tiers = sorted(list(all_tiers_set))


# Hub selection
if all_hubs:
    selected_hub = st.sidebar.selectbox("🏢 Choose a Hub", all_hubs)
else:
    st.sidebar.warning("No 'hub' data found across all relevant datasets.")

# Tier selection
if all_tiers:
    selected_tier = st.sidebar.selectbox("🎯 Choose a Tier", all_tiers)
else:
    st.sidebar.warning("No 'tier' data found across all relevant datasets.")


# Country Filter (Global)
if not df_usage.empty and "country" in df_usage.columns:
    unique_countries = sorted(df_usage["country"].unique())
    selected_country = st.sidebar.selectbox(
        "🌍 Choose a Country",
        ["All Countries"] + unique_countries
    )
else:
    st.sidebar.info("Country data not available for filtering.")

# Vendor Filter
if not df_competition.empty and "vendor" in df_competition.columns:
    unique_vendors = sorted(df_competition["vendor"].unique())
    selected_vendor = st.sidebar.selectbox(
        "🏪 Select Vendor",
        ["All Vendors"] + unique_vendors
    )
else:
    st.sidebar.info("Vendor data not available for filtering.")

# MRR Filter
if not df_usage.empty and "monthly_recurring_revenue" in df_usage.columns:
    # After cleaning (dropna), check if df_usage is still not empty
    if not df_usage.empty and 'monthly_recurring_revenue' in df_usage.columns:
        min_mrr_val = float(df_usage["monthly_recurring_revenue"].min())
        max_mrr_val = float(df_usage["monthly_recurring_revenue"].max())
        # Handle case where min_mrr_val and max_mrr_val might be equal (e.g., only one data point)
        if min_mrr_val == max_mrr_val:
            mrr_range = st.sidebar.slider(
                "💰 MRR Range ($)",
                min_value=min_mrr_val,
                max_value=max_mrr_val + 1.0, # Add a small buffer to make it a range
                value=(min_mrr_val, max_mrr_val + 1.0),
                format="$%.2f"
            )
        else:
            mrr_range = st.sidebar.slider(
                "💰 MRR Range ($)",
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
    # After cleaning (dropna), check if df_usage is still not empty
    if not df_usage.empty and 'months_active' in df_usage.columns:
        min_months_val = int(df_usage["months_active"].min())
        max_months_val = int(df_usage["months_active"].max())
        # Handle case where min_months_val and max_months_val might be equal
        if min_months_val == max_months_val:
            months_active_range = st.sidebar.slider(
                "📅 Months Active Range",
                min_value=min_months_val,
                max_value=max_months_val + 1, # Add a small buffer
                value=(min_months_val, max_months_val + 1)
            )
        else:
            months_active_range = st.sidebar.slider(
                "📅 Months Active Range",
                min_value=min_months_val,
                max_value=max_months_val,
                value=(min_months_val, max_months_val)
            )
        min_months, max_months = months_active_range
    else:
        st.sidebar.info("Months Active data not available for filtering after cleaning.")
else:
    st.sidebar.info("Months Active data not available for filtering.")

# --- 4. Main Dashboard Title ---
st.title("💸 Hub Monetization Insights Dashboard")
st.markdown("### Elegant insights with iOS-inspired design")

# --- 5. Tab Navigation ---
tabs = st.tabs([
    "📊 Overview", "💵 Pricing Elasticity", "🌍 Geo View", 
    "📉 Funnel Analysis", "🏁 Competitors", "📈 Pricing Strategy", "👑 Executive Summary", "🧠 Recommendations"
])

# --- Helper function to apply global filters to df_usage ---
def apply_global_filters(dataframe):
    filtered_df = dataframe.copy()

    if selected_hub and "hub" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["hub"] == selected_hub]
    if selected_tier and "tier" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["tier"] == selected_tier]
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

def create_ios_metric_card(title, value, subtitle="", color_gradient="135deg, #667eea 0%, #764ba2 100%"):
    st.markdown(f"""
    <div style="background: linear-gradient({color_gradient}); border-radius: 12px; padding: 20px; margin: 8px 0; color: white; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
        <div style="font-size: 0.9em; opacity: 0.9; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">{title}</div>
        <div style="font-size: 2.2em; font-weight: 700; margin: 8px 0; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">{value}</div>
        <div style="font-size: 0.8em; opacity: 0.8;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. Tab Content: Overview ---
with tabs[0]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader(f"📊 Overview Metrics – {selected_hub or 'All Hubs'} / {selected_tier or 'All Tiers'}")

    filtered_overview = apply_global_filters(df_usage)

    if not filtered_overview.empty:
        # KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_ios_metric_card("CUSTOMERS", f"{len(filtered_overview):,}")
        
        with col2:
            create_ios_metric_card("AVG MRR", f"${filtered_overview['monthly_recurring_revenue'].mean():.2f}", 
                                   color_gradient="135deg, #00b894 0%, #00a085 100%")
        
        with col3:
            create_ios_metric_card("AVG LIFETIME", f"{filtered_overview['months_active'].mean():.1f}mo", 
                                   color_gradient="135deg, #fd79a8 0%, #e84393 100%")

        # Visuals
        st.markdown('### Customer Tenure Distribution') # Moved title here
        fig1 = px.histogram(filtered_overview, x="months_active", nbins=20,
                            title="") # Removed title from px.histogram as it's now markdown
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"),
            title_font_size=20,
            title_font_color='#2d3436',
            xaxis=dict(gridcolor='#f0f0f0'), # Light grid lines
            yaxis=dict(gridcolor='#f0f0f0') # Light grid lines
        )
        fig1.update_traces(marker_color='rgba(102, 126, 234, 0.8)', marker_line_color='white', marker_line_width=2)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No data available with the selected filters for Overview.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. Tab Content: Pricing Elasticity ---
with tabs[1]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("💵 Price Elasticity Curve")
    
    if not df_elasticity.empty and selected_hub and selected_tier:
        elastic_filtered = df_elasticity[
            (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
        ]
        if not elastic_filtered.empty:
            # Visual
            fig2 = px.line(elastic_filtered, x="price", y="adoption_rate", markers=True,
                           title=f"Adoption Rate vs Price for {selected_hub} - {selected_tier}")
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"),
                xaxis_title="Price (USD)", yaxis_title="Adoption Rate",
                xaxis=dict(gridcolor='#f0f0f0'), # Light grid lines
                yaxis=dict(gridcolor='#f0f0f0') # Light grid lines
            )
            fig2.update_traces(line_color='rgba(102, 126, 234, 0.8)', marker_color='rgba(116, 185, 255, 1)')
            st.plotly_chart(fig2, use_container_width=True)

            # Insight/KPI
            if 'elasticity_coefficient' in elastic_filtered.columns and not elastic_filtered['elasticity_coefficient'].isna().all():
                coefficient = elastic_filtered['elasticity_coefficient'].iloc[0]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                    <h4>💡 Price Elasticity Insight</h4>
                    <p><strong>Coefficient: {coefficient:.2f}</strong></p>
                    <p>{'Elastic demand - price changes significantly impact adoption' if coefficient < -1 else 'Inelastic demand - customers less sensitive to price changes'}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No elasticity data available for {selected_hub} / {selected_tier}.")
    else:
        st.info("Elasticity data not available or Hub/Tier not selected.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. Tab Content: Geo View ---
with tabs[2]:
    st.markdown('<div class="geo-card">', unsafe_allow_html=True)
    st.subheader("🌍 Geographic Customer Distribution")
    
    # Filter/Control
    geo_mode = st.radio("Map Mode", ["Global", "USA States"], horizontal=True)
    filtered_geo_usage = apply_global_filters(df_usage)

    if geo_mode == "Global":
        if not filtered_geo_usage.empty and "country" in filtered_geo_usage.columns:
            geo_data = filtered_geo_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
            if not geo_data.empty:
                # Visual
                fig4 = go.Figure(data=go.Scattergeo(
                    locations=geo_data['country'],
                    locationmode="country names",
                    text=geo_data['customers'].astype(str) + ' customers',
                    marker=dict(
                        size=geo_data['customers'] / 10 + 5,
                        color='rgba(255, 255, 255, 0.9)',
                        line=dict(color='rgba(116, 185, 255, 1)', width=2)
                    ),
                    hovertemplate="<b>%{location}</b><br>Customers: %{text}<extra></extra>"
                ))
                fig4.update_layout(
                    title_text="Customer Distribution by Country",
                    geo=dict(showland=True, landcolor='rgba(116, 185, 255, 0.1)', 
                             showlakes=True, lakecolor='white'),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white')
                )
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No global geographic data available with the selected filters.")
        else:
            st.info("No geographic data available in usage data after applying filters.")
    else:  # USA States mode
        if not filtered_geo_usage.empty and "country" in filtered_geo_usage.columns:
            us_only_data = filtered_geo_usage[filtered_geo_usage["country"] == "United States"].copy()
            if not us_only_data.empty and "state" in us_only_data.columns:
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
                    # Visual
                    fig4 = go.Figure(data=go.Scattergeo(
                        locations=geo_data['state'],
                        locationmode="USA-states",
                        text=geo_data['customers'].astype(str) + ' customers',
                        marker=dict(
                            size=geo_data['customers'] / 2 + 8,
                            color='rgba(255, 255, 255, 0.9)',
                            line=dict(color='rgba(116, 185, 255, 1)', width=2)
                        ),
                        hovertemplate="<b>%{location}</b><br>Customers: %{text}<extra></extra>"
                    ))
                    fig4.update_layout(
                        title_text="Customer Distribution by U.S. State",
                        geo=dict(scope="usa", showland=True, landcolor='rgba(116, 185, 255, 0.1)',
                                 showlakes=True, lakecolor='white'),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white')
                    )
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.warning("No valid U.S. state data available for visualization after filtering.")
            else:
                st.warning("No customer data for 'United States' found after applying filters.")
        else:
            st.info("No geographic data available in usage data after applying filters.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. Tab Content: Funnel Analysis ---
with tabs[3]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("📉 Conversion Funnel Analysis")

    # Filter/Control
    compare_by = st.radio("Compare Funnel By:", ["Hub", "Tier", "Country"], horizontal=True)
    stage_order = ["Visitor", "Signup", "Trial", "Paid"]

    if compare_by == "Hub":
        if not df_funnel.empty and "hub" in df_funnel.columns:
            selected_hub_funnel = st.selectbox("Select Hub to Analyze", sorted(df_funnel["hub"].unique()), key="funnel_hub_select_new")
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

                # KPIs
                col1, col2, col3 = st.columns(3)
                with col1:
                    create_ios_metric_card("VISITOR → SIGNUP", f"{signup_rate:.1f}%", 
                                           color_gradient="135deg, #74b9ff 0%, #0984e3 100%")
                with col2:
                    create_ios_metric_card("SIGNUP → TRIAL", f"{trial_rate:.1f}%", 
                                           color_gradient="135deg, #fd79a8 0%, #e84393 100%")
                with col3:
                    create_ios_metric_card("TRIAL → PAID", f"{paid_rate:.1f}%", 
                                           color_gradient="135deg, #00b894 0%, #00a085 100%")

                # Visual
                fig5 = px.funnel(funnel_sorted, x="count", y="stage",
                                 title=f"Customer Acquisition Funnel – {selected_hub_funnel}")
                fig5.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"),
                    yaxis={'categoryorder': 'array', 'categoryarray': stage_order},
                    xaxis=dict(gridcolor='#f0f0f0'), # Light grid lines
                    yaxis=dict(gridcolor='#f0f0f0') # Light grid lines
                )
                fig5.update_traces(textposition='inside', marker_line_color='rgba(0,0,0,0.1)', marker_line_width=1)
                st.plotly_chart(fig5, use_container_width=True)

                # Insight
                overall_conversion = (paid_count / visitor_count * 100) if visitor_count > 0 else 0
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                    <h4>📊 Overall Conversion Rate</h4>
                    <p><strong>{overall_conversion:.2f}%</strong> of visitors become paid customers</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"No funnel data available for '{selected_hub_funnel}' in the 'funnel_data.csv' file.")
        else:
            st.info("Funnel data by Hub is not available.")

    elif compare_by == "Tier":
        filtered_funnel_usage = apply_global_filters(df_usage)
        if not filtered_funnel_usage.empty and "tier" in filtered_funnel_usage.columns and "stage" in filtered_funnel_usage.columns:
            selected_tier_funnel = st.selectbox("Select Tier to Analyze", sorted(filtered_funnel_usage["tier"].unique()), key="funnel_tier_select_new")

            tier_data = filtered_funnel_usage[filtered_funnel_usage["tier"] == selected_tier_funnel].copy()

            visitor_count = len(tier_data[tier_data["stage"] == "Visitor"])
            signup_count = len(tier_data[tier_data["stage"] == "Signup"])
            trial_count = len(tier_data[tier_data["stage"] == "Trial"])
            paid_count = len(tier_data[tier_data["stage"] == "Paid"])

            tier_funnel_data = [
                {"stage": "Visitor", "count": visitor_count},
                {"stage": "Signup", "count": signup_count},
                {"stage": "Trial", "count": trial_count},
                {"stage": "Paid", "count": paid_count}
            ]
            tier_funnel = pd.DataFrame(tier_funnel_data)

            signup_rate = (signup_count / visitor_count * 100) if visitor_count > 0 else 0
            trial_rate = (trial_count / signup_count * 100) if signup_count > 0 else 0
            paid_rate = (paid_count / trial_count * 100) if trial_count > 0 else 0

            # KPIs
            col1, col2, col3 = st.columns(3)
            with col1:
                create_ios_metric_card("VISITOR → SIGNUP", f"{signup_rate:.1f}%", 
                                       color_gradient="135deg, #74b9ff 0%, #0984e3 100%")
            with col2:
                create_ios_metric_card("SIGNUP → TRIAL", f"{trial_rate:.1f}%", 
                                       color_gradient="135deg, #fd79a8 0%, #e84393 100%")
            with col3:
                create_ios_metric_card("TRIAL → PAID", f"{paid_rate:.1f}%", 
                                       color_gradient="135deg, #00b894 0%, #00a085 100%")

            # Visual
            fig5 = px.funnel(tier_funnel, x="count", y="stage",
                             title=f"Conversion Funnel – {selected_tier_funnel} Tier")
            fig5.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"),
                yaxis={'categoryorder': 'array', 'categoryarray': stage_order},
                xaxis=dict(gridcolor='#f0f0f0'), # Light grid lines
                yaxis=dict(gridcolor='#f0f0f0') # Light grid lines
            )
            fig5.update_traces(textposition='inside', marker_line_color='rgba(0,0,0,0.1)', marker_line_width=1)
            st.plotly_chart(fig5, use_container_width=True)

            # Insight
            total_customers = len(tier_data)
            avg_mrr_paid_tier = tier_data[tier_data["stage"] == "Paid"]["monthly_recurring_revenue"].mean()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                <h4>📊 {selected_tier_funnel} Tier Insights</h4>
                <p><strong>{total_customers}</strong> total customers in filter</p>
                <p><strong>${avg_mrr_paid_tier:.2f}</strong> average MRR for paid customers</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Usage data is required for Tier funnel analysis.")

    else:  # Country analysis
        filtered_funnel_usage = apply_global_filters(df_usage)
        if not filtered_funnel_usage.empty and "country" in filtered_funnel_usage.columns and "stage" in filtered_funnel_usage.columns:
            available_countries = sorted(filtered_funnel_usage["country"].unique())
            selected_country_funnel = st.selectbox("Select Country to Analyze", available_countries, key="funnel_country_select_new")

            country_data = filtered_funnel_usage[filtered_funnel_usage["country"] == selected_country_funnel].copy()

            visitor_count = len(country_data[country_data["stage"] == "Visitor"])
            signup_count = len(country_data[country_data["stage"] == "Signup"])
            trial_count = len(country_data[country_data["stage"] == "Trial"])
            paid_count = len(country_data[country_data["stage"] == "Paid"])

            country_funnel_data = [
                {"stage": "Visitor", "count": visitor_count},
                {"stage": "Signup", "count": signup_count},
                {"stage": "Trial", "count": trial_count},
                {"stage": "Paid", "count": paid_count}
            ]
            country_funnel = pd.DataFrame(country_funnel_data)

            signup_rate = (signup_count / visitor_count * 100) if visitor_count > 0 else 0
            trial_rate = (trial_count / signup_count * 100) if signup_count > 0 else 0
            paid_rate = (paid_count / trial_count * 100) if trial_count > 0 else 0

            # KPIs
            col1, col2, col3 = st.columns(3)
            with col1:
                create_ios_metric_card("VISITOR → SIGNUP", f"{signup_rate:.1f}%", 
                                       color_gradient="135deg, #74b9ff 0%, #0984e3 100%")
            with col2:
                create_ios_metric_card("SIGNUP → TRIAL", f"{trial_rate:.1f}%", 
                                       color_gradient="135deg, #fd79a8 0%, #e84393 100%")
            with col3:
                create_ios_metric_card("TRIAL → PAID", f"{paid_rate:.1f}%", 
                                       color_gradient="135deg, #00b894 0%, #00a085 100%")

            # Visual
            fig5 = px.funnel(country_funnel, x="count", y="stage",
                             title=f"Conversion Funnel – {selected_country_funnel}")
            fig5.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"),
                yaxis={'categoryorder': 'array', 'categoryarray': stage_order},
                xaxis=dict(gridcolor='#f0f0f0'), # Light grid lines
                yaxis=dict(gridcolor='#f0f0f0') # Light grid lines
            )
            fig5.update_traces(textposition='inside', marker_line_color='rgba(0,0,0,0.1)', marker_line_width=1)
            st.plotly_chart(fig5, use_container_width=True)

            # Insight
            total_customers = len(country_data)
            paid_customers = len(country_data[country_data["stage"] == "Paid"])

            if selected_country_funnel == "United States":
                insight_text = f"🇺🇸 **US Market**: {total_customers} total customers, {paid_customers} paying customers. Strong trial adoption - consider premium tier promotions"
            elif selected_country_funnel in ["United Kingdom", "Germany"]:
                insight_text = f"🇪🇺 **{selected_country_funnel}**: {total_customers} total customers, {paid_customers} paying customers. European market - consider GDPR-compliant onboarding optimizations"
            elif selected_country_funnel in ["India", "Australia", "Canada"]:
                insight_text = f"🌏 **{selected_country_funnel}**: {total_customers} total customers, {paid_customers} paying customers. International market - evaluate pricing sensitivity and local payment methods"
            else:
                insight_text = f"📊 **{selected_country_funnel}**: {total_customers} total customers, {paid_customers} paying customers"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #55a3ff 0%, #003d82 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                <h4>🌍 Geographic Insights</h4>
                <p>{insight_text}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Usage data is required for Country funnel analysis.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 10. Tab Content: Competitive Price Benchmark ---
with tabs[4]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("🏁 Competitive Price Benchmark")
    
    if not df_competition.empty and selected_hub and selected_tier:
        df_comp = df_competition[
            (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
        ].copy()

        if selected_vendor != "All Vendors" and "vendor" in df_comp.columns:
            df_comp = df_comp[df_comp["vendor"] == selected_vendor]

        if not df_comp.empty:
            df_comp['price_usd'] = pd.to_numeric(df_comp['price_usd'], errors='coerce')
            df_comp.dropna(subset=['price_usd'], inplace=True)

            if not df_comp.empty:
                # KPIs (Price Metrics)
                avg_competitor_price = df_comp['price_usd'].mean()
                max_price = df_comp['price_usd'].max()
                min_price = df_comp['price_usd'].min()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    create_ios_metric_card("AVG PRICE", f"${avg_competitor_price:.2f}", 
                                           color_gradient="135deg, #e17055 0%, #d63031 100%")
                with col2:
                    create_ios_metric_card("HIGHEST", f"${max_price:.2f}", 
                                           color_gradient="135deg, #fd79a8 0%, #e84393 100%")
                with col3:
                    create_ios_metric_card("LOWEST", f"${min_price:.2f}", 
                                           color_gradient="135deg, #00b894 0%, #00a085 100%")

                # Visual
                fig6 = px.bar(df_comp, x="vendor", y="price_usd", color="vendor",
                              title=f"Vendor Pricing for {selected_hub} - {selected_tier}" + 
                                     (f" ({selected_vendor} Only)" if selected_vendor != "All Vendors" else ""))
                fig6.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"),
                    showlegend=False,
                    xaxis=dict(gridcolor='#f0f0f0'), # Light grid lines
                    yaxis=dict(gridcolor='#f0f0f0') # Light grid lines
                )
                st.plotly_chart(fig6, use_container_width=True)

                # Insight
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                    <h4>💡 Competitive Pricing Insights</h4>
                    <p>Compare your product's price against competitors for <strong>{selected_hub} - {selected_tier}</strong></p>
                    <p>Price range: <strong>${min_price:.2f} - ${max_price:.2f}</strong></p>
                    <p>Are you priced competitively? Higher pricing might require strong value proposition.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"No valid competitive pricing data for {selected_hub} / {selected_tier} with selected vendor after cleaning.")
        else:
            st.info(f"No competitive pricing data available for {selected_hub} / {selected_tier} with selected vendor.")
    else:
        st.info("Competitive pricing data not available or Hub/Tier not selected.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 11. Tab Content: Pricing Strategy & Financial Projections ---
with tabs[5]:
    st.markdown('<div class="projection-card">', unsafe_allow_html=True)
    st.subheader("📈 Pricing Strategy & Financial Projections")
    
    if selected_hub and selected_tier:
        # Attempt to get baseline data from pricing_strategy. If not found for selected H/T, it will be generated below.
        scenario_data_exists = False
        current_scenario_data = pd.DataFrame() # Initialize to empty
        
        if not df_pricing_strategy.empty:
            current_scenario_data = df_pricing_strategy[
                (df_pricing_strategy["hub"] == selected_hub) &
                (df_pricing_strategy["tier"] == selected_tier)
            ]
            if not current_scenario_data.empty:
                scenario_data_exists = True
                # Get baseline from "Conservative" if exists, otherwise first entry for this hub/tier
                baseline_data = current_scenario_data[current_scenario_data["scenario"] == "Conservative"].iloc[0] if "Conservative" in current_scenario_data["scenario"].unique() else current_scenario_data.iloc[0]
                
                current_price = baseline_data['current_price']
                current_customers = baseline_data['current_customers']
                current_churn = baseline_data['churn_rate']
                current_cac = baseline_data['cac']
                base_elasticity = baseline_data['price_elasticity']
            
        if not scenario_data_exists:
            st.info(f"Generating sample data for {selected_hub} / {selected_tier} as existing data was not found or was invalid.")
            # Generate a new sample data point for this specific hub/tier if not found
            np.random.seed(hash(selected_hub + selected_tier) % 2**32) # Consistent seed
            
            # Use general randomized base values
            current_price = np.random.uniform(29, 499)
            current_customers = np.random.randint(50, 2000)
            current_churn = np.random.uniform(0.02, 0.12)
            current_cac = np.random.uniform(80, 350)
            base_elasticity = np.random.uniform(-2.8, -0.3)

            # Generate and append data for all scenarios for this new combination
            new_data_rows = []
            for scenario in ['Conservative', 'Optimistic', 'Aggressive']:
                price_multiplier = np.random.uniform(1.0, 1.15) if scenario == 'Conservative' else \
                                   np.random.uniform(1.15, 1.35) if scenario == 'Optimistic' else \
                                   np.random.uniform(1.35, 1.65)
                adoption_impact = np.random.uniform(0.95, 1.05) if scenario == 'Conservative' else \
                                  np.random.uniform(0.85, 1.1) if scenario == 'Optimistic' else \
                                  np.random.uniform(0.75, 1.0)
                
                projected_price_at_change = current_price * price_multiplier
                projected_customers_at_change = int(current_customers * adoption_impact)

                for month in range(1, 13):
                    growth_rate_monthly = (np.random.uniform(0.01, 0.05) if scenario == 'Optimistic' else 
                                           np.random.uniform(0.005, 0.03) if scenario == 'Conservative' else 
                                           np.random.uniform(0.03, 0.08))
                    
                    if month == 1:
                        monthly_customers = projected_customers_at_change
                    else:
                        monthly_customers_calc_base = projected_customers_at_change * (1 + growth_rate_monthly) ** (month -1) 
                        monthly_customers = int(monthly_customers_calc_base * (1 - current_churn * month/12)) 
                        monthly_customers = max(1, monthly_customers) 

                    monthly_mrr = projected_price_at_change * monthly_customers
                    monthly_arr = monthly_mrr * 12
                    
                    avg_lifespan_months = 1 / current_churn if current_churn > 0 else 1000
                    ltv = projected_price_at_change * avg_lifespan_months
                    
                    cac_scenario = current_cac * (1.3 if scenario == 'Aggressive' else 1.0) 
                    ltv_cac_ratio = ltv / cac_scenario if cac_scenario > 0 else ltv

                    new_customer_revenue = np.random.uniform(0.1, 0.3) * monthly_mrr
                    expansion_revenue = np.random.uniform(0.05, 0.15) * monthly_mrr
                    
                    new_data_rows.append({
                        'hub': selected_hub, 'tier': selected_tier, 'scenario': scenario, 'month': month,
                        'date': (datetime.now() + timedelta(days=30*month)).strftime('%Y-%m-%d'),
                        'current_price': current_price, 'projected_price': projected_price_at_change,
                        'current_customers': current_customers, 'projected_customers': monthly_customers,
                        'current_mrr': current_mrr, 'projected_mrr': monthly_mrr, 'projected_arr': monthly_arr,
                        'churn_rate': current_churn, 'ltv': ltv, 'cac': cac_scenario, 'ltv_cac_ratio': ltv_cac_ratio,
                        'new_customer_revenue': new_customer_revenue, 'expansion_revenue': expansion_revenue,
                        'price_elasticity': base_elasticity,
                        'market_penetration': np.random.uniform(0.03, 0.35),
                        'competitive_position': np.random.choice(['Leading', 'Competitive', 'Behind'])
                    })
            
            new_df_to_append = pd.DataFrame(new_data_rows)
            global df_pricing_strategy 
            df_pricing_strategy = pd.concat([df_pricing_strategy, new_df_to_append], ignore_index=True)
            df_pricing_strategy.to_csv(Path("data/pricing_strategy.csv"), index=False)
            st.success(f"Generated and saved new data for {selected_hub} / {selected_tier}.")
            
            current_scenario_data = new_df_to_append 
            baseline_data = current_scenario_data[current_scenario_data["scenario"] == "Conservative"].iloc[0] if "Conservative" in current_scenario_data["scenario"].unique() else current_scenario_data.iloc[0]
            current_price = baseline_data['current_price']
            current_customers = baseline_data['current_customers']
            current_churn = baseline_data['churn_rate']
            current_cac = baseline_data['cac']
            base_elasticity = baseline_data['price_elasticity']


        # Filters/Controls for Interactive Simulator
        st.markdown("### 🎛️ Interactive Pricing Simulator")
        
        st.markdown('<div class="ios-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Price Adjustments")
            
            price_change = st.slider(
                "Price Change (%)",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                help="Adjust pricing relative to current price"
            )
            
            new_price = current_price * (1 + price_change / 100)
            st.metric("New Price", f"${new_price:.2f}", f"{price_change:+.0f}%")
            
            customer_growth = st.slider(
                "Annual Customer Growth (%)",
                min_value=-30,
                max_value=200,
                value=20,
                step=5,
                help="Expected annual customer growth rate"
            )
            
        with col2:
            st.markdown("#### 📊 Market Conditions")
            
            churn_adjustment = st.slider(
                "Churn Rate Adjustment (%)",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                help="Adjust monthly churn rate"
            )
            
            new_churn = current_churn * (1 + churn_adjustment / 100)
            st.metric("Monthly Churn Rate", f"{new_churn*100:.2f}%", f"{churn_adjustment:+.0f}%")
            
            cac_adjustment = st.slider(
                "CAC Adjustment (%)",
                min_value=-50,
                max_value=100,
                value=0,
                step=5,
                help="Adjust Customer Acquisition Cost"
            )
            
            new_cac = current_cac * (1 + cac_adjustment / 100)
            st.metric("Customer Acquisition Cost", f"${new_cac:.2f}", f"{cac_adjustment:+.0f}%")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Calculate dynamic projections based on sliders
        def calculate_dynamic_projections(months=12):
            price_impact = 1 + (base_elasticity * price_change / 100)
            effective_growth = customer_growth / 100 * max(0.1, price_impact) 
            
            projections = []
            
            for month in range(1, months + 1):
                month_growth_factor = (1 + effective_growth) ** (month / 12)
                projected_customers_base = int(current_customers * month_growth_factor)
                
                retained_customers = int(projected_customers_base * (1 - new_churn) ** month)
                retained_customers = max(1, retained_customers) 

                monthly_mrr = new_price * retained_customers
                annual_revenue = monthly_mrr * 12
                
                avg_lifespan_months = 1 / max(0.001, new_churn) 
                cltv = new_price * avg_lifespan_months
                
                ltv_cac_ratio = cltv / max(1, new_cac)
                
                # Profit calculation (simplified)
                monthly_profit = monthly_mrr * (1 - 0.30) - (new_cac * (retained_customers - (projections[-1]['customers'] if month > 1 else current_customers))) if month > 1 else monthly_mrr * (1 - 0.30)
                monthly_profit = max(-monthly_mrr, monthly_profit) 
                
                projections.append({
                    'month': month,
                    'customers': retained_customers,
                    'mrr': monthly_mrr,
                    'arr': annual_revenue,
                    'cltv': cltv,
                    'cac': new_cac,
                    'ltv_cac_ratio': ltv_cac_ratio,
                    'churn_rate': new_churn,
                    'profit': monthly_profit,
                    'avg_mrr_per_customer': new_price
                })
                
            return projections
        
        # Generate 12-month projections
        projections = calculate_dynamic_projections(12)
        projection_df = pd.DataFrame(projections)
        
        # KPIs - Dynamic Financial Metrics
        st.markdown("### 📊 Dynamic Financial Projections (12-Month)")
        
        final_metrics = projections[-1] # 12th month
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_ios_metric_card("AVG MRR/CUSTOMER", f"${final_metrics['avg_mrr_per_customer']:.2f}",
                                   f"Price: ${new_price:.2f}",
                                   color_gradient="135deg, #74b9ff 0%, #0984e3 100%")
        
        with col2:
            create_ios_metric_card("TOTAL CUSTOMERS", f"{final_metrics['customers']:,}",
                                   f"Growth: {customer_growth:+.0f}%",
                                   color_gradient="135deg, #fd79a8 0%, #e84393 100%")
        
        with col3:
            create_ios_metric_card("ANNUAL REVENUE", f"${final_metrics['arr']:,.0f}",
                                   f"ARR Projection",
                                   color_gradient="135deg, #00b894 0%, #00a085 100%")
        
        with col4:
            create_ios_metric_card("MONTHLY PROFIT", f"${final_metrics['profit']:,.0f}",
                                   f"Net profit (est.)",
                                   color_gradient="135deg, #fdcb6e 0%, #e17055 100%")
        
        # Second row of metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            create_ios_metric_card("CLTV", f"${final_metrics['cltv']:,.0f}",
                                   f"Customer Lifetime Value",
                                   color_gradient="135deg, #a29bfe 0%, #6c5ce7 100%")
        
        with col6:
            create_ios_metric_card("CHURN RATE", f"{final_metrics['churn_rate']*100:.2f}%",
                                   f"Monthly churn",
                                   color_gradient="135deg, #e17055 0%, #d63031 100%")
        
        with col7:
            create_ios_metric_card("CAC", f"${final_metrics['cac']:.0f}",
                                   f"Customer Acquisition Cost",
                                   color_gradient="135deg, #fab1a0 0%, #e17055 100%")
        
        with col8:
            create_ios_metric_card("LTV:CAC RATIO", f"{final_metrics['ltv_cac_ratio']:.1f}:1",
                                   f"{'Excellent' if final_metrics['ltv_cac_ratio'] > 3 else 'Good' if final_metrics['ltv_cac_ratio'] > 2 else 'Poor'}",
                                   color_gradient="135deg, #55a3ff 0%, #003d82 100%")
        
        # Visuals - Interactive Charts
        st.markdown("### 📈 Financial Projections Over Time")
        
        # Create tabs for different chart views
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Revenue & Customers", "Profitability", "Key Ratios"])
        
        with chart_tab1:
            fig_revenue_customers = go.Figure()
            
            # Add MRR line
            fig_revenue_customers.add_trace(go.Scatter(
                x=projection_df['month'],
                y=projection_df['mrr'],
                mode='lines+markers',
                name='Monthly Recurring Revenue',
                line=dict(color='rgba(255, 255, 255, 0.9)', width=3),
                yaxis='y'
            ))
            
            # Add customers line (secondary y-axis)
            fig_revenue_customers.add_trace(go.Scatter(
                x=projection_df['month'],
                y=projection_df['customers'],
                mode='lines+markers',
                name='Total Customers',
                line=dict(color='rgba(253, 121, 168, 0.9)', width=3),
                yaxis='y2'
            ))
            
            fig_revenue_customers.update_layout(
                title="Revenue & Customer Growth Projection",
                xaxis_title="Month",
                yaxis_title="Monthly Recurring Revenue ($)",
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)'), # Light grid lines on dark background
                yaxis2=dict(title="Total Customers", overlaying='y', side='right', gridcolor='rgba(255,255,255,0.2)'), # Light grid lines on dark background
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white'),
                legend=dict(bgcolor='rgba(255,255,255,0.1)', font=dict(color='white'))
            )
            
            st.plotly_chart(fig_revenue_customers, use_container_width=True)
        
        with chart_tab2:
            fig_profit = px.line(projection_df, x="month", y="profit",
                                 title="Monthly Profit Projection")
            fig_profit.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white'),
                xaxis_title="Month",
                yaxis_title="Monthly Profit ($)",
                xaxis=dict(gridcolor='rgba(255,255,255,0.2)'), # Light grid lines on dark background
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)') # Light grid lines on dark background
            )
            fig_profit.update_traces(line_color='rgba(0, 184, 148, 0.9)', line_width=3)
            st.plotly_chart(fig_profit, use_container_width=True)
            
            # Profit summary (KPIs)
            total_annual_profit = sum(p['profit'] for p in projections)
            profit_margin = (final_metrics['profit'] / final_metrics['mrr'] * 100) if final_metrics['mrr'] > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                create_ios_metric_card("ANNUAL PROFIT", f"${total_annual_profit:,.0f}",
                                       f"Total profit projection",
                                       color_gradient="135deg, #00b894 0%, #00a085 100%")
            with col2:
                create_ios_metric_card("PROFIT MARGIN", f"{profit_margin:.1f}%",
                                       f"Monthly profit margin",
                                       color_gradient="135deg, #74b9ff 0%, #0984e3 100%")
        
        with chart_tab3:
            # LTV:CAC and Churn over time (Visuals)
            fig_ratios = go.Figure()
            
            fig_ratios.add_trace(go.Scatter(
                x=projection_df['month'],
                y=projection_df['ltv_cac_ratio'],
                mode='lines+markers',
                name='LTV:CAC Ratio',
                line=dict(color='rgba(255, 255, 255, 0.9)', width=3)
            ))
            
            fig_ratios.update_layout(
                title="LTV:CAC Ratio Over Time",
                xaxis_title="Month",
                yaxis_title="LTV:CAC Ratio",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.2)'), # Light grid lines on dark background
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)') # Light grid lines on dark background
            )
            
            st.plotly_chart(fig_ratios, use_container_width=True)
        
        # Impact Analysis (KPIs/Insights)
        st.markdown("### 🎯 Impact Analysis")
        
        # Calculate impact vs baseline (conservative scenario for the currently selected H/T)
        baseline_12m_from_generated_data = current_scenario_data[
            (current_scenario_data["scenario"] == "Conservative") &
            (current_scenario_data["month"] == 12)
        ].iloc[0]

        revenue_impact = ((final_metrics['arr'] - baseline_12m_from_generated_data['projected_arr']) / baseline_12m_from_generated_data['projected_arr']) * 100 if baseline_12m_from_generated_data['projected_arr'] > 0 else 0
        customer_impact = ((final_metrics['customers'] - baseline_12m_from_generated_data['projected_customers']) / baseline_12m_from_generated_data['projected_customers']) * 100 if baseline_12m_from_generated_data['projected_customers'] > 0 else 0
        
        impact_color = "135deg, #00b894 0%, #00a085 100%" if revenue_impact >= 0 else "135deg, #e17055 0%, #d63031 100%"
        
        st.markdown(f"""
        <div style="background: linear-gradient({impact_color}); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
            <h4>📊 Impact vs Baseline (Conservative Scenario)</h4>
            <div style="display: flex; justify-content: space-between; margin: 16px 0;">
                <div style="text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold;">{revenue_impact:+.1f}%</div>
                    <div>Revenue Impact</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold;">{customer_impact:+.1f}%</div>
                    <div>Customer Impact</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5em; font-weight: bold;">{final_metrics['ltv_cac_ratio']:.1f}:1</div>
                    <div>LTV:CAC Ratio</div>
                </div>
            </div>
            <p><strong>Strategy Assessment:</strong> {
                'Excellent strategy with strong unit economics' if final_metrics['ltv_cac_ratio'] > 3 and revenue_impact > 0
                else 'Good strategy but monitor closely' if final_metrics['ltv_cac_ratio'] > 2 
                else 'Consider revising - poor unit economics' if final_metrics['ltv_cac_ratio'] < 2
                else 'Moderate strategy'
            }</p>
        </div>
        """, unsafe_allow_html=True)

        # Real Data Baseline (if available) - moved to bottom as a supplementary insight
        if not df_churn_retention.empty and not df_pricing_plans.empty: # Only display if both real data sources exist
            real_churn_data_filtered = df_churn_retention[
                (df_churn_retention["hub"] == selected_hub) &
                (df_churn_retention["tier"] == selected_tier)
            ]
            real_pricing_data_filtered = df_pricing_plans[
                (df_pricing_plans["hub"] == selected_hub) &
                (df_pricing_plans["tier"] == selected_tier)
            ]

            if not real_churn_data_filtered.empty and not real_pricing_data_filtered.empty:
                current_ltv_real = float(real_churn_data_filtered.iloc[0]['avg_ltv'])
                avg_months_active_real = float(real_churn_data_filtered.iloc[0]['avg_months_active'])
                current_mrr_real = float(real_churn_data_filtered.iloc[0]['avg_mrr'])
                ltv_to_mrr_ratio_real = float(real_churn_data_filtered.iloc[0]['ltv_to_mrr_ratio'])
                
                st.markdown("### 📋 Current Performance (Real Data Baseline)")
                st.info("✅ Using real data from your datasets for this baseline view.")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    create_ios_metric_card("CURRENT LTV", f"${current_ltv_real:,.0f}",
                                           f"From real data",
                                           color_gradient="135deg, #00cec9 0%, #00b894 100%")
                
                with col2:
                    create_ios_metric_card("AVG MONTHS ACTIVE", f"{avg_months_active_real:.1f}",
                                           f"Customer lifespan",
                                           color_gradient="135deg, #fd79a8 0%, #e84393 100%")
                
                with col3:
                    create_ios_metric_card("CURRENT MRR", f"${current_mrr_real:,.0f}",
                                           f"Real baseline",
                                           color_gradient="135deg, #fdcb6e 0%, #e17055 100%")
                
                with col4:
                    create_ios_metric_card("LTV/MRR RATIO", f"{ltv_to_mrr_ratio_real:.1f}",
                                           f"Efficiency metric",
                                           color_gradient="135deg, #a29bfe 0%, #6c5ce7 100%")

                # Display available real data combinations for reference
                st.markdown("### All Available Real Churn/Pricing Data:")
                churn_summary = df_churn_retention.copy()
                churn_summary['ltv_formatted'] = churn_summary['avg_ltv'].apply(lambda x: f"${x:,.0f}")
                churn_summary['mrr_formatted'] = churn_summary['avg_mrr'].apply(lambda x: f"${x:,.0f}")
                churn_summary['churn_formatted'] = churn_summary['churn_rate'].apply(lambda x: f"{x*100:.1f}%")
                
                display_cols = ['hub', 'tier', 'customer_count', 'churn_formatted', 'ltv_formatted', 'mrr_formatted', 'ltv_to_mrr_ratio']
                display_summary = churn_summary[display_cols].copy()
                display_summary.columns = ['Hub', 'Tier', 'Customers', 'Churn Rate', 'Avg LTV', 'Avg MRR', 'LTV/MRR Ratio']
                st.dataframe(display_summary, use_container_width=True)

            else:
                st.info("No real churn/pricing data found for the selected Hub/Tier combination. Displaying only generated projections.")
        else:
            st.info("Real churn_retention.csv or pricing_plans.csv not found. Displaying only generated projections.")

    else: # If selected_hub or selected_tier is None
        st.info("Please select both a Hub and Tier from the sidebar to view pricing strategy projections.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 12. Tab Content: Executive Summary (NEW) ---
with tabs[6]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("👑 Executive Summary")
    
    if not df_executive_summary.empty:
        # Assuming df_executive_summary has data for a specific period/overall
        exec_data = df_executive_summary.iloc[0] # Get latest executive summary
        
        # KPIs
        st.markdown("### 📊 Key Performance Indicators")
        
        # Top-level KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_ios_metric_card("CURRENT MRR", f"${exec_data.get('current_mrr', 0):,.0f}",
                                   f"Month: {exec_data.get('summary_month', 'N/A')}",
                                   color_gradient="135deg, #00b894 0%, #00a085 100%")
        
        with col2:
            create_ios_metric_card("ACTIVE CUSTOMERS", f"{exec_data.get('total_customers', 0):,.0f}",
                                   f"Growth: {exec_data.get('customer_growth_rate', 0):+.1f}%",
                                   color_gradient="135deg, #74b9ff 0%, #0984e3 100%")
        
        with col3:
            create_ios_metric_card("MRR GROWTH", f"{exec_data.get('mrr_growth_rate', 0):+.1f}%",
                                   f"Month-over-month",
                                   color_gradient="135deg, #fd79a8 0%, #e84393 100%")
        
        with col4:
            create_ios_metric_card("CHURN RATE", f"{exec_data.get('avg_churn_rate', 0)*100:.2f}%",
                                   f"Monthly average",
                                   color_gradient="135deg, #e17055 0%, #d63031 100%")
        
        # Visuals/Detailed KPIs - Customer Segments Analysis
        if not df_customer_dim.empty:
            st.markdown("### 🎯 Customer Segmentation")
            
            segment_summary = df_customer_dim.groupby('customer_segment').agg({
                'customer_id': 'count',
                'current_mrr': 'sum',
                'estimated_ltv': 'mean'
            }).reset_index()
            
            # Display top segments
            col1, col2 = st.columns(2)
            
            with col1:
                champions = segment_summary[segment_summary['customer_segment'] == 'CHAMPION']
                if not champions.empty:
                    champ_data = champions.iloc[0]
                    create_ios_metric_card("CHAMPION CUSTOMERS", f"{champ_data['customer_id']:,}",
                                           f"MRR: ${champ_data['current_mrr']:,.0f}",
                                           color_gradient="135deg, #fdcb6e 0%, #e17055 100%")
                else:
                    create_ios_metric_card("CHAMPION CUSTOMERS", "0", "No champions yet",
                                           color_gradient="135deg, #ddd 0%, #bbb 100%")
            
            with col2:
                # Assuming 'churn_risk' column exists in df_customer_dim
                if 'churn_risk' in df_customer_dim.columns:
                    at_risk = df_customer_dim[df_customer_dim['churn_risk'] == 'HIGH']['customer_id'].count()
                    create_ios_metric_card("HIGH RISK CUSTOMERS", f"{at_risk:,}",
                                           f"Require immediate attention",
                                           color_gradient="135deg, #e17055 0%, #d63031 100%")
                else:
                    create_ios_metric_card("HIGH RISK CUSTOMERS", "N/A", "Churn risk data missing",
                                           color_gradient="135deg, #ddd 0%, #bbb 100%")
        
        # Visuals/Detailed KPIs - Pricing Opportunities
        if not df_pricing_optimization.empty:
            st.markdown("### 💰 Pricing Opportunities")
            
            immediate_opps = df_pricing_optimization[
                df_pricing_optimization['strategic_recommendation'] == 'IMPLEMENT_IMMEDIATELY'
            ]
            
            if not immediate_opps.empty:
                total_uplift = immediate_opps['optimal_revenue_uplift_pct'].sum()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    create_ios_metric_card("IMMEDIATE OPPORTUNITIES", f"{len(immediate_opps)}",
                                           f"Ready to implement",
                                           color_gradient="135deg, #00b894 0%, #00a085 100%")
                
                with col2:
                    create_ios_metric_card("POTENTIAL UPLIFT", f"{total_uplift:.1f}%",
                                           f"Revenue increase potential",
                                           color_gradient="135deg, #a29bfe 0%, #6c5ce7 100%")
                
                # Show top opportunities (Visual/Table)
                st.markdown("**Top Pricing Opportunities:**")
                display_opps = immediate_opps.nlargest(3, 'optimal_revenue_uplift_pct')[
                    ['hub', 'tier', 'current_avg_price', 'optimal_price', 'optimal_revenue_uplift_pct']
                ].copy()
                display_opps.columns = ['Hub', 'Tier', 'Current Price', 'Optimal Price', 'Uplift %']
                display_opps['Current Price'] = display_opps['Current Price'].apply(lambda x: f"${x:.2f}")
                display_opps['Optimal Price'] = display_opps['Optimal Price'].apply(lambda x: f"${x:.2f}")
                display_opps['Uplift %'] = display_opps['Uplift %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(display_opps, use_container_width=True)
        
        # Visuals/Detailed KPIs - Data Quality Dashboard
        if not df_data_quality.empty:
            st.markdown("### 🔍 Data Quality Status")
            
            avg_quality = df_data_quality['data_quality_score'].mean() if 'data_quality_score' in df_data_quality.columns else 0
            failed_checks = len(df_data_quality[df_data_quality['uniqueness_check'] == 'FAIL']) if 'uniqueness_check' in df_data_quality.columns else 0
            
            col1, col2 = st.columns(2)
            
            with col1:
                quality_color = ("135deg, #00b894 0%, #00a085 100%" if avg_quality >= 95 
                                 else "135deg, #fdcb6e 0%, #e17055 100%" if avg_quality >= 85
                                 else "135deg, #e17055 0%, #d63031 100%")
                create_ios_metric_card("DATA QUALITY SCORE", f"{avg_quality:.1f}%",
                                       f"Overall data health",
                                       color_gradient=quality_color)
            
            with col2:
                failed_color = ("135deg, #00b894 0%, #00a085 100%" if failed_checks == 0
                                else "135deg, #e17055 0%, #d63031 100%")
                create_ios_metric_card("FAILED CHECKS", f"{failed_checks}",
                                       f"Data quality issues",
                                       color_gradient=failed_color)
        
        # Insights - Strategic Recommendations (from executive summary context)
        st.markdown("### 🎯 Strategic Recommendations")
        
        recommendations_exec = []
        
        # MRR Growth recommendations
        mrr_growth = exec_data.get('mrr_growth_rate', 0)
        if mrr_growth < 5:
            recommendations_exec.append(("📈 Focus on Growth", "MRR growth is below 5%. Consider pricing optimization and customer acquisition strategies."))
        elif mrr_growth > 20:
            recommendations_exec.append(("🚀 Scale Operations", "Exceptional growth! Ensure operational capacity can support continued expansion."))
        
        # Churn recommendations
        churn_rate_exec = exec_data.get('avg_churn_rate', 0)
        if churn_rate_exec > 0.05: # Using raw float from data, convert to % for display logic
            recommendations_exec.append(("⚠️ Address Churn", f"Churn rate of {churn_rate_exec*100:.1f}% needs immediate attention. Focus on customer success and retention programs."))
        
        # Customer segment recommendations
        if not df_customer_dim.empty and 'churn_risk' in df_customer_dim.columns:
            total_customers_dim = len(df_customer_dim)
            if total_customers_dim > 0:
                at_risk_pct = (df_customer_dim[df_customer_dim['churn_risk'] == 'HIGH']['customer_id'].count() / total_customers_dim) * 100
                if at_risk_pct > 15:
                    recommendations_exec.append(("🆘 Customer Health", f"{at_risk_pct:.1f}% of customers are high-risk. Implement proactive retention measures."))
        
        # Display recommendations
        for i, (title, content) in enumerate(recommendations_exec):
            color_gradients_exec = [
                "135deg, #667eea 0%, #764ba2 100%",
                "135deg, #fd79a8 0%, #e84393 100%",
                "135deg, #fdcb6e 0%, #e17055 100%"
            ]
            
            st.markdown(f"""
            <div style="background: linear-gradient({color_gradients_exec[i % len(color_gradients_exec)]}); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                <h4>{title}</h4>
                <p>{content}</p>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info("Executive summary data not available. This would typically be generated from your dbt mart models or a dedicated CSV.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 13. Tab Content: Recommendations (General) ---
with tabs[7]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("🧠 Pricing Strategy Recommendations")
    
    filter_summary = f"**{selected_hub or 'All Hubs'} – {selected_tier or 'All Tiers'}**"
    if selected_country != "All Countries":
        filter_summary += f" in **{selected_country}**"
    if min_mrr is not None:
        filter_summary += f" (MRR: ${min_mrr:.2f}-${max_mrr:.2f})"
    if min_months is not None:
        filter_summary += f" (Months Active: {min_months}-{max_months})"
    
    st.markdown(f"Based on selected filters: {filter_summary}")
    
    # Dynamic recommendations based on available data
    recommendations = []
    
    # Elasticity-based recommendations
    if not df_elasticity.empty and selected_hub and selected_tier:
        elastic_data = df_elasticity[
            (df_elasticity["hub"] == selected_hub) & (df_elasticity["tier"] == selected_tier)
        ]
        if not elastic_data.empty and 'elasticity_coefficient' in elastic_data.columns:
            coeff = elastic_data['elasticity_coefficient'].iloc[0]
            if coeff < -1:
                recommendations.append(("🎯 Price Sensitivity Alert", 
                                       f"High elasticity detected (coefficient: {coeff:.2f}). Small price increases can significantly reduce adoption. Consider value-based pricing strategies."))
            else:
                recommendations.append(("📈 Pricing Opportunity", 
                                       f"Low price sensitivity (coefficient: {coeff:.2f}). Consider gradual price increases with enhanced value proposition."))
    
    # Competitive positioning
    if not df_competition.empty and selected_hub and selected_tier:
        comp_data = df_competition[
            (df_competition["product_hub"] == selected_hub) & (df_competition["tier"] == selected_tier)
        ]
        if not comp_data.empty:
            comp_data['price_usd'] = pd.to_numeric(comp_data['price_usd'], errors='coerce')
            avg_competitor_price = comp_data['price_usd'].mean()
            recommendations.append(("🏁 Competitive Analysis", 
                                   f"Average competitor price: ${avg_competitor_price:.2f}. Ensure your pricing aligns with market positioning and value delivery."))
    
    # Usage-based recommendations
    if not df_usage.empty:
        filtered_usage = apply_global_filters(df_usage)
        if not filtered_usage.empty:
            avg_tenure = filtered_usage['months_active'].mean()
            avg_mrr = filtered_usage['monthly_recurring_revenue'].mean()
            
            if avg_tenure < 6:
                recommendations.append(("⚠️ Retention Focus", 
                                       f"Average tenure is {avg_tenure:.1f} months. Focus on onboarding improvements and early value delivery before price optimization."))
            elif avg_tenure > 18:
                recommendations.append(("🎯 Upsell Opportunity", 
                                       f"High customer loyalty ({avg_tenure:.1f} months average). Consider premium tier introductions or feature-based upsells."))
    
    # Display recommendations in iOS cards
    for i, (title, content) in enumerate(recommendations):
        color_gradients = [
            "135deg, #667eea 0%, #764ba2 100%",
            "135deg, #74b9ff 0%, #0984e3 100%",
            "135deg, #00b894 0%, #00a085 100%",
            "135deg, #fd79a8 0%, #e84393 100%",
            "135deg, #fdcb6e 0%, #e17055 100%"
        ]
        
        st.markdown(f"""
        <div style="background: linear-gradient({color_gradients[i % len(color_gradients)]}); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
            <h4>{title}</h4>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # General strategic recommendations
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
        <h4>📋 Strategic Action Items</h4>
        <ul>
            <li><strong>Bundling & Upselling:</strong> For the <strong>{selected_tier or 'Starter'}</strong> tier, consider bundling with complementary features to increase perceived value and improve retention.</li>
            <li><strong>Market Expansion:</strong> In regions with high visitor but low conversion rates, investigate localized marketing and UX improvements.</li>
            <li><strong>Geographic Strategy:</strong> If Geo View shows strong presence in price-sensitive countries, evaluate regional pricing adjustments.</li>
            <li><strong>Data-Driven Optimization:</strong> Use the financial projections to model different pricing scenarios before implementation.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("*These recommendations are based on your current data. For precise actions, conduct A/B testing on specific customer segments.*")
    
    st.markdown('</div>', unsafe_allow_html=True)
