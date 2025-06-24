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
    .ios-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
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
    
    .kpi-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        color: white;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
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
    
    .apple-maps-container {
        background: linear-gradient(145deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 12px 20px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        font-weight: bold !important;
        color: #000000 !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Mart Classes for Better Structure ---
class DataMartManager:
    """Manages data marts following dbt patterns"""
    
    def __init__(self):
        # Try multiple possible paths for dbt models
        possible_paths = [
            Path("dbt_models/models/marts"),
            Path("models/marts"),
            Path("marts"),
            Path("data/marts"),
            Path("data")
        ]
        
        self.data_path = None
        for path in possible_paths:
            if path.exists():
                self.data_path = path
                break
        
        if self.data_path is None:
            self.data_path = Path("data")
            self.data_path.mkdir(exist_ok=True)
        
        self.marts = {}
        
    def load_mart(self, mart_name, required=True):
        """Load a data mart with error handling"""
        try:
            # Try different file extensions and naming conventions
            possible_files = [
                self.data_path / f"{mart_name}.csv",
                self.data_path / f"{mart_name}.sql",
                self.data_path / f"{mart_name}.parquet",
                # Also try without marts prefix if the mart_name includes it
                self.data_path / f"{mart_name.replace('mart_', '')}.csv",
                self.data_path / f"{mart_name.replace('mart_', '')}.sql"
            ]
            
            for file_path in possible_files:
                if file_path.exists():
                    if file_path.suffix == '.csv':
                        self.marts[mart_name] = pd.read_csv(file_path)
                        return self.marts[mart_name]
                    elif file_path.suffix == '.sql':
                        # For SQL files, we'll use generated data (SQL execution not available)
                        return self._generate_fallback_data(mart_name)
                    elif file_path.suffix == '.parquet':
                        self.marts[mart_name] = pd.read_parquet(file_path)
                        return self.marts[mart_name]
            
            # No files found
            if required:
                st.error(f"Required data mart '{mart_name}' not found in {self.data_path}")
                st.stop()
            else:
                return self._generate_fallback_data(mart_name)
                
        except Exception as e:
            if required:
                st.error(f"Error loading {mart_name}: {str(e)}")
                st.stop()
            else:
                return self._generate_fallback_data(mart_name)
    
    def _generate_fallback_data(self, mart_name):
        """Generate fallback data when marts are missing"""
        if mart_name == "dim_customers":
            return self._generate_customer_dimension()
        elif mart_name == "dim_products":
            return self._generate_product_dimension()
        elif mart_name == "fact_subscription_metrics":
            return self._generate_subscription_facts()
        elif mart_name == "fact_customer_ltv":
            return self._generate_ltv_facts()
        elif mart_name == "fact_pricing_optimization":
            return self._generate_pricing_facts()
        elif mart_name == "mart_executive_summary":
            return self._generate_executive_summary()
        else:
            return pd.DataFrame()
    
    def _generate_customer_dimension(self):
        """Generate sample customer dimension data"""
        np.random.seed(42)
        customers = []
        segments = ['CHAMPION', 'LOYAL', 'POTENTIAL_LOYAL', 'NEW_CUSTOMER', 'PROMISING', 'AT_RISK', 'HIBERNATING']
        industries = ['Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing', 'Education']
        company_sizes = ['Small', 'Medium', 'Large', 'Enterprise']
        countries = ['United States', 'Canada', 'United Kingdom', 'Germany', 'France', 'Australia', 'Japan', 'Brazil', 'India', 'Mexico']
        states = ['California', 'Texas', 'New York', 'Florida', 'Illinois', 'Pennsylvania', 'Ohio', 'Washington', 'North Carolina', 'Georgia']
        churn_risks = ['LOW', 'MEDIUM', 'HIGH']
        
        for i in range(1000):
            country = np.random.choice(countries)
            state = np.random.choice(states) if country == 'United States' else None
            
            customers.append({
                'customer_id': f'CUST_{i:04d}',
                'industry': np.random.choice(industries),
                'company_size': np.random.choice(company_sizes),
                'country': country,
                'state': state,
                'customer_segment': np.random.choice(segments),
                'estimated_ltv': np.random.uniform(500, 15000),
                'churn_risk': np.random.choice(churn_risks),
                'customer_health_score': np.random.uniform(10, 100),
                'current_mrr': np.random.uniform(50, 500),
                'months_since_first_subscription': np.random.randint(1, 36),
                'total_subscriptions': np.random.randint(1, 5),
                'active_subscriptions': np.random.randint(1, 3)
            })
        return pd.DataFrame(customers)
    
    def _generate_product_dimension(self):
        """Generate sample product dimension data"""
        products = []
        hubs = ['CMS', 'CRM', 'Marketing', 'Analytics', 'Sales']
        tiers = ['Starter', 'Professional', 'Enterprise']
        
        for hub in hubs:
            for tier in tiers:
                products.append({
                    'hub': hub,
                    'tier': tier,
                    'product_full_name': f"{hub} - {tier}",
                    'avg_monthly_revenue': np.random.uniform(29, 299),
                    'total_subscribers': np.random.randint(50, 500),
                    'active_subscribers': np.random.randint(40, 450),
                    'retention_rate': np.random.uniform(0.85, 0.98)
                })
        return pd.DataFrame(products)
    
    def _generate_subscription_facts(self):
        """Generate sample subscription metrics facts"""
        np.random.seed(42)
        facts = []
        hubs = ['CMS', 'CRM', 'Marketing', 'Analytics', 'Sales']
        tiers = ['Starter', 'Professional', 'Enterprise']
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(90):
            date = base_date + timedelta(days=i)
            for hub in hubs:
                for tier in tiers:
                    facts.append({
                        'metric_date': date.strftime('%Y-%m-%d'),
                        'hub': hub,
                        'tier': tier,
                        'active_subscriptions': np.random.randint(50, 300),
                        'new_subscriptions': np.random.randint(0, 10),
                        'churned_subscriptions': np.random.randint(0, 5),
                        'total_mrr': np.random.uniform(5000, 50000),
                        'new_mrr': np.random.uniform(0, 2000),
                        'churned_mrr': np.random.uniform(0, 1000),
                        'daily_churn_rate_pct': np.random.uniform(0.1, 2.0),
                        'arpu': np.random.uniform(80, 200)
                    })
        return pd.DataFrame(facts)
    
    def _generate_ltv_facts(self):
        """Generate sample LTV facts"""
        np.random.seed(42)
        facts = []
        segments = ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']
        
        for i in range(500):
            facts.append({
                'customer_id': f'CUST_{i:04d}',
                'predicted_ltv': np.random.uniform(500, 15000),
                'total_historical_revenue': np.random.uniform(100, 8000),
                'current_mrr': np.random.uniform(50, 500),
                'ltv_segment': np.random.choice(segments),
                'customer_roi_pct': np.random.uniform(150, 500),
                'payback_period_months': np.random.uniform(2, 12)
            })
        return pd.DataFrame(facts)
    
    def _generate_pricing_facts(self):
        """Generate sample pricing optimization facts"""
        np.random.seed(42)
        facts = []
        hubs = ['CMS', 'CRM', 'Marketing', 'Analytics', 'Sales']
        tiers = ['Starter', 'Professional', 'Enterprise']
        recommendations = ['IMPLEMENT_IMMEDIATELY', 'TEST_RECOMMENDED', 'CAREFUL_TESTING', 'MONITOR', 'AVOID']
        
        for hub in hubs:
            for tier in tiers:
                for i in range(5):  # 5 pricing scenarios per product
                    base_price = np.random.uniform(50, 300)
                    price_point = base_price * (0.8 + i * 0.1)  # Price variations
                    
                    facts.append({
                        'hub': hub,
                        'tier': tier,
                        'price_point': price_point,
                        'current_avg_price': base_price,
                        'potential_monthly_revenue': np.random.uniform(10000, 80000),
                        'potential_customers': np.random.randint(100, 800),
                        'revenue_change_pct': np.random.uniform(-20, 40),
                        'customer_change_pct': np.random.uniform(-30, 20),
                        'optimal_price': price_point if i == 2 else None,  # Mark middle scenario as optimal
                        'optimal_revenue_uplift_pct': np.random.uniform(5, 25) if i == 2 else None,
                        'strategic_recommendation': np.random.choice(recommendations),
                        'revenue_rank': i + 1
                    })
        return pd.DataFrame(facts)
    
    def _generate_executive_summary(self):
        """Generate sample executive summary matching the dbt model schema"""
        return pd.DataFrame([{
            'current_month': datetime.now().strftime('%Y-%m-01'),
            'current_month_avg_mrr': np.random.uniform(150000, 200000),
            'current_month_avg_customers': np.random.randint(1500, 2000),
            'current_month_avg_churn_rate': np.random.uniform(1.5, 3.0),
            'mrr_growth_mom_pct': np.random.uniform(3, 8),
            'customer_growth_mom_pct': np.random.uniform(2, 6),
            'top_hub_by_revenue': 'Marketing',
            'top_hub_revenue': np.random.uniform(80000, 120000),
            'champion_customers': np.random.randint(100, 200),
            'champion_mrr': np.random.uniform(50000, 80000),
            'total_high_risk_customers': np.random.randint(50, 150),
            'immediate_pricing_opportunities': np.random.randint(3, 8),
            'total_pricing_upside_pct': np.random.uniform(15, 35),
            'report_generated_at': datetime.now().isoformat(),
            'report_type': 'EXECUTIVE_SUMMARY'
        }])

# --- Initialize Data Marts ---
@st.cache_data
def load_data_marts():
    """Load all data marts using the manager"""
    dm = DataMartManager()
    
    marts = {
        'dim_customers': dm.load_mart('dim_customers', required=False),
        'dim_products': dm.load_mart('dim_products', required=False),
        'fact_subscription_metrics': dm.load_mart('fact_subscription_metrics', required=False),
        'fact_customer_ltv': dm.load_mart('fact_customer_ltv', required=False),
        'fact_pricing_optimization': dm.load_mart('fact_pricing_optimization', required=False),
        'mart_executive_summary': dm.load_mart('mart_executive_summary', required=False)
    }
    
    return marts

# Load all data marts
data_marts = load_data_marts()

# --- Tab Navigation ---
st.set_page_config(page_title="Hub Monetization Insights", page_icon="💸", layout="wide")

# --- Sidebar Filters ---
st.sidebar.title("🎛️ Hub Filters")

# Initialize filter variables
selected_hub = "All Hubs"
selected_tier = "All Tiers"
selected_segment = "All Segments"
selected_country = "All Countries"
selected_ltv_segment = "All LTV Segments"

# Hub selection from products dimension
if not data_marts['dim_products'].empty and 'hub' in data_marts['dim_products'].columns:
    unique_hubs = sorted(data_marts['dim_products']['hub'].unique())
    selected_hub = st.sidebar.selectbox("🏢 Choose a Hub", ["All Hubs"] + unique_hubs)
else:
    st.sidebar.info("Hub filter not available - no product data")

# Tier selection from products dimension
if not data_marts['dim_products'].empty and 'tier' in data_marts['dim_products'].columns:
    unique_tiers = sorted(data_marts['dim_products']['tier'].unique())
    selected_tier = st.sidebar.selectbox("🎯 Choose a Tier", ["All Tiers"] + unique_tiers)
else:
    st.sidebar.info("Tier filter not available - no product data")

# Customer segment filter
if not data_marts['dim_customers'].empty and 'customer_segment' in data_marts['dim_customers'].columns:
    unique_segments = sorted(data_marts['dim_customers']['customer_segment'].unique())
    selected_segment = st.sidebar.selectbox(
        "👥 Customer Segment",
        ["All Segments"] + unique_segments
    )
else:
    st.sidebar.info("Customer segment filter not available")

# Country filter
if not data_marts['dim_customers'].empty and 'country' in data_marts['dim_customers'].columns:
    unique_countries = sorted(data_marts['dim_customers']['country'].unique())
    selected_country = st.sidebar.selectbox(
        "🌍 Choose a Country",
        ["All Countries"] + unique_countries
    )
else:
    st.sidebar.info("Country filter not available")

# LTV Segment filter
if not data_marts['fact_customer_ltv'].empty and 'ltv_segment' in data_marts['fact_customer_ltv'].columns:
    unique_ltv_segments = sorted(data_marts['fact_customer_ltv']['ltv_segment'].unique())
    selected_ltv_segment = st.sidebar.selectbox(
        "💰 LTV Segment",
        ["All LTV Segments"] + unique_ltv_segments
    )
else:
    st.sidebar.info("LTV segment filter not available")

# --- Helper Functions ---
def apply_filters_to_customers(df):
    """Apply global filters to customer data"""
    if df.empty:
        return df
        
    filtered_df = df.copy()
    
    # Apply customer segment filter
    if selected_segment != "All Segments" and 'customer_segment' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['customer_segment'] == selected_segment]
    
    # Apply country filter
    if selected_country != "All Countries" and 'country' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['country'] == selected_country]
    
    return filtered_df

