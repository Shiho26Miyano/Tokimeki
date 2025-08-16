import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Portfolio Manager Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .agent-log {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        max-height: 300px;
        overflow-y: auto;
    }
    .risk-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-note {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_api_connection():
    """Test connection to the backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}/test", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_portfolio_analysis(config):
    """Run portfolio analysis via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio/analyze",
            json=config,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def create_price_chart(prices_data, features_data, primary_ticker):
    """Create interactive price chart with indicators"""
    if primary_ticker not in features_data:
        return None
    
    features = features_data[primary_ticker]
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'close': features['close'],
        'ma_fast': features['ma_fast'],
        'ma_slow': features['ma_slow'],
        'bb_upper': features.get('bb_upper', pd.Series()),
        'bb_lower': features.get('bb_lower', pd.Series()),
        'volatility': features['volatility_20']
    })
    
    # Create subplot
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f'{primary_ticker} Price & Indicators', 'Volatility'),
        row_heights=[0.7, 0.3]
    )
    
    # Price and moving averages
    fig.add_trace(
        go.Scatter(x=df.index, y=df['close'], name='Close Price', line=dict(color='#1f77b4')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['ma_fast'], name='Fast MA', line=dict(color='#ff7f0e')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['ma_slow'], name='Slow MA', line=dict(color='#2ca02c')),
        row=1, col=1
    )
    
    # Bollinger Bands if available
    if not df['bb_upper'].empty and not df['bb_lower'].empty:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', 
                      line=dict(color='rgba(0,0,0,0.3)', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', 
                      line=dict(color='rgba(0,0,0,0.3)', dash='dash')),
            row=1, col=1
        )
    
    # Volatility
    fig.add_trace(
        go.Scatter(x=df.index, y=df['volatility'], name='Volatility', 
                  line=dict(color='#d62728'), fill='tonexty'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text=f"{primary_ticker} Technical Analysis"
    )
    
    return fig

def create_backtest_chart(backtest_data):
    """Create backtest performance chart"""
    if not backtest_data:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'equity': backtest_data['equity'],
        'drawdown': backtest_data['drawdown']
    })
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('Portfolio Equity', 'Drawdown'),
        row_heights=[0.6, 0.4]
    )
    
    # Equity curve
    fig.add_trace(
        go.Scatter(x=df.index, y=df['equity'], name='Portfolio Value', 
                  line=dict(color='#1f77b4'), fill='tonexty'),
        row=1, col=1
    )
    
    # Drawdown
    fig.add_trace(
        go.Scatter(x=df.index, y=df['drawdown'], name='Drawdown', 
                  line=dict(color='#d62728'), fill='tonexty'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=500,
        showlegend=True,
        title_text="Backtest Performance"
    )
    
    return fig

def display_risk_metrics(backtest_data):
    """Display risk metrics in a formatted way"""
    if not backtest_data:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Annual Return",
            f"{backtest_data['annual_return']:.1%}",
            delta=f"{backtest_data['annual_return']:.1%}"
        )
    
    with col2:
        st.metric(
            "Sharpe Ratio",
            f"{backtest_data['sharpe_ratio']:.2f}",
            delta="Good" if backtest_data['sharpe_ratio'] > 1.0 else "Needs improvement"
        )
    
    with col3:
        st.metric(
            "Max Drawdown",
            f"{backtest_data['max_drawdown']:.1%}",
            delta="High risk" if backtest_data['max_drawdown'] < -0.2 else "Acceptable"
        )
    
    with col4:
        st.metric(
            "Win Rate",
            f"{backtest_data['win_rate']:.1%}",
            delta="Good" if backtest_data['win_rate'] > 0.5 else "Needs improvement"
        )

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Portfolio Manager Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("Multi-Agent Portfolio Analysis & Risk Management")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("📋 Configuration")
        
        # Ticker input
        tickers_input = st.text_input(
            "Tickers (comma-separated)",
            value="SPY,QQQ,AAPL,MSFT",
            help="Enter stock symbols separated by commas"
        )
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        # Primary ticker selection
        primary_ticker = st.selectbox(
            "Primary Ticker",
            options=tickers,
            index=0 if tickers else None
        )
        
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        start_date = st.date_input("Start Date", value=start_date)
        end_date = st.date_input("End Date", value=end_date)
        
        # Cost parameters
        st.subheader("💰 Transaction Costs")
        fee_bps = st.slider("Commission (bps)", 0.0, 50.0, 1.0, 0.5)
        slip_bps = st.slider("Slippage (bps)", 0.0, 100.0, 2.0, 0.5)
        
        # Run analysis button
        run_analysis = st.button("🚀 Run Portfolio Analysis", type="primary", use_container_width=True)
        
        # API status
        st.subheader("🔌 API Status")
        if test_api_connection():
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Disconnected")
            st.info("Make sure the FastAPI backend is running on localhost:8000")
    
    # Main content area
    if run_analysis and tickers and primary_ticker:
        st.info("🔄 Running multi-agent portfolio analysis...")
        
        # Prepare configuration
        config = {
            "tickers": tickers,
            "primary": primary_ticker,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "fee_bps": fee_bps,
            "slip_bps": slip_bps
        }
        
        # Run analysis
        with st.spinner("Agents are working..."):
            result = run_portfolio_analysis(config)
        
        if result and result.get("success"):
            data = result["data"]
            
            # Display results in tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Overview", "🔍 Research", "📈 Strategy", "⚠️ Risk", "📋 Execution"
            ])
            
            with tab1:
                st.header("Portfolio Overview")
                
                # Key metrics
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if "prices" in data and "features" in data:
                        fig = create_price_chart(data["prices"], data["features"], primary_ticker)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Market Regime")
                    regime = data.get("regime", "Unknown")
                    st.markdown(f"**Current Regime:** {regime}")
                    
                    if "thesis" in data:
                        st.subheader("Research Thesis")
                        for point in data["thesis"]:
                            st.markdown(f"• {point}")
                    
                    st.subheader("Quick Stats")
                    if "features" in data and primary_ticker in data["features"]:
                        features = data["features"][primary_ticker]
                        if "volatility_20" in features:
                            current_vol = list(features["volatility_20"].values())[-1]
                            st.metric("Current Volatility", f"{current_vol:.1%}")
            
            with tab2:
                st.header("Research Agent Analysis")
                
                if "thesis" in data:
                    st.subheader("Market Analysis")
                    for point in data["thesis"]:
                        st.markdown(f"• {point}")
                
                if "regime" in data:
                    regime = data["regime"]
                    st.subheader("Regime Classification")
                    
                    regime_info = {
                        "Bull": "Strong upward trend with positive momentum",
                        "Bear": "Strong downward trend with negative momentum", 
                        "High Volatility": "Elevated volatility above historical average",
                        "Low Volatility": "Below average volatility levels",
                        "Neutral": "Sideways or mixed market conditions"
                    }
                    
                    st.info(f"**{regime}**: {regime_info.get(regime, 'Unknown regime')}")
            
            with tab3:
                st.header("Strategy Agent Output")
                
                if "strategy_params" in data:
                    params = data["strategy_params"]
                    st.subheader("Strategy Parameters")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Strategy Type", params.get("type", "Unknown"))
                        st.metric("Fast MA", params.get("fast_ma", "N/A"))
                    with col2:
                        st.metric("Slow MA", params.get("slow_ma", "N/A"))
                        st.metric("Position Size", f"{params.get('position_size', 0):.1%}")
                    
                    st.subheader("Strategy Logic")
                    st.info(f"""
                    **{params.get('type', 'Unknown')} Strategy**
                    - Fast moving average: {params.get('fast_ma', 'N/A')} days
                    - Slow moving average: {params.get('slow_ma', 'N/A')} days
                    - Position sizing: {params.get('position_size', 0):.1%}
                    - Volatility filter: {'Enabled' if params.get('volatility_filter') else 'Disabled'}
                    """)
            
            with tab4:
                st.header("Risk Agent Analysis")
                
                if "backtest_results" in data:
                    backtest_data = data["backtest_results"]
                    
                    # Risk metrics
                    st.subheader("Risk Metrics")
                    display_risk_metrics(backtest_data)
                    
                    # Risk chart
                    st.subheader("Performance Chart")
                    fig = create_backtest_chart(backtest_data)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Risk notes
                    if "risk_notes" in data:
                        st.subheader("Risk Analysis")
                        for note in data["risk_notes"]:
                            if "⚠️" in note:
                                st.markdown(f'<div class="risk-warning">{note}</div>', unsafe_allow_html=True)
                            elif "✅" in note:
                                st.markdown(f'<div class="success-note">{note}</div>', unsafe_allow_html=True)
                            else:
                                st.info(note)
            
            with tab5:
                st.header("Execution Agent Plan")
                
                if "trade_plan" in data:
                    st.subheader("Trade Execution Plan")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        for item in data["trade_plan"]:
                            st.markdown(f"• {item}")
                    
                    with col2:
                        st.subheader("Current Position")
                        if "position" in data and primary_ticker in data["position"]:
                            position_data = data["position"][primary_ticker]
                            current_pos = list(position_data.values())[-1]
                            
                            if current_pos > 0:
                                st.success(f"Long: {current_pos:.1%}")
                            elif current_pos < 0:
                                st.error(f"Short: {abs(current_pos):.1%}")
                            else:
                                st.info("Flat")
                
                # Agent activity log
                if "agent_log" in data:
                    st.subheader("Agent Activity Log")
                    st.markdown('<div class="agent-log">', unsafe_allow_html=True)
                    for log_entry in data["agent_log"]:
                        st.text(log_entry)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        elif result:
            st.error("❌ Analysis failed")
            st.json(result)
        else:
            st.error("❌ No results returned")
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to the Portfolio Manager Dashboard!
        
        This dashboard uses a multi-agent system to analyze portfolios:
        
        - **Data Agent**: Collects and processes market data
        - **Research Agent**: Analyzes market conditions and identifies regimes
        - **Strategy Agent**: Designs trading strategies based on market conditions
        - **Risk Agent**: Calculates risk metrics and provides risk analysis
        - **Execution Agent**: Creates trade execution plans
        
        ### Getting Started:
        1. Configure your portfolio in the sidebar
        2. Select tickers and date range
        3. Set transaction costs
        4. Click "Run Portfolio Analysis"
        
        ### Features:
        - Multi-timeframe analysis
        - Regime-aware strategy selection
        - Risk-adjusted performance metrics
        - Interactive charts and visualizations
        - Agent activity logging
        """)
        
        # Example configuration
        st.subheader("Example Configuration")
        st.code("""
        Tickers: SPY, QQQ, AAPL, MSFT
        Primary: SPY
        Date Range: 1 year
        Commission: 1 bps
        Slippage: 2 bps
        """)

if __name__ == "__main__":
    main()
