# applications/dashboard/churn_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Churn Revenue Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .small-font {
        font-size:14px !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_sample_data():
    """Generate comprehensive sample data for demonstration"""
    np.random.seed(42)
    n_customers = 2000

    # Generate customer data with realistic patterns
    df = pd.DataFrame({
        'customer_id': [f'CUST_{i:06d}' for i in range(n_customers)],
        'email': [f'user{i}@company{i%100}.com' for i in range(n_customers)],
        'company_name': [f'Company {i%100}' for i in range(n_customers)],
        'first_name': [f'FirstName{i}' for i in range(n_customers)],
        'last_name': [f'LastName{i}' for i in range(n_customers)],
        'phone': [f'+1-555-{1000+i:04d}' for i in range(n_customers)],
        'country': np.random.choice(['USA', 'Canada', 'UK', 'Germany', 'France'], n_customers, p=[0.4, 0.2, 0.15, 0.15, 0.1]),
        'company_size': np.random.choice(['startup', 'small', 'medium', 'large', 'enterprise'],
                                         n_customers, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
        'industry': np.random.choice(['Technology', 'Healthcare', 'Finance', 'Education', 'Retail'],
                                       n_customers, p=[0.3, 0.2, 0.2, 0.15, 0.15]),
        'subscription_tier': np.random.choice(['basic', 'premium', 'enterprise'],
                                               n_customers, p=[0.5, 0.35, 0.15]),
        'monthly_revenue': np.random.choice([29, 99, 299], n_customers, p=[0.5, 0.35, 0.15]),
        'customer_tenure_months': np.random.exponential(scale=12, size=n_customers).round(1),
        'total_revenue': np.random.exponential(scale=2000, size=n_customers).round(0),
        'avg_daily_usage': np.random.exponential(scale=5, size=n_customers).round(1),
        'features_adopted': np.random.poisson(lam=3, size=n_customers),
        'last_activity_days_ago': np.random.exponential(scale=7, size=n_customers).round(0).astype(int),
        'support_tickets': np.random.poisson(lam=2, size=n_customers),
        'avg_satisfaction_score': np.random.choice([1, 2, 3, 4, 5], n_customers, p=[0.05, 0.1, 0.2, 0.4, 0.25]),
        'signup_date': pd.date_range(start='2022-01-01', periods=n_customers, freq='D')[:n_customers],
        'subscription_start_date': pd.date_range(start='2022-01-01', periods=n_customers, freq='D')[:n_customers],
        'payment_method': np.random.choice(['credit_card', 'bank_transfer', 'paypal'], n_customers, p=[0.7, 0.2, 0.1]),
        'is_active': np.random.choice([True, False], n_customers, p=[0.85, 0.15])
    })

    # Calculate churn risk with realistic patterns
    df = calculate_churn_risk(df)

    return df

def calculate_churn_risk(df):
    """Calculate churn risk based on available metrics"""
    try:
        # Normalize factors for risk calculation
        df['risk_inactivity'] = np.where(df['last_activity_days_ago'] > 30, 0.3, 0)
        df['risk_low_usage'] = np.where(df['avg_daily_usage'] < 1, 0.25, 0)
        df['risk_support'] = np.where(df['support_tickets'] > 5, 0.2, 0)
        df['risk_satisfaction'] = np.where(df['avg_satisfaction_score'] < 3, 0.15, 0)
        df['risk_new_customer'] = np.where(df['customer_tenure_months'] < 3, 0.1, 0)

        # Enterprise customers get risk reduction
        df['risk_reduction'] = np.where(df['subscription_tier'] == 'enterprise', -0.15, 0)

        # Calculate overall churn risk score
        df['churn_risk_score'] = (
            0.1 + # Base risk
            df['risk_inactivity'] +
            df['risk_low_usage'] +
            df['risk_support'] +
            df['risk_satisfaction'] +
            df['risk_new_customer'] +
            df['risk_reduction']
        ).clip(0, 1)

        # Create risk levels
        df['churn_risk_level'] = pd.cut(
            df['churn_risk_score'],
            bins=[0, 0.2, 0.5, 1.0],
            labels=['low', 'medium', 'high'],
            right=False # Ensure 0.2 is 'low', not 'medium'
        )

        # Simulate actual churn based on risk scores
        df['is_churned'] = np.random.binomial(1, df['churn_risk_score'], size=len(df))

        return df
    except Exception as e:
        st.error(f"Error calculating churn risk: {e}")
        return df

def calculate_metrics(df):
    """Calculate key business metrics"""
    try:
        total_customers = len(df)
        churned_customers = df['is_churned'].sum() if 'is_churned' in df.columns else 0
        churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0

        # Calculate MRR from active customers
        active_customers = df[df['is_churned'] == 0] if 'is_churned' in df.columns else df
        mrr = active_customers['monthly_revenue'].sum() if 'monthly_revenue' in active_customers.columns else 0

        # Average customer metrics
        avg_ltv = df['total_revenue'].mean() if 'total_revenue' in df.columns else 0
        avg_tenure = df['customer_tenure_months'].mean() if 'customer_tenure_months' in df.columns else 0

        # At-risk customers
        at_risk = len(df[df['churn_risk_level'] == 'high']) if 'churn_risk_level' in df.columns else 0

        # Revenue at risk
        revenue_at_risk = df[df['churn_risk_level'] == 'high']['monthly_revenue'].sum() if 'churn_risk_level' in df.columns and 'monthly_revenue' in df.columns else 0
        revenue_at_risk *= 12 # Annualize for consistency in terms of 'at risk'

        return {
            'total_customers': total_customers,
            'churned_customers': churned_customers,
            'churn_rate': churn_rate,
            'mrr': mrr,
            'avg_ltv': avg_ltv,
            'avg_tenure': avg_tenure,
            'at_risk_customers': at_risk,
            'revenue_at_risk': revenue_at_risk
        }
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return {} # Return an empty dictionary on error

def create_churn_by_segment_chart(df, segment_col, title_suffix=""):
    """Create churn rate chart by segment"""
    try:
        if segment_col not in df.columns or 'is_churned' not in df.columns:
            st.warning(f"Missing '{segment_col}' or 'is_churned' column for churn segment chart.")
            return None

        # Filter out rows where segment_col might be NaN if not handled upstream
        df_filtered = df.dropna(subset=[segment_col])

        if df_filtered.empty: # Check if DataFrame is empty after dropping NaNs
            st.info(f"No data for {segment_col} after filtering out missing values.")
            return None

        segment_stats = df_filtered.groupby(segment_col).agg({
            'customer_id': 'count',
            'is_churned': ['sum', 'mean'],
            'monthly_revenue': 'sum'
        }).reset_index()

        segment_stats.columns = [segment_col, 'total_customers', 'churned_customers', 'churn_rate', 'total_revenue']
        segment_stats['churn_rate'] = segment_stats['churn_rate'] * 100

        fig = px.bar(
            segment_stats,
            x=segment_col,
            y='churn_rate',
            title=f'Churn Rate by {segment_col.replace("_", " ").title()}{title_suffix}',
            labels={'churn_rate': 'Churn Rate (%)', segment_col: segment_col.replace("_", " ").title()},
            color='churn_rate',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating segment chart for {segment_col}: {e}")
        return None

def create_revenue_chart(df):
    """Create revenue analysis chart"""
    try:
        if 'subscription_tier' not in df.columns or 'monthly_revenue' not in df.columns:
            st.warning("Missing 'subscription_tier' or 'monthly_revenue' column for revenue chart.")
            return None

        revenue_by_tier = df.groupby('subscription_tier')['monthly_revenue'].sum().reset_index()

        fig = px.pie(
            revenue_by_tier,
            names='subscription_tier',
            values='monthly_revenue',
            title='Monthly Revenue Distribution by Tier',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating revenue chart: {e}")
        return None

def create_tenure_usage_scatter(df):
    """Create tenure vs usage scatter plot"""
    try:
        if not all(col in df.columns for col in ['customer_tenure_months', 'avg_daily_usage', 'churn_risk_level']):
            st.warning("Missing required columns for tenure vs usage scatter plot.")
            return None

        # Sample data for better performance with large datasets
        sample_df = df.sample(min(len(df), 1000)) # Ensure min is not zero if len(df) is too small

        fig = px.scatter(
            sample_df,
            x='customer_tenure_months',
            y='avg_daily_usage',
            color='churn_risk_level',
            title='Customer Tenure vs Daily Usage',
            labels={
                'customer_tenure_months': 'Tenure (Months)',
                'avg_daily_usage': 'Daily Usage',
                'churn_risk_level': 'Risk Level'
            },
            color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
        )
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating scatter plot: {e}")
        return None

def create_satisfaction_chart(df):
    """Create satisfaction score distribution"""
    try:
        if 'avg_satisfaction_score' not in df.columns:
            st.warning("Missing 'avg_satisfaction_score' column for satisfaction chart.")
            return None

        satisfaction_dist = df['avg_satisfaction_score'].value_counts().sort_index()

        fig = px.bar(
            x=satisfaction_dist.index,
            y=satisfaction_dist.values,
            title='Customer Satisfaction Score Distribution',
            labels={'x': 'Satisfaction Score', 'y': 'Number of Customers'},
            color=satisfaction_dist.values,
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating satisfaction chart: {e}")
        return None

def main():
    """Main dashboard function"""
    st.title("🎯 Customer Churn Analytics Dashboard")
    st.markdown("*Comprehensive analytics for subscription business churn and revenue optimization*")

    # Load data
    with st.spinner("Loading data..."):
        df = load_sample_data()

    if df is None or len(df) == 0:
        st.error("No data available or data loading failed.")
        return

    st.success(f"✅ Successfully loaded {len(df):,} customer records")

    # --- Sidebar Filters ---
    st.sidebar.header("⚙️ Apply Filters")

    # For single-select dropdowns, use st.selectbox
    # It's good practice to add an "All" option for selection box filters
    # when you want to show all data by default.

    # Filter by Country
    if 'country' in df.columns:
        all_countries = ['All'] + df['country'].unique().tolist()
        selected_country = st.sidebar.selectbox(
            "Select Country",
            options=all_countries,
            index=0 # 'All' is default
        )
        if selected_country != 'All':
            df = df[df['country'] == selected_country]

    # Filter by Company Size
    if 'company_size' in df.columns:
        company_size_order = ['All', 'startup', 'small', 'medium', 'large', 'enterprise']
        # Ensure only relevant options are in the list based on current data
        available_company_sizes = [s for s in company_size_order if s == 'All' or s in df['company_size'].unique()]
        selected_company_size = st.sidebar.selectbox(
            "Select Company Size",
            options=available_company_sizes,
            index=0
        )
        if selected_company_size != 'All':
            df = df[df['company_size'] == selected_company_size]

    # Filter by Industry
    if 'industry' in df.columns:
        all_industries = ['All'] + df['industry'].unique().tolist()
        selected_industry = st.sidebar.selectbox(
            "Select Industry",
            options=all_industries,
            index=0
        )
        if selected_industry != 'All':
            df = df[df['industry'] == selected_industry]

    # Filter by Subscription Tier
    if 'subscription_tier' in df.columns:
        subscription_tier_order = ['All', 'basic', 'premium', 'enterprise']
        available_subscription_tiers = [s for s in subscription_tier_order if s == 'All' or s in df['subscription_tier'].unique()]
        selected_subscription_tier = st.sidebar.selectbox(
            "Select Subscription Tier",
            options=available_subscription_tiers,
            index=0
        )
        if selected_subscription_tier != 'All':
            df = df[df['subscription_tier'] == selected_subscription_tier]

    # Filter by Churn Risk Level
    if 'churn_risk_level' in df.columns:
        risk_level_order = ['All', 'low', 'medium', 'high']
        available_risk_levels = [l for l in risk_level_order if l == 'All' or l in df['churn_risk_level'].unique()]
        selected_risk_level = st.sidebar.selectbox(
            "Filter by Churn Risk Level",
            options=available_risk_levels,
            index=0
        )
        if selected_risk_level != 'All':
            df = df[df['churn_risk_level'] == selected_risk_level]

    # Filter by Customer Tenure (Months) - Slider remains for range selection
    if 'customer_tenure_months' in df.columns and not df['customer_tenure_months'].empty:
        # Check if min/max tenure are valid numbers before using them
        if not df['customer_tenure_months'].isnull().all(): # Check if not all are NaN
            min_tenure_val = df['customer_tenure_months'].min()
            max_tenure_val = df['customer_tenure_months'].max()

            # Handle cases where min/max might be the same (e.g., all customers have 0 tenure)
            if min_tenure_val == max_tenure_val:
                st.sidebar.write(f"Customer Tenure (Months): {min_tenure_val:.1f}")
                tenure_range = (min_tenure_val, max_tenure_val) # Set range to single value
            else:
                tenure_range = st.sidebar.slider(
                    "Customer Tenure (Months)",
                    min_value=float(min_tenure_val),
                    max_value=float(max_tenure_val),
                    value=(float(min_tenure_val), float(max_tenure_val)),
                    step=0.1
                )
            df = df[(df['customer_tenure_months'] >= tenure_range[0]) & (df['customer_tenure_months'] <= tenure_range[1])]
        else:
            st.sidebar.info("Customer Tenure data is not available for filtering.")


    # Filter by Monthly Revenue - Slider remains for range selection
    if 'monthly_revenue' in df.columns and not df['monthly_revenue'].empty:
        if not df['monthly_revenue'].isnull().all():
            min_revenue_val = df['monthly_revenue'].min()
            max_revenue_val = df['monthly_revenue'].max()

            if min_revenue_val == max_revenue_val:
                st.sidebar.write(f"Monthly Revenue ($): ${min_revenue_val:,.0f}")
                revenue_range = (min_revenue_val, max_revenue_val)
            else:
                revenue_range = st.sidebar.slider(
                    "Monthly Revenue ($)",
                    min_value=float(min_revenue_val),
                    max_value=float(max_revenue_val),
                    value=(float(min_revenue_val), float(max_revenue_val)),
                    step=1.0
                )
            df = df[(df['monthly_revenue'] >= revenue_range[0]) & (df['monthly_revenue'] <= revenue_range[1])]
        else:
            st.sidebar.info("Monthly Revenue data is not available for filtering.")


    # Check if filtered DataFrame is empty
    if df.empty:
        st.warning("No customers match the selected filter criteria. Please adjust your filters.")
        return # Exit main if no data to display

    # Recalculate metrics after filtering
    metrics = calculate_metrics(df)

    if not metrics: # Check if metrics dictionary is empty due to an error (e.g., filtered df is empty, leading to division by zero)
        st.error("Could not calculate key metrics after filtering. Please adjust filters.")
        return

    # Display key metrics
    st.markdown("### 📊 Executive Dashboard")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Customers",
            f"{metrics.get('total_customers', 0):,}",
            help="Total number of customers in the dataset"
        )

    with col2:
        churn_rate = metrics.get('churn_rate', 0)
        # Use a consistent delta for demonstration, or remove if not truly dynamic
        delta_churn = np.random.uniform(-0.5, 0.5)
        st.metric(
            "Churn Rate",
            f"{churn_rate:.1f}%",
            delta=f"{delta_churn:.1f}%",
            delta_color="inverse" if churn_rate > 15 else "normal", # Dynamic delta color based on churn rate
            help="Percentage of customers who have churned"
        )

    with col3:
        delta_mrr = np.random.randint(1000, 5000)
        st.metric(
            "Monthly Recurring Revenue",
            f"${metrics.get('mrr', 0):,.0f}",
            delta=f"+${delta_mrr:,}",
            help="Total monthly recurring revenue from active customers"
        )

    with col4:
        delta_risk_customers = np.random.randint(-10, 5)
        st.metric(
            "High-Risk Customers",
            f"{metrics.get('at_risk_customers', 0):,}",
            delta=f"{delta_risk_customers:+d}",
            delta_color="inverse",
            help="Customers with high churn risk scores"
        )

    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Average LTV", f"${metrics.get('avg_ltv', 0):,.0f}")

    with col2:
        st.metric("Average Tenure", f"{metrics.get('avg_tenure', 0):.1f} months")

    with col3:
        st.metric("Revenue at Risk", f"${metrics.get('revenue_at_risk', 0):,.0f}")

    with col4:
        retention_rate = 100 - metrics.get('churn_rate', 0)
        st.metric("Retention Rate", f"{retention_rate:.1f}%")

    st.markdown("---")

    # Analytics tabs - UPDATED TABS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Churn Analysis",
        "💰 Revenue Analysis",
        "👥 Customer Segments",
        "📈 Value & Adoption", # New tab for LTV & Feature Adoption
        "⚠️ Risk Management",
        "💡 Recommendations", # New tab for Recommended Actions
        "📋 Data Explorer"
    ])

    with tab1:
        st.markdown("#### Churn Analysis by Customer Segments")

        col1, col2 = st.columns(2)

        with col1:
            chart = create_churn_by_segment_chart(df, 'subscription_tier')
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            chart = create_churn_by_segment_chart(df, 'company_size')
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        # Industry analysis
        col1, col2 = st.columns(2)

        with col1:
            chart = create_churn_by_segment_chart(df, 'industry')
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            chart = create_satisfaction_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

    with tab2:
        st.markdown("#### Revenue Analysis")

        col1, col2 = st.columns(2)

        with col1:
            chart = create_revenue_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            # Revenue at risk by segment
            if 'churn_risk_level' in df.columns and 'monthly_revenue' in df.columns:
                risk_revenue = df.groupby('churn_risk_level')['monthly_revenue'].sum().reset_index()
                fig = px.bar(
                    risk_revenue,
                    x='churn_risk_level',
                    y='monthly_revenue',
                    title='Monthly Revenue by Risk Level',
                    color='churn_risk_level',
                    color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Missing 'churn_risk_level' or 'monthly_revenue' column for Revenue by Risk Level chart.")

        # LTV analysis and Feature Adoption Analysis are now in a new tab

    with tab3: # Customer Segments
        st.markdown("#### Customer Segmentation Analysis")

        col1, col2 = st.columns(2)

        with col1:
            chart = create_tenure_usage_scatter(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            if 'churn_risk_level' in df.columns:
                risk_dist = df['churn_risk_level'].value_counts()
                fig = px.pie(
                    values=risk_dist.values,
                    names=risk_dist.index,
                    title='Customer Risk Distribution',
                    color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Missing 'churn_risk_level' column for Customer Risk Distribution chart.")

        # Feature adoption analysis is now in a new tab

    with tab4: # 📈 Value & Adoption (New Tab)
        st.markdown("#### Customer Lifetime Value Analysis")
        if 'total_revenue' in df.columns:
            col1, col2, col3 = st.columns(3)

            with col1:
                ltv_by_tier = df.groupby('subscription_tier')['total_revenue'].mean().reset_index()
                fig = px.bar(ltv_by_tier, x='subscription_tier', y='total_revenue',
                             title='Average LTV by Subscription Tier')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                ltv_by_size = df.groupby('company_size')['total_revenue'].mean().reset_index()
                fig = px.bar(ltv_by_size, x='company_size', y='total_revenue',
                             title='Average LTV by Company Size')
                st.plotly_chart(fig, use_container_width=True)

            with col3:
                fig = px.histogram(df, x='total_revenue', nbins=30,
                                   title='LTV Distribution')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Missing 'total_revenue' column for Customer Lifetime Value Analysis.")

        st.markdown("#### Feature Adoption Analysis")
        if 'features_adopted' in df.columns and 'subscription_tier' in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                avg_features_by_tier = df.groupby('subscription_tier')['features_adopted'].mean().reset_index()
                fig = px.bar(avg_features_by_tier, x='subscription_tier', y='features_adopted',
                             title='Average Features Adopted by Tier')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.histogram(df, x='features_adopted', nbins=15,
                                   title='Distribution of Features Adopted')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Missing 'features_adopted' or 'subscription_tier' column for Feature Adoption Analysis.")


    with tab5: # Risk Management (original tab, content remains)
        st.markdown("#### Risk Management Dashboard")

        # High-risk customers
        if 'churn_risk_level' in df.columns:
            high_risk = df[df['churn_risk_level'] == 'high'].copy()

            if len(high_risk) > 0:
                st.markdown(f"**🚨 {len(high_risk):,} High-Risk Customers Identified**")

                # Sort by risk score
                if 'churn_risk_score' in high_risk.columns:
                    high_risk = high_risk.sort_values('churn_risk_score', ascending=False)

                # Top 20 high-risk customers
                display_cols = [col for col in ['customer_id', 'company_name', 'subscription_tier',
                               'monthly_revenue', 'churn_risk_score', 'last_activity_days_ago',
                               'support_tickets', 'avg_satisfaction_score']
                               if col in high_risk.columns]

                st.dataframe(
                    high_risk[display_cols].head(20),
                    use_container_width=True,
                    hide_index=True
                )

                # Risk factor analysis
                st.markdown("#### Risk Factor Breakdown")

                col1, col2 = st.columns(2)

                with col1:
                    risk_factors = []
                    # Ensure risk calculation columns exist before checking them
                    if all(col in df.columns for col in ['last_activity_days_ago', 'avg_daily_usage', 'support_tickets']):
                        inactive_pct = (df['last_activity_days_ago'] > 30).mean() * 100
                        risk_factors.append({"Factor": "Inactive > 30 days", "Percentage": inactive_pct})

                        low_usage_pct = (df['avg_daily_usage'] < 1).mean() * 100
                        risk_factors.append({"Factor": "Low daily usage", "Percentage": low_usage_pct})

                        high_support_pct = (df['support_tickets'] > 5).mean() * 100
                        risk_factors.append({"Factor": "High support tickets", "Percentage": high_support_pct})

                    if risk_factors:
                        risk_df = pd.DataFrame(risk_factors)
                        fig = px.bar(risk_df, x='Factor', y='Percentage',
                                     title='Risk Factors in Customer Base')
                        fig.update_traces(marker_color='red', opacity=0.7)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No primary risk factors identified in the data for this chart.")

                with col2:
                    # Risk score distribution
                    fig = px.histogram(df, x='churn_risk_score', nbins=20,
                                       title='Churn Risk Score Distribution')
                    fig.add_vline(x=0.5, line_dash="dash", line_color="red",
                                  annotation_text="High Risk Threshold")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No high-risk customers identified based on current criteria.")
        else:
            st.warning("Missing 'churn_risk_level' column for Risk Management Dashboard.")


        # Action recommendations are now in a new tab

    with tab6: # 💡 Recommendations (New Tab)
        st.markdown("#### 💡 Recommended Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.error("""
            **🚨 Immediate Actions (High Risk)**
            - Personal outreach to top 50 at-risk customers
            - Offer usage training sessions
            - Provide dedicated customer success manager
            - Consider pricing incentives for renewals
            """)

        with col2:
            st.warning("""
            **⚠️ Medium-term Actions (Medium Risk)**
            - Automated email engagement campaigns
            - Feature adoption workshops
            - Regular health score check-ins
            - Product usage optimization tips
            """)

        with col3:
            st.info("""
            **ℹ️ Preventive Actions (Low Risk)**
            - Monthly product newsletters
            - Feature announcement updates
            - Customer satisfaction surveys
            - Referral program enrollment
            """)

    with tab7: # Data Explorer (original tab, content remains)
        st.markdown("#### Data Explorer")

        # Data overview
        st.markdown("**Dataset Overview:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Total Records:** {len(df):,}")
            st.write(f"**Total Columns:** {len(df.columns)}")

        with col2:
            # Check if signup_date column exists before accessing
            if 'signup_date' in df.columns and not df['signup_date'].empty:
                st.write(f"**Date Range:** {df['signup_date'].min().strftime('%Y-%m-%d')} to {df['signup_date'].max().strftime('%Y-%m-%d')}")
            else:
                st.write("**Date Range:** N/A (signup_date column missing or empty)")

            if 'country' in df.columns:
                st.write(f"**Countries:** {df['country'].nunique()}")
            else:
                st.write("**Countries:** N/A (country column missing)")

        with col3:
            if 'industry' in df.columns:
                st.write(f"**Industries:** {df['industry'].nunique()}")
            else:
                st.write("**Industries:** N/A (industry column missing)")

            if 'subscription_tier' in df.columns:
                st.write(f"**Subscription Tiers:** {df['subscription_tier'].nunique()}")
            else:
                st.write("**Subscription Tiers:** N/A (subscription_tier column missing)")

        # Sample data
        st.markdown("**Sample Data:**")
        st.dataframe(df.head(10), use_container_width=True)

        # Column information
        with st.expander("📋 Column Details"):
            st.write("**Available columns:**")
            for i, col in enumerate(df.columns, 1):
                st.write(f"{i}. **{col}** - {df[col].dtype}")

if __name__ == "__main__":
    main()# applications/dashboard/churn_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Churn Revenue Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .medium-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .small-font {
        font-size:14px !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_sample_data():
    """Generate comprehensive sample data for demonstration"""
    np.random.seed(42)
    n_customers = 2000

    # Generate customer data with realistic patterns
    df = pd.DataFrame({
        'customer_id': [f'CUST_{i:06d}' for i in range(n_customers)],
        'email': [f'user{i}@company{i%100}.com' for i in range(n_customers)],
        'company_name': [f'Company {i%100}' for i in range(n_customers)],
        'first_name': [f'FirstName{i}' for i in range(n_customers)],
        'last_name': [f'LastName{i}' for i in range(n_customers)],
        'phone': [f'+1-555-{1000+i:04d}' for i in range(n_customers)],
        'country': np.random.choice(['USA', 'Canada', 'UK', 'Germany', 'France'], n_customers, p=[0.4, 0.2, 0.15, 0.15, 0.1]),
        'company_size': np.random.choice(['startup', 'small', 'medium', 'large', 'enterprise'],
                                         n_customers, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
        'industry': np.random.choice(['Technology', 'Healthcare', 'Finance', 'Education', 'Retail'],
                                       n_customers, p=[0.3, 0.2, 0.2, 0.15, 0.15]),
        'subscription_tier': np.random.choice(['basic', 'premium', 'enterprise'],
                                               n_customers, p=[0.5, 0.35, 0.15]),
        'monthly_revenue': np.random.choice([29, 99, 299], n_customers, p=[0.5, 0.35, 0.15]),
        'customer_tenure_months': np.random.exponential(scale=12, size=n_customers).round(1),
        'total_revenue': np.random.exponential(scale=2000, size=n_customers).round(0),
        'avg_daily_usage': np.random.exponential(scale=5, size=n_customers).round(1),
        'features_adopted': np.random.poisson(lam=3, size=n_customers),
        'last_activity_days_ago': np.random.exponential(scale=7, size=n_customers).round(0).astype(int),
        'support_tickets': np.random.poisson(lam=2, size=n_customers),
        'avg_satisfaction_score': np.random.choice([1, 2, 3, 4, 5], n_customers, p=[0.05, 0.1, 0.2, 0.4, 0.25]),
        'signup_date': pd.date_range(start='2022-01-01', periods=n_customers, freq='D')[:n_customers],
        'subscription_start_date': pd.date_range(start='2022-01-01', periods=n_customers, freq='D')[:n_customers],
        'payment_method': np.random.choice(['credit_card', 'bank_transfer', 'paypal'], n_customers, p=[0.7, 0.2, 0.1]),
        'is_active': np.random.choice([True, False], n_customers, p=[0.85, 0.15])
    })

    # Calculate churn risk with realistic patterns
    df = calculate_churn_risk(df)

    return df

def calculate_churn_risk(df):
    """Calculate churn risk based on available metrics"""
    try:
        # Normalize factors for risk calculation
        df['risk_inactivity'] = np.where(df['last_activity_days_ago'] > 30, 0.3, 0)
        df['risk_low_usage'] = np.where(df['avg_daily_usage'] < 1, 0.25, 0)
        df['risk_support'] = np.where(df['support_tickets'] > 5, 0.2, 0)
        df['risk_satisfaction'] = np.where(df['avg_satisfaction_score'] < 3, 0.15, 0)
        df['risk_new_customer'] = np.where(df['customer_tenure_months'] < 3, 0.1, 0)

        # Enterprise customers get risk reduction
        df['risk_reduction'] = np.where(df['subscription_tier'] == 'enterprise', -0.15, 0)

        # Calculate overall churn risk score
        df['churn_risk_score'] = (
            0.1 + # Base risk
            df['risk_inactivity'] +
            df['risk_low_usage'] +
            df['risk_support'] +
            df['risk_satisfaction'] +
            df['risk_new_customer'] +
            df['risk_reduction']
        ).clip(0, 1)

        # Create risk levels
        df['churn_risk_level'] = pd.cut(
            df['churn_risk_score'],
            bins=[0, 0.2, 0.5, 1.0],
            labels=['low', 'medium', 'high'],
            right=False # Ensure 0.2 is 'low', not 'medium'
        )

        # Simulate actual churn based on risk scores
        df['is_churned'] = np.random.binomial(1, df['churn_risk_score'], size=len(df))

        return df
    except Exception as e:
        st.error(f"Error calculating churn risk: {e}")
        return df

def calculate_metrics(df):
    """Calculate key business metrics"""
    try:
        total_customers = len(df)
        churned_customers = df['is_churned'].sum() if 'is_churned' in df.columns else 0
        churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0

        # Calculate MRR from active customers
        active_customers = df[df['is_churned'] == 0] if 'is_churned' in df.columns else df
        mrr = active_customers['monthly_revenue'].sum() if 'monthly_revenue' in active_customers.columns else 0

        # Average customer metrics
        avg_ltv = df['total_revenue'].mean() if 'total_revenue' in df.columns else 0
        avg_tenure = df['customer_tenure_months'].mean() if 'customer_tenure_months' in df.columns else 0

        # At-risk customers
        at_risk = len(df[df['churn_risk_level'] == 'high']) if 'churn_risk_level' in df.columns else 0

        # Revenue at risk
        revenue_at_risk = df[df['churn_risk_level'] == 'high']['monthly_revenue'].sum() if 'churn_risk_level' in df.columns and 'monthly_revenue' in df.columns else 0
        revenue_at_risk *= 12 # Annualize for consistency in terms of 'at risk'

        return {
            'total_customers': total_customers,
            'churned_customers': churned_customers,
            'churn_rate': churn_rate,
            'mrr': mrr,
            'avg_ltv': avg_ltv,
            'avg_tenure': avg_tenure,
            'at_risk_customers': at_risk,
            'revenue_at_risk': revenue_at_risk
        }
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return {} # Return an empty dictionary on error

def create_churn_by_segment_chart(df, segment_col, title_suffix=""):
    """Create churn rate chart by segment"""
    try:
        if segment_col not in df.columns or 'is_churned' not in df.columns:
            st.warning(f"Missing '{segment_col}' or 'is_churned' column for churn segment chart.")
            return None

        # Filter out rows where segment_col might be NaN if not handled upstream
        df_filtered = df.dropna(subset=[segment_col])

        if df_filtered.empty: # Check if DataFrame is empty after dropping NaNs
            st.info(f"No data for {segment_col} after filtering out missing values.")
            return None

        segment_stats = df_filtered.groupby(segment_col).agg({
            'customer_id': 'count',
            'is_churned': ['sum', 'mean'],
            'monthly_revenue': 'sum'
        }).reset_index()

        segment_stats.columns = [segment_col, 'total_customers', 'churned_customers', 'churn_rate', 'total_revenue']
        segment_stats['churn_rate'] = segment_stats['churn_rate'] * 100

        fig = px.bar(
            segment_stats,
            x=segment_col,
            y='churn_rate',
            title=f'Churn Rate by {segment_col.replace("_", " ").title()}{title_suffix}',
            labels={'churn_rate': 'Churn Rate (%)', segment_col: segment_col.replace("_", " ").title()},
            color='churn_rate',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating segment chart for {segment_col}: {e}")
        return None

def create_revenue_chart(df):
    """Create revenue analysis chart"""
    try:
        if 'subscription_tier' not in df.columns or 'monthly_revenue' not in df.columns:
            st.warning("Missing 'subscription_tier' or 'monthly_revenue' column for revenue chart.")
            return None

        revenue_by_tier = df.groupby('subscription_tier')['monthly_revenue'].sum().reset_index()

        fig = px.pie(
            revenue_by_tier,
            names='subscription_tier',
            values='monthly_revenue',
            title='Monthly Revenue Distribution by Tier',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating revenue chart: {e}")
        return None

def create_tenure_usage_scatter(df):
    """Create tenure vs usage scatter plot"""
    try:
        if not all(col in df.columns for col in ['customer_tenure_months', 'avg_daily_usage', 'churn_risk_level']):
            st.warning("Missing required columns for tenure vs usage scatter plot.")
            return None

        # Sample data for better performance with large datasets
        sample_df = df.sample(min(len(df), 1000)) # Ensure min is not zero if len(df) is too small

        fig = px.scatter(
            sample_df,
            x='customer_tenure_months',
            y='avg_daily_usage',
            color='churn_risk_level',
            title='Customer Tenure vs Daily Usage',
            labels={
                'customer_tenure_months': 'Tenure (Months)',
                'avg_daily_usage': 'Daily Usage',
                'churn_risk_level': 'Risk Level'
            },
            color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
        )
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating scatter plot: {e}")
        return None

def create_satisfaction_chart(df):
    """Create satisfaction score distribution"""
    try:
        if 'avg_satisfaction_score' not in df.columns:
            st.warning("Missing 'avg_satisfaction_score' column for satisfaction chart.")
            return None

        satisfaction_dist = df['avg_satisfaction_score'].value_counts().sort_index()

        fig = px.bar(
            x=satisfaction_dist.index,
            y=satisfaction_dist.values,
            title='Customer Satisfaction Score Distribution',
            labels={'x': 'Satisfaction Score', 'y': 'Number of Customers'},
            color=satisfaction_dist.values,
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        return fig
    except Exception as e:
        st.error(f"Error creating satisfaction chart: {e}")
        return None

def main():
    """Main dashboard function"""
    st.title("🎯 Customer Churn Analytics Dashboard")
    st.markdown("*Comprehensive analytics for subscription business churn and revenue optimization*")

    # Load data
    with st.spinner("Loading data..."):
        df = load_sample_data()

    if df is None or len(df) == 0:
        st.error("No data available or data loading failed.")
        return

    st.success(f"✅ Successfully loaded {len(df):,} customer records")

    # --- Sidebar Filters ---
    st.sidebar.header("⚙️ Apply Filters")

    # For single-select dropdowns, use st.selectbox
    # It's good practice to add an "All" option for selection box filters
    # when you want to show all data by default.

    # Filter by Country
    if 'country' in df.columns:
        all_countries = ['All'] + df['country'].unique().tolist()
        selected_country = st.sidebar.selectbox(
            "Select Country",
            options=all_countries,
            index=0 # 'All' is default
        )
        if selected_country != 'All':
            df = df[df['country'] == selected_country]

    # Filter by Company Size
    if 'company_size' in df.columns:
        company_size_order = ['All', 'startup', 'small', 'medium', 'large', 'enterprise']
        # Ensure only relevant options are in the list based on current data
        available_company_sizes = [s for s in company_size_order if s == 'All' or s in df['company_size'].unique()]
        selected_company_size = st.sidebar.selectbox(
            "Select Company Size",
            options=available_company_sizes,
            index=0
        )
        if selected_company_size != 'All':
            df = df[df['company_size'] == selected_company_size]

    # Filter by Industry
    if 'industry' in df.columns:
        all_industries = ['All'] + df['industry'].unique().tolist()
        selected_industry = st.sidebar.selectbox(
            "Select Industry",
            options=all_industries,
            index=0
        )
        if selected_industry != 'All':
            df = df[df['industry'] == selected_industry]

    # Filter by Subscription Tier
    if 'subscription_tier' in df.columns:
        subscription_tier_order = ['All', 'basic', 'premium', 'enterprise']
        available_subscription_tiers = [s for s in subscription_tier_order if s == 'All' or s in df['subscription_tier'].unique()]
        selected_subscription_tier = st.sidebar.selectbox(
            "Select Subscription Tier",
            options=available_subscription_tiers,
            index=0
        )
        if selected_subscription_tier != 'All':
            df = df[df['subscription_tier'] == selected_subscription_tier]

    # Filter by Churn Risk Level
    if 'churn_risk_level' in df.columns:
        risk_level_order = ['All', 'low', 'medium', 'high']
        available_risk_levels = [l for l in risk_level_order if l == 'All' or l in df['churn_risk_level'].unique()]
        selected_risk_level = st.sidebar.selectbox(
            "Filter by Churn Risk Level",
            options=available_risk_levels,
            index=0
        )
        if selected_risk_level != 'All':
            df = df[df['churn_risk_level'] == selected_risk_level]

    # Filter by Customer Tenure (Months) - Slider remains for range selection
    if 'customer_tenure_months' in df.columns and not df['customer_tenure_months'].empty:
        # Check if min/max tenure are valid numbers before using them
        if not df['customer_tenure_months'].isnull().all(): # Check if not all are NaN
            min_tenure_val = df['customer_tenure_months'].min()
            max_tenure_val = df['customer_tenure_months'].max()

            # Handle cases where min/max might be the same (e.g., all customers have 0 tenure)
            if min_tenure_val == max_tenure_val:
                st.sidebar.write(f"Customer Tenure (Months): {min_tenure_val:.1f}")
                tenure_range = (min_tenure_val, max_tenure_val) # Set range to single value
            else:
                tenure_range = st.sidebar.slider(
                    "Customer Tenure (Months)",
                    min_value=float(min_tenure_val),
                    max_value=float(max_tenure_val),
                    value=(float(min_tenure_val), float(max_tenure_val)),
                    step=0.1
                )
            df = df[(df['customer_tenure_months'] >= tenure_range[0]) & (df['customer_tenure_months'] <= tenure_range[1])]
        else:
            st.sidebar.info("Customer Tenure data is not available for filtering.")


    # Filter by Monthly Revenue - Slider remains for range selection
    if 'monthly_revenue' in df.columns and not df['monthly_revenue'].empty:
        if not df['monthly_revenue'].isnull().all():
            min_revenue_val = df['monthly_revenue'].min()
            max_revenue_val = df['monthly_revenue'].max()

            if min_revenue_val == max_revenue_val:
                st.sidebar.write(f"Monthly Revenue ($): ${min_revenue_val:,.0f}")
                revenue_range = (min_revenue_val, max_revenue_val)
            else:
                revenue_range = st.sidebar.slider(
                    "Monthly Revenue ($)",
                    min_value=float(min_revenue_val),
                    max_value=float(max_revenue_val),
                    value=(float(min_revenue_val), float(max_revenue_val)),
                    step=1.0
                )
            df = df[(df['monthly_revenue'] >= revenue_range[0]) & (df['monthly_revenue'] <= revenue_range[1])]
        else:
            st.sidebar.info("Monthly Revenue data is not available for filtering.")


    # Check if filtered DataFrame is empty
    if df.empty:
        st.warning("No customers match the selected filter criteria. Please adjust your filters.")
        return # Exit main if no data to display

    # Recalculate metrics after filtering
    metrics = calculate_metrics(df)

    if not metrics: # Check if metrics dictionary is empty due to an error (e.g., filtered df is empty, leading to division by zero)
        st.error("Could not calculate key metrics after filtering. Please adjust filters.")
        return

    # Display key metrics
    st.markdown("### 📊 Executive Dashboard")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Customers",
            f"{metrics.get('total_customers', 0):,}",
            help="Total number of customers in the dataset"
        )

    with col2:
        churn_rate = metrics.get('churn_rate', 0)
        # Use a consistent delta for demonstration, or remove if not truly dynamic
        delta_churn = np.random.uniform(-0.5, 0.5)
        st.metric(
            "Churn Rate",
            f"{churn_rate:.1f}%",
            delta=f"{delta_churn:.1f}%",
            delta_color="inverse" if churn_rate > 15 else "normal", # Dynamic delta color based on churn rate
            help="Percentage of customers who have churned"
        )

    with col3:
        delta_mrr = np.random.randint(1000, 5000)
        st.metric(
            "Monthly Recurring Revenue",
            f"${metrics.get('mrr', 0):,.0f}",
            delta=f"+${delta_mrr:,}",
            help="Total monthly recurring revenue from active customers"
        )

    with col4:
        delta_risk_customers = np.random.randint(-10, 5)
        st.metric(
            "High-Risk Customers",
            f"{metrics.get('at_risk_customers', 0):,}",
            delta=f"{delta_risk_customers:+d}",
            delta_color="inverse",
            help="Customers with high churn risk scores"
        )

    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Average LTV", f"${metrics.get('avg_ltv', 0):,.0f}")

    with col2:
        st.metric("Average Tenure", f"{metrics.get('avg_tenure', 0):.1f} months")

    with col3:
        st.metric("Revenue at Risk", f"${metrics.get('revenue_at_risk', 0):,.0f}")

    with col4:
        retention_rate = 100 - metrics.get('churn_rate', 0)
        st.metric("Retention Rate", f"{retention_rate:.1f}%")

    st.markdown("---")

    # Analytics tabs - UPDATED TABS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Churn Analysis",
        "💰 Revenue Analysis",
        "👥 Customer Segments",
        "📈 Value & Adoption", # New tab for LTV & Feature Adoption
        "⚠️ Risk Management",
        "💡 Recommendations", # New tab for Recommended Actions
        "📋 Data Explorer"
    ])

    with tab1:
        st.markdown("#### Churn Analysis by Customer Segments")

        col1, col2 = st.columns(2)

        with col1:
            chart = create_churn_by_segment_chart(df, 'subscription_tier')
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            chart = create_churn_by_segment_chart(df, 'company_size')
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        # Industry analysis
        col1, col2 = st.columns(2)

        with col1:
            chart = create_churn_by_segment_chart(df, 'industry')
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            chart = create_satisfaction_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

    with tab2:
        st.markdown("#### Revenue Analysis")

        col1, col2 = st.columns(2)

        with col1:
            chart = create_revenue_chart(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            # Revenue at risk by segment
            if 'churn_risk_level' in df.columns and 'monthly_revenue' in df.columns:
                risk_revenue = df.groupby('churn_risk_level')['monthly_revenue'].sum().reset_index()
                fig = px.bar(
                    risk_revenue,
                    x='churn_risk_level',
                    y='monthly_revenue',
                    title='Monthly Revenue by Risk Level',
                    color='churn_risk_level',
                    color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Missing 'churn_risk_level' or 'monthly_revenue' column for Revenue by Risk Level chart.")

        # LTV analysis and Feature Adoption Analysis are now in a new tab

    with tab3: # Customer Segments
        st.markdown("#### Customer Segmentation Analysis")

        col1, col2 = st.columns(2)

        with col1:
            chart = create_tenure_usage_scatter(df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)

        with col2:
            if 'churn_risk_level' in df.columns:
                risk_dist = df['churn_risk_level'].value_counts()
                fig = px.pie(
                    values=risk_dist.values,
                    names=risk_dist.index,
                    title='Customer Risk Distribution',
                    color_discrete_map={'low': 'green', 'medium': 'orange', 'high': 'red'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Missing 'churn_risk_level' column for Customer Risk Distribution chart.")

        # Feature adoption analysis is now in a new tab

    with tab4: # 📈 Value & Adoption (New Tab)
        st.markdown("#### Customer Lifetime Value Analysis")
        if 'total_revenue' in df.columns:
            col1, col2, col3 = st.columns(3)

            with col1:
                ltv_by_tier = df.groupby('subscription_tier')['total_revenue'].mean().reset_index()
                fig = px.bar(ltv_by_tier, x='subscription_tier', y='total_revenue',
                             title='Average LTV by Subscription Tier')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                ltv_by_size = df.groupby('company_size')['total_revenue'].mean().reset_index()
                fig = px.bar(ltv_by_size, x='company_size', y='total_revenue',
                             title='Average LTV by Company Size')
                st.plotly_chart(fig, use_container_width=True)

            with col3:
                fig = px.histogram(df, x='total_revenue', nbins=30,
                                   title='LTV Distribution')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Missing 'total_revenue' column for Customer Lifetime Value Analysis.")

        st.markdown("#### Feature Adoption Analysis")
        if 'features_adopted' in df.columns and 'subscription_tier' in df.columns:
            col1, col2 = st.columns(2)

            with col1:
                avg_features_by_tier = df.groupby('subscription_tier')['features_adopted'].mean().reset_index()
                fig = px.bar(avg_features_by_tier, x='subscription_tier', y='features_adopted',
                             title='Average Features Adopted by Tier')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.histogram(df, x='features_adopted', nbins=15,
                                   title='Distribution of Features Adopted')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Missing 'features_adopted' or 'subscription_tier' column for Feature Adoption Analysis.")


    with tab5: # Risk Management (original tab, content remains)
        st.markdown("#### Risk Management Dashboard")

        # High-risk customers
        if 'churn_risk_level' in df.columns:
            high_risk = df[df['churn_risk_level'] == 'high'].copy()

            if len(high_risk) > 0:
                st.markdown(f"**🚨 {len(high_risk):,} High-Risk Customers Identified**")

                # Sort by risk score
                if 'churn_risk_score' in high_risk.columns:
                    high_risk = high_risk.sort_values('churn_risk_score', ascending=False)

                # Top 20 high-risk customers
                display_cols = [col for col in ['customer_id', 'company_name', 'subscription_tier',
                               'monthly_revenue', 'churn_risk_score', 'last_activity_days_ago',
                               'support_tickets', 'avg_satisfaction_score']
                               if col in high_risk.columns]

                st.dataframe(
                    high_risk[display_cols].head(20),
                    use_container_width=True,
                    hide_index=True
                )

                # Risk factor analysis
                st.markdown("#### Risk Factor Breakdown")

                col1, col2 = st.columns(2)

                with col1:
                    risk_factors = []
                    # Ensure risk calculation columns exist before checking them
                    if all(col in df.columns for col in ['last_activity_days_ago', 'avg_daily_usage', 'support_tickets']):
                        inactive_pct = (df['last_activity_days_ago'] > 30).mean() * 100
                        risk_factors.append({"Factor": "Inactive > 30 days", "Percentage": inactive_pct})

                        low_usage_pct = (df['avg_daily_usage'] < 1).mean() * 100
                        risk_factors.append({"Factor": "Low daily usage", "Percentage": low_usage_pct})

                        high_support_pct = (df['support_tickets'] > 5).mean() * 100
                        risk_factors.append({"Factor": "High support tickets", "Percentage": high_support_pct})

                    if risk_factors:
                        risk_df = pd.DataFrame(risk_factors)
                        fig = px.bar(risk_df, x='Factor', y='Percentage',
                                     title='Risk Factors in Customer Base')
                        fig.update_traces(marker_color='red', opacity=0.7)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No primary risk factors identified in the data for this chart.")

                with col2:
                    # Risk score distribution
                    fig = px.histogram(df, x='churn_risk_score', nbins=20,
                                       title='Churn Risk Score Distribution')
                    fig.add_vline(x=0.5, line_dash="dash", line_color="red",
                                  annotation_text="High Risk Threshold")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No high-risk customers identified based on current criteria.")
        else:
            st.warning("Missing 'churn_risk_level' column for Risk Management Dashboard.")


        # Action recommendations are now in a new tab

    with tab6: # 💡 Recommendations (New Tab)
        st.markdown("#### 💡 Recommended Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.error("""
            **🚨 Immediate Actions (High Risk)**
            - Personal outreach to top 50 at-risk customers
            - Offer usage training sessions
            - Provide dedicated customer success manager
            - Consider pricing incentives for renewals
            """)

        with col2:
            st.warning("""
            **⚠️ Medium-term Actions (Medium Risk)**
            - Automated email engagement campaigns
            - Feature adoption workshops
            - Regular health score check-ins
            - Product usage optimization tips
            """)

        with col3:
            st.info("""
            **ℹ️ Preventive Actions (Low Risk)**
            - Monthly product newsletters
            - Feature announcement updates
            - Customer satisfaction surveys
            - Referral program enrollment
            """)

    with tab7: # Data Explorer (original tab, content remains)
        st.markdown("#### Data Explorer")

        # Data overview
        st.markdown("**Dataset Overview:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Total Records:** {len(df):,}")
            st.write(f"**Total Columns:** {len(df.columns)}")

        with col2:
            # Check if signup_date column exists before accessing
            if 'signup_date' in df.columns and not df['signup_date'].empty:
                st.write(f"**Date Range:** {df['signup_date'].min().strftime('%Y-%m-%d')} to {df['signup_date'].max().strftime('%Y-%m-%d')}")
            else:
                st.write("**Date Range:** N/A (signup_date column missing or empty)")

            if 'country' in df.columns:
                st.write(f"**Countries:** {df['country'].nunique()}")
            else:
                st.write("**Countries:** N/A (country column missing)")

        with col3:
            if 'industry' in df.columns:
                st.write(f"**Industries:** {df['industry'].nunique()}")
            else:
                st.write("**Industries:** N/A (industry column missing)")

            if 'subscription_tier' in df.columns:
                st.write(f"**Subscription Tiers:** {df['subscription_tier'].nunique()}")
            else:
                st.write("**Subscription Tiers:** N/A (subscription_tier column missing)")

        # Sample data
        st.markdown("**Sample Data:**")
        st.dataframe(df.head(10), use_container_width=True)

        # Column information
        with st.expander("📋 Column Details"):
            st.write("**Available columns:**")
            for i, col in enumerate(df.columns, 1):
                st.write(f"{i}. **{col}** - {df[col].dtype}")

if __name__ == "__main__":
    main()