def apply_filters_to_metrics(df):
    """Apply global filters to subscription metrics"""
    if df.empty:
        return df
        
    filtered_df = df.copy()
    
    # Apply hub filter
    if selected_hub != "All Hubs" and 'hub' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['hub'] == selected_hub]
    
    # Apply tier filter  
    if selected_tier != "All Tiers" and 'tier' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['tier'] == selected_tier]
    
    return filtered_df

def apply_filters_to_ltv(df):
    """Apply global filters to LTV data"""
    if df.empty:
        return df
        
    filtered_df = df.copy()
    
    # Apply LTV segment filter
    if selected_ltv_segment != "All LTV Segments" and 'ltv_segment' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['ltv_segment'] == selected_ltv_segment]
    
    return filtered_df

def apply_filters_to_pricing(df):
    """Apply global filters to pricing optimization data"""
    if df.empty:
        return df
        
    filtered_df = df.copy()
    
    # Apply hub filter
    if selected_hub != "All Hubs" and 'hub' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['hub'] == selected_hub]
    
    # Apply tier filter
    if selected_tier != "All Tiers" and 'tier' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['tier'] == selected_tier]
    
    return filtered_df

def create_ios_metric_card(title, value, subtitle="", color_gradient="135deg, #667eea 0%, #764ba2 100%"):
    """Create iOS-style metric cards"""
    st.markdown(f"""
    <div style="background: linear-gradient({color_gradient}); border-radius: 12px; padding: 20px; margin: 8px 0; color: white; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
        <div style="font-size: 0.9em; opacity: 0.9; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">{title}</div>
        <div style="font-size: 2.2em; font-weight: 700; margin: 8px 0; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">{value}</div>
        <div style="font-size: 0.8em; opacity: 0.8;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Main Dashboard Title ---
st.title("💸 Hub Monetization Insights Dashboard")
st.markdown("### Data Mart-Driven Analytics")

# Create tabs
tabs = st.tabs([
    "📊 Executive Summary", "💵 Customer Analytics", "🔄 Funnel Analysis", 
    "📈 Subscription Metrics", "💰 LTV Analysis", "🎯 Pricing Strategy", 
    "📊 Financial Projections", "🧠 Recommendations"
])

# --- Tab 1: Executive Summary (Using mart_executive_summary) ---
with tabs[0]:
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    st.subheader("📈 Executive KPI Dashboard")
    
    if not data_marts['mart_executive_summary'].empty:
        exec_data = data_marts['mart_executive_summary'].iloc[0]
        
        # Top-level KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_ios_metric_card(
                "MONTHLY REVENUE", 
                f"${exec_data['current_month_avg_mrr']:,.0f}",
                f"Growth: {exec_data['mrr_growth_mom_pct']:+.1f}%",
                "135deg, #00b894 0%, #00a085 100%"
            )
        
        with col2:
            create_ios_metric_card(
                "ACTIVE CUSTOMERS", 
                f"{exec_data['current_month_avg_customers']:,.0f}",
                f"Growth: {exec_data['customer_growth_mom_pct']:+.1f}%",
                "135deg, #74b9ff 0%, #0984e3 100%"
            )
        
        with col3:
            create_ios_metric_card(
                "CHURN RATE", 
                f"{exec_data['current_month_avg_churn_rate']:.2f}%",
                "Monthly average",
                "135deg, #fd79a8 0%, #e84393 100%"
            )
        
        with col4:
            create_ios_metric_card(
                "CHAMPION CUSTOMERS", 
                f"{exec_data['champion_customers']:,.0f}",
                "High-value segment",
                "135deg, #fdcb6e 0%, #e17055 100%"
            )
        
        # Second row of KPIs
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            create_ios_metric_card(
                "TOP HUB", 
                exec_data['top_hub_by_revenue'],
                "By revenue",
                "135deg, #a29bfe 0%, #6c5ce7 100%"
            )
        
        with col6:
            create_ios_metric_card(
                "AT-RISK CUSTOMERS", 
                f"{exec_data['total_high_risk_customers']:,.0f}",
                "Require attention",
                "135deg, #e17055 0%, #d63031 100%"
            )
        
        with col7:
            create_ios_metric_card(
                "PRICING OPPORTUNITIES", 
                f"{exec_data['immediate_pricing_opportunities']:,.0f}",
                "Ready to implement",
                "135deg, #55a3ff 0%, #003d82 100%"
            )
        
        with col8:
            # Calculate ARR
            arr = exec_data['current_month_avg_mrr'] * 12
            create_ios_metric_card(
                "ANNUAL REVENUE", 
                f"${arr:,.0f}",
                "ARR projection",
                "135deg, #00cec9 0%, #00b894 100%"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 2: Customer Analytics (Using dim_customers) ---
with tabs[1]:
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    st.subheader("👥 Customer Analytics KPIs")
    
    filtered_customers = apply_filters_to_customers(data_marts['dim_customers'])
    
    if not filtered_customers.empty:
        # KPIs FIRST - Top Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_ios_metric_card("AVG HEALTH SCORE", f"{filtered_customers['customer_health_score'].mean():.1f}",
                                 "Customer health average",
                                 "135deg, #00b894 0%, #00a085 100%")
        with col2:
            create_ios_metric_card("AVG LTV", f"${filtered_customers['estimated_ltv'].mean():,.0f}",
                                 "Lifetime value average",
                                 "135deg, #74b9ff 0%, #0984e3 100%")
        with col3:
            high_risk_pct = (filtered_customers['churn_risk'] == 'HIGH').mean() * 100
            create_ios_metric_card("HIGH RISK %", f"{high_risk_pct:.1f}%",
                                 "Customers at risk",
                                 "135deg, #fd79a8 0%, #e84393 100%")
        with col4:
            total_customers = len(filtered_customers)
            create_ios_metric_card("TOTAL CUSTOMERS", f"{total_customers:,}",
                                 "In current filter",
                                 "135deg, #fdcb6e 0%, #e17055 100%")
        
        # Second Row of KPIs
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            avg_mrr = filtered_customers['current_mrr'].mean()
            create_ios_metric_card("AVG MRR", f"${avg_mrr:.0f}",
                                 "Monthly recurring revenue",
                                 "135deg, #a29bfe 0%, #6c5ce7 100%")
        with col6:
            total_mrr = filtered_customers['current_mrr'].sum()
            create_ios_metric_card("TOTAL MRR", f"${total_mrr:,.0f}",
                                 "Combined monthly revenue",
                                 "135deg, #00cec9 0%, #00b894 100%")
        with col7:
            champion_pct = (filtered_customers['customer_segment'] == 'CHAMPION').mean() * 100
            create_ios_metric_card("CHAMPION %", f"{champion_pct:.1f}%",
                                 "Top tier customers",
                                 "135deg, #e17055 0%, #d63031 100%")
        with col8:
            avg_tenure = filtered_customers['months_since_first_subscription'].mean()
            create_ios_metric_card("AVG TENURE", f"{avg_tenure:.1f}mo",
                                 "Customer lifetime",
                                 "135deg, #55a3ff 0%, #003d82 100%")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # VISUALIZATIONS SECOND - Side by Side Cards
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("📊 Customer Analysis Visualizations")
    
    if not filtered_customers.empty:
        # Side by side visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Customer segment distribution
            segment_dist = filtered_customers['customer_segment'].value_counts()
            fig_segments = px.pie(
                values=segment_dist.values, 
                names=segment_dist.index,
                title="Customer Segment Distribution"
            )
            fig_segments.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                font=dict(size=12)
            )
            st.plotly_chart(fig_segments, use_container_width=True)
        
        with col2:
            # Health score vs MRR scatter
            fig_health = px.scatter(
                filtered_customers,
                x='customer_health_score',
                y='current_mrr',
                color='churn_risk',
                size='estimated_ltv',
                title="Customer Health Score vs MRR"
            )
            fig_health.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                font=dict(size=12)
            )
            st.plotly_chart(fig_health, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 3: Funnel Analysis ---
with tabs[2]:
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    st.subheader("🔄 Customer Acquisition & Conversion Funnel")
    
    # Funnel-specific filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Hub filter for funnel
        funnel_hub = st.selectbox(
            "📍 Funnel Hub Filter",
            ["All Hubs"] + (sorted(data_marts['dim_products']['hub'].unique()) if not data_marts['dim_products'].empty else []),
            key="funnel_hub"
        )
    
    with col2:
        # Tier filter for funnel
        funnel_tier = st.selectbox(
            "🎯 Funnel Tier Filter", 
            ["All Tiers"] + (sorted(data_marts['dim_products']['tier'].unique()) if not data_marts['dim_products'].empty else []),
            key="funnel_tier"
        )
    
    with col3:
        # Country filter for funnel
        funnel_country = st.selectbox(
            "🌍 Funnel Country Filter",
            ["All Countries"] + (sorted(data_marts['dim_customers']['country'].unique()) if not data_marts['dim_customers'].empty else []),
            key="funnel_country"
        )
    
    # Apply funnel filters to get relevant data
    filtered_customers_funnel = data_marts['dim_customers'].copy()
    filtered_metrics_funnel = data_marts['fact_subscription_metrics'].copy()
    
    # Apply funnel-specific filters
    if funnel_country != "All Countries" and 'country' in filtered_customers_funnel.columns:
        filtered_customers_funnel = filtered_customers_funnel[filtered_customers_funnel['country'] == funnel_country]
    
    if funnel_hub != "All Hubs" and 'hub' in filtered_metrics_funnel.columns:
        filtered_metrics_funnel = filtered_metrics_funnel[filtered_metrics_funnel['hub'] == funnel_hub]
    
    if funnel_tier != "All Tiers" and 'tier' in filtered_metrics_funnel.columns:
        filtered_metrics_funnel = filtered_metrics_funnel[filtered_metrics_funnel['tier'] == funnel_tier]
    
    if not filtered_customers_funnel.empty and not filtered_metrics_funnel.empty:
        # Generate funnel data (simulated customer journey stages)
        total_visitors = len(filtered_customers_funnel) * 10  # Assume 10x more visitors than customers
        trial_signups = len(filtered_customers_funnel) * 3   # 3x more trials than paying customers
        active_trials = len(filtered_customers_funnel) * 2   # 2x more active trials
        paying_customers = len(filtered_customers_funnel)
        
        # Get latest subscription metrics for calculations
        latest_metrics = filtered_metrics_funnel[filtered_metrics_funnel['metric_date'] == filtered_metrics_funnel['metric_date'].max()] if not filtered_metrics_funnel.empty else pd.DataFrame()
        
        if not latest_metrics.empty:
            active_subscriptions = latest_metrics['active_subscriptions'].sum()
            total_mrr = latest_metrics['total_mrr'].sum()
        else:
            active_subscriptions = paying_customers
            total_mrr = paying_customers * 150  # Assume $150 average
        
        # Funnel KPIs - Top Row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            conversion_rate = (paying_customers / total_visitors * 100) if total_visitors > 0 else 0
            create_ios_metric_card(
                "OVERALL CONVERSION",
                f"{conversion_rate:.2f}%",
                f"Visitors to customers",
                "135deg, #00b894 0%, #00a085 100%"
            )
        
        with col2:
            trial_conversion = (paying_customers / trial_signups * 100) if trial_signups > 0 else 0
            create_ios_metric_card(
                "TRIAL CONVERSION",
                f"{trial_conversion:.1f}%",
                f"Trials to paid",
                "135deg, #74b9ff 0%, #0984e3 100%"
            )
        
        with col3:
            activation_rate = (active_trials / trial_signups * 100) if trial_signups > 0 else 0
            create_ios_metric_card(
                "ACTIVATION RATE",
                f"{activation_rate:.1f}%",
                f"Signups to active",
                "135deg, #fdcb6e 0%, #e17055 100%"
            )
        
        with col4:
            avg_revenue_per_customer = total_mrr / paying_customers if paying_customers > 0 else 0
            create_ios_metric_card(
                "AVG REVENUE/CUSTOMER",
                f"${avg_revenue_per_customer:.0f}",
                f"Monthly per customer",
                "135deg, #a29bfe 0%, #6c5ce7 100%"
            )
        
        # Second Row of Funnel KPIs
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            create_ios_metric_card(
                "TOTAL VISITORS",
                f"{total_visitors:,}",
                f"Website traffic",
                "135deg, #fd79a8 0%, #e84393 100%"
            )
        
        with col6:
            create_ios_metric_card(
                "TRIAL SIGNUPS",
                f"{trial_signups:,}",
                f"Free trial starts",
                "135deg, #00cec9 0%, #00b894 100%"
            )
        
        with col7:
            create_ios_metric_card(
                "ACTIVE TRIALS",
                f"{active_trials:,}",
                f"Engaged trial users",
                "135deg, #e17055 0%, #d63031 100%"
            )
        
        with col8:
            create_ios_metric_card(
                "PAYING CUSTOMERS",
                f"{paying_customers:,}",
                f"Converted customers",
                "135deg, #55a3ff 0%, #003d82 100%"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Funnel Visualization
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader("📊 Conversion Funnel Visualization")
        
        # Create funnel chart data
        funnel_stages = [
            "Website Visitors",
            "Trial Signups", 
            "Active Trials",
            "Paying Customers"
        ]
        
        funnel_values = [
            total_visitors,
            trial_signups,
            active_trials,
            paying_customers
        ]
        
        funnel_colors = [
            '#E3F2FD',  # Light blue
            '#90CAF9',  # Medium blue  
            '#42A5F5',  # Blue
            '#1E88E5'   # Dark blue
        ]
        
        # Create funnel chart using go.Funnel for proper funnel visualization
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textposition="inside",
            textinfo="value+percent initial",
            opacity=0.65,
            marker=dict(
                color=funnel_colors,
                line=dict(width=2, color="white")
            ),
            connector=dict(line=dict(color="rgb(63, 63, 63)", dash="dot", width=3))
        ))
        
        fig_funnel.update_layout(
            title=f"🔄 Customer Acquisition Funnel - {funnel_hub} {funnel_tier} ({funnel_country})",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            font=dict(size=12)
        )
        
        st.plotly_chart(fig_funnel, use_container_width=True)
        
        # Conversion Rate Analysis - Side by Side Cards
        st.subheader("📈 Stage-by-Stage Conversion Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Stage conversion rates
            stage_conversions = []
            stage_names = []
            
            for i in range(1, len(funnel_values)):
                conversion = (funnel_values[i] / funnel_values[i-1]) * 100
                stage_conversions.append(conversion)
                stage_names.append(f"{funnel_stages[i-1]} → {funnel_stages[i]}")
            
            fig_conversion = px.bar(
                x=stage_names,
                y=stage_conversions,
                title="Stage-by-Stage Conversion Rates",
                color=stage_conversions,
                color_continuous_scale=['#FFE5E5', '#FF6B6B', '#E74C3C', '#C0392B']
            )
            
            fig_conversion.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Conversion Stage",
                yaxis_title="Conversion Rate (%)",
                title="Stage-by-Stage Conversion Rates",
                showlegend=False,
                height=400
            )
            
            fig_conversion.update_traces(
                texttemplate='%{y:.1f}%',
                textposition='outside'
            )
            
            st.plotly_chart(fig_conversion, use_container_width=True)
        
        with col2:
            # Funnel insights and recommendations
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0; height: 360px;">
                <h4>🎯 Funnel Optimization Insights</h4>
                <div style="margin: 12px 0;">
                    <strong>Key Findings:</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                        <li>Overall visitor-to-customer conversion: {:.2f}%</li>
                        <li>Trial-to-paid conversion: {:.1f}%</li>
                        <li>Biggest drop-off: {} stage</li>
                    </ul>
                </div>
                <div style="margin: 12px 0;">
                    <strong>Recommendations:</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                        <li>Focus on improving trial activation</li>
                        <li>Optimize onboarding experience</li>
                        <li>Implement retargeting campaigns</li>
                        <li>A/B test pricing and messaging</li>
                    </ul>
                </div>
            </div>
            """.format(
                conversion_rate,
                trial_conversion,
                stage_names[stage_conversions.index(min(stage_conversions))] if stage_conversions else "N/A"
            ), unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.info("🔄 No funnel data available with current filter selections.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 4: Subscription Metrics (Using fact_subscription_metrics) ---
with tabs[3]:
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    st.subheader("📈 Subscription Performance KPIs")
    
    filtered_metrics = apply_filters_to_metrics(data_marts['fact_subscription_metrics'])
    
    if not filtered_metrics.empty:
        # Convert metric_date to datetime
        filtered_metrics['metric_date'] = pd.to_datetime(filtered_metrics['metric_date'])
        
        # Get latest metrics for KPIs
        latest_metrics = filtered_metrics[filtered_metrics['metric_date'] == filtered_metrics['metric_date'].max()]
        
        # KPIs FIRST - Top Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_ios_metric_card("TOTAL MRR", f"${latest_metrics['total_mrr'].sum():,.0f}",
                                 "Current monthly revenue",
                                 "135deg, #00b894 0%, #00a085 100%")
        with col2:
            create_ios_metric_card("ACTIVE SUBS", f"{latest_metrics['active_subscriptions'].sum():,.0f}",
                                 "Current subscribers",
                                 "135deg, #74b9ff 0%, #0984e3 100%")
        with col3:
            create_ios_metric_card("AVG CHURN", f"{latest_metrics['daily_churn_rate_pct'].mean():.2f}%",
                                 "Daily churn rate",
                                 "135deg, #fd79a8 0%, #e84393 100%")
        with col4:
            create_ios_metric_card("AVG ARPU", f"${latest_metrics['arpu'].mean():.0f}",
                                 "Revenue per user",
                                 "135deg, #fdcb6e 0%, #e17055 100%")
        
        # Time series visualizations
        daily_metrics = filtered_metrics.groupby('metric_date').agg({
            'total_mrr': 'sum',
            'active_subscriptions': 'sum',
            'daily_churn_rate_pct': 'mean'
        }).reset_index()
        
        # MRR trend chart
        fig_mrr = px.line(daily_metrics, x='metric_date', y='total_mrr',
                         title='MRR Trend Analysis')
        fig_mrr.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white')
        )
        fig_mrr.update_traces(line_color='rgba(0, 184, 148, 0.9)', line_width=3)
        st.plotly_chart(fig_mrr, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 5: LTV Analysis (Using fact_customer_ltv) ---
with tabs[4]:
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    st.subheader("💰 Customer Lifetime Value KPIs")
    
    ltv_data = apply_filters_to_ltv(data_marts['fact_customer_ltv'])
    
    if not ltv_data.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_ios_metric_card("AVG LTV", f"${ltv_data['predicted_ltv'].mean():,.0f}",
                                 "Predicted lifetime value",
                                 "135deg, #00b894 0%, #00a085 100%")
        with col2:
            create_ios_metric_card("TOTAL REVENUE", f"${ltv_data['total_historical_revenue'].sum():,.0f}",
                                 "Historical customer revenue",
                                 "135deg, #74b9ff 0%, #0984e3 100%")
        with col3:
            create_ios_metric_card("AVG ROI", f"{ltv_data['customer_roi_pct'].mean():.0f}%",
                                 "Return on investment",
                                 "135deg, #fdcb6e 0%, #e17055 100%")
        with col4:
            create_ios_metric_card("AVG PAYBACK", f"{ltv_data['payback_period_months'].mean():.1f}mo",
                                 "Customer payback period",
                                 "135deg, #a29bfe 0%, #6c5ce7 100%")
        
        # LTV distribution visualization
        if 'ltv_segment' in ltv_data.columns:
            fig_ltv_dist = px.box(ltv_data, x='ltv_segment', y='predicted_ltv',
                                 title='LTV Distribution by Segment')
            fig_ltv_dist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif", color='white')
            )
            st.plotly_chart(fig_ltv_dist, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 6: Pricing Strategy ---
with tabs[5]:
    st.markdown('<div class="projection-card">', unsafe_allow_html=True)
    st.subheader("🎯 Pricing Optimization Strategy")
    
    # Only show if specific hub and tier are selected
    if selected_hub != "All Hubs" and selected_tier != "All Tiers":
        pricing_data = apply_filters_to_pricing(data_marts['fact_pricing_optimization'])
        
        if not pricing_data.empty:
            # Show optimal pricing recommendations for selected product only
            optimal_prices = pricing_data[pricing_data['revenue_rank'] == 1]
            
            if not optimal_prices.empty:
                for _, row in optimal_prices.iterrows():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
                        <h4>💡 Pricing Recommendation for {row['hub']} - {row['tier']}</h4>
                        <div style="display: flex; justify-content: space-between; margin: 16px 0;">
                            <div style="text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold;">${row['current_avg_price']:.2f}</div>
                                <div>Current Price</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold;">${row.get('optimal_price', 0):.2f}</div>
                                <div>Optimal Price</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 1.5em; font-weight: bold;">{row.get('optimal_revenue_uplift_pct', 0):.1f}%</div>
                                <div>Revenue Uplift</div>
                            </div>
                        </div>
                        <p><strong>Recommendation:</strong> {row['strategic_recommendation'].replace('_', ' ').title()}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Side by side visualizations for selected product
                col1, col2 = st.columns(2)
                
                with col1:
                    # Price elasticity analysis for selected product
                    if len(pricing_data) > 1:
                        fig_elasticity = px.line(
                            pricing_data, 
                            x='price_point', 
                            y='potential_monthly_revenue',
                            title=f'Price Elasticity: {selected_hub} - {selected_tier}'
                        )
                        fig_elasticity.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            height=400,
                            font=dict(size=12, color='white')
                        )
                        st.plotly_chart(fig_elasticity, use_container_width=True)
                
                with col2:
                    # Strategic recommendations summary for selected product
                    recommendations = pricing_data['strategic_recommendation'].value_counts()
                    fig_recommendations = px.bar(
                        x=recommendations.index, 
                        y=recommendations.values,
                        title=f'Strategy Distribution: {selected_hub} - {selected_tier}'
                    )
                    fig_recommendations.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400,
                        font=dict(size=12, color='white'),
                        xaxis_title="Strategy Type",
                        yaxis_title="Count"
                    )
                    st.plotly_chart(fig_recommendations, use_container_width=True)
            else:
                st.info(f"🎯 No pricing optimization data available for {selected_hub} - {selected_tier}.")
        else:
            st.info(f"🎯 No pricing data found for {selected_hub} - {selected_tier}.")
    else:
        st.info("🎯 Please select both a specific Hub and Tier from the sidebar to view pricing strategy recommendations.")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
            <h4>📋 How to Use Pricing Strategy</h4>
            <div style="margin: 12px 0;">
                <p><strong>Steps:</strong></p>
                <ol style="margin: 8px 0; padding-left: 20px;">
                    <li>Select a specific Hub (e.g., CMS, CRM, Marketing)</li>
                    <li>Select a specific Tier (e.g., Starter, Professional, Enterprise)</li>
                    <li>View personalized pricing recommendations</li>
                    <li>Analyze price elasticity and strategic options</li>
                </ol>
            </div>
            <p><strong>Available Combinations:</strong> CMS/CRM/Marketing/Analytics/Sales × Starter/Professional/Enterprise</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 7: Financial Projections ---
with tabs[6]:
    st.markdown('<div class="projection-card">', unsafe_allow_html=True)
    st.subheader("📊 Financial Projections")
    
    if selected_hub != "All Hubs" and selected_tier != "All Tiers":
        # Interactive controls for financial modeling
        col1, col2 = st.columns(2)
        
        with col1:
            price_change = st.slider("Price Change (%)", -50, 100, 0, 5)
            customer_growth = st.slider("Annual Customer Growth (%)", -30, 200, 20, 5)
        
        with col2:
            churn_adjustment = st.slider("Churn Rate Adjustment (%)", -50, 100, 0, 5)
            cac_adjustment = st.slider("CAC Adjustment (%)", -50, 100, 0, 5)
        
        # Display projection metrics (simplified example)
        st.markdown("#### 📊 12-Month Projections")
        
        # Sample calculation for demonstration
        base_mrr = 50000
        projected_mrr = base_mrr * (1 + price_change/100) * (1 + customer_growth/100/12)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            create_ios_metric_card("PROJECTED MRR", f"${projected_mrr:,.0f}",
                                 f"12-month target",
                                 "135deg, #00b894 0%, #00a085 100%")
        with col2:
            arr_projection = projected_mrr * 12
            create_ios_metric_card("PROJECTED ARR", f"${arr_projection:,.0f}",
                                 "Annual projection",
                                 "135deg, #74b9ff 0%, #0984e3 100%")
        with col3:
            revenue_impact = ((projected_mrr - base_mrr) / base_mrr) * 100
            create_ios_metric_card("REVENUE IMPACT", f"{revenue_impact:+.1f}%",
                                 "vs current baseline",
                                 "135deg, #fdcb6e 0%, #e17055 100%")
    else:
        st.info("Please select both a Hub and Tier to view financial projections.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 8: Recommendations ---
with tabs[7]:
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("🧠 Data-Driven Strategic Recommendations")
    
    # Generate recommendations based on the data
    recommendations = []
    
    # Executive summary insights
    if not data_marts['mart_executive_summary'].empty:
        exec_summary = data_marts['mart_executive_summary'].iloc[0]
        
        if exec_summary['mrr_growth_mom_pct'] < 3:
            recommendations.append(("⚠️ Growth Acceleration Needed", 
                                   f"MRR growth of {exec_summary['mrr_growth_mom_pct']:.1f}% is below industry benchmarks. Consider pricing optimization and customer expansion strategies."))
        
        if exec_summary['total_high_risk_customers'] > exec_summary['current_month_avg_customers'] * 0.1:
            recommendations.append(("🚨 Churn Risk Management", 
                                   f"{exec_summary['total_high_risk_customers']} high-risk customers need immediate attention. Implement proactive retention programs."))
    
    # Display recommendations
    color_gradients = [
        "135deg, #667eea 0%, #764ba2 100%",
        "135deg, #74b9ff 0%, #0984e3 100%",
        "135deg, #00b894 0%, #00a085 100%",
        "135deg, #fd79a8 0%, #e84393 100%",
        "135deg, #fdcb6e 0%, #e17055 100%",
        "135deg, #a29bfe 0%, #6c5ce7 100%"
    ]
    
    for i, (title, content) in enumerate(recommendations):
        st.markdown(f"""
        <div style="background: linear-gradient({color_gradients[i % len(color_gradients)]}); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
            <h4>{title}</h4>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Strategic Action Plan
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2d3436 0%, #636e72 100%); border-radius: 12px; padding: 20px; color: white; margin: 16px 0;">
        <h4>📋 Strategic Action Plan</h4>
        <div style="margin: 16px 0;">
            <h5>🎯 Immediate Actions (0-30 days):</h5>
            <ul>
                <li>Implement pricing optimization for high-opportunity products</li>
                <li>Launch retention campaigns for high-risk customer segments</li>
                <li>Set up automated alerts for churn risk thresholds</li>
            </ul>
            
            <h5>📈 Short-term Initiatives (1-3 months):</h5>
            <ul>
                <li>A/B test recommended pricing scenarios</li>
                <li>Develop upselling programs for promising customer segments</li>
                <li>Enhance onboarding processes to improve health scores</li>
            </ul>
            
            <h5>🚀 Long-term Strategy (3-12 months):</h5>
            <ul>
                <li>Build predictive churn models using health scores</li>
                <li>Develop tiered value propositions based on LTV segments</li>
                <li>Create champion customer advocacy programs</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin: 20px 0;">
    <p>Hub Monetization Dashboard | Data Mart Architecture | Built with Streamlit & Plotly</p>
    <p>Following dbt data modeling best practices for scalable analytics</p>
</div>
""", unsafe_allow_html=True)
