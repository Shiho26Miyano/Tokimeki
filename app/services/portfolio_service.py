import asyncio
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class PortfolioState(TypedDict, total=False):
    """State object for portfolio management workflow"""
    tickers: List[str]
    primary: str
    start: str
    end: str
    fee_bps: float
    slip_bps: float
    
    # Shared artifacts
    prices: pd.DataFrame
    features: Dict[str, pd.DataFrame]
    regime: str
    thesis: List[str]
    strategy_params: Dict[str, Any]
    position: Dict[str, pd.Series]
    backtest_results: Dict[str, Any]
    risk_notes: List[str]
    trade_plan: List[str]
    agent_log: List[str]

class PortfolioService:
    """Multi-agent portfolio management service"""
    
    def __init__(self):
        self.state: PortfolioState = {}
    
    def log(self, msg: str):
        """Add message to agent log"""
        if "agent_log" not in self.state:
            self.state["agent_log"] = []
        self.state["agent_log"].append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")
    
    async def data_agent(self, state: PortfolioState) -> PortfolioState:
        """Data Agent: Load and prepare market data"""
        try:
            self.log("DataAgent: Starting data collection...")
            
            # Download price data
            data = yf.download(
                state["tickers"], 
                start=state["start"], 
                end=state["end"], 
                auto_adjust=True, 
                progress=False
            )
            
            if data.empty:
                raise ValueError("No data retrieved from Yahoo Finance")
            
            # Handle single ticker case
            if len(state["tickers"]) == 1:
                close = data["Close"].to_frame()
            else:
                close = data["Close"]
            
            # Calculate features for each ticker
            features = {}
            for ticker in state["tickers"]:
                if ticker not in close.columns:
                    continue
                    
                series = close[ticker].dropna()
                if len(series) < 50:  # Need minimum data
                    continue
                    
                features[ticker] = pd.DataFrame({
                    "close": series,
                    "returns": series.pct_change(),
                    "ma_fast": series.rolling(20).mean(),
                    "ma_slow": series.rolling(50).mean(),
                    "volatility_20": series.pct_change().rolling(20).std() * np.sqrt(252),
                    "atr_20": self._calculate_atr(series, 20),
                    "rsi_14": self._calculate_rsi(series, 14),
                    "bb_upper": self._calculate_bollinger_bands(series, 20, 2)[0],
                    "bb_lower": self._calculate_bollinger_bands(series, 20, 2)[1],
                })
            
            state["prices"] = close
            state["features"] = features
            
            self.log(f"DataAgent: Loaded {len(close)} rows for {list(features.keys())} tickers")
            return state
            
        except Exception as e:
            self.log(f"DataAgent: Error - {str(e)}")
            raise
    
    async def research_agent(self, state: PortfolioState) -> PortfolioState:
        """Research Agent: Analyze market regime and generate thesis"""
        try:
            self.log("ResearchAgent: Analyzing market conditions...")
            
            # Determine regime based on primary ticker
            primary = state["primary"]
            if primary not in state["features"]:
                raise ValueError(f"Primary ticker {primary} not found in features")
            
            features = state["features"][primary]
            close = features["close"]
            
            # Regime detection
            if len(close) > 60:
                # 3-month trend
                slope_3m = (close.iloc[-1] / close.iloc[-60]) - 1
                # 1-month momentum
                momentum_1m = (close.iloc[-1] / close.iloc[-20]) - 1
                # Volatility regime
                current_vol = features["volatility_20"].iloc[-1]
                avg_vol = features["volatility_20"].mean()
                
                if slope_3m > 0.05 and momentum_1m > 0.02:
                    regime = "Bull"
                elif slope_3m < -0.05 and momentum_1m < -0.02:
                    regime = "Bear"
                elif current_vol > avg_vol * 1.5:
                    regime = "High Volatility"
                elif current_vol < avg_vol * 0.7:
                    regime = "Low Volatility"
                else:
                    regime = "Neutral"
            else:
                regime = "Insufficient Data"
            
            # Generate thesis
            thesis = [
                f"Market Regime: **{regime}**",
                f"Primary Asset: {primary}",
                f"Current Volatility: {features['volatility_20'].iloc[-1]:.1%}",
                f"Trend Strength: {'Strong' if abs(slope_3m) > 0.1 else 'Moderate' if abs(slope_3m) > 0.05 else 'Weak'}",
                "Risk Management: Use regime-appropriate position sizing and stop levels"
            ]
            
            state["regime"] = regime
            state["thesis"] = thesis
            
            self.log(f"ResearchAgent: Identified {regime} regime")
            return state
            
        except Exception as e:
            self.log(f"ResearchAgent: Error - {str(e)}")
            raise
    
    async def strategy_agent(self, state: PortfolioState) -> PortfolioState:
        """Strategy Agent: Generate trading strategy parameters"""
        try:
            self.log("StrategyAgent: Designing trading strategy...")
            
            primary = state["primary"]
            features = state["features"][primary]
            regime = state.get("regime", "Neutral")
            
            # Strategy selection based on regime
            if regime == "Bull":
                strategy_type = "Momentum"
                fast_ma, slow_ma = 10, 30
                position_size = 1.0
            elif regime == "Bear":
                strategy_type = "Mean Reversion"
                fast_ma, slow_ma = 5, 20
                position_size = 0.5
            elif regime == "High Volatility":
                strategy_type = "Volatility Breakout"
                fast_ma, slow_ma = 15, 40
                position_size = 0.3
            else:
                strategy_type = "Trend Following"
                fast_ma, slow_ma = 20, 50
                position_size = 0.7
            
            # Generate position signals
            ma_fast = features[f"ma_fast"]
            ma_slow = features[f"ma_slow"]
            
            # Basic crossover strategy
            position = pd.Series(0.0, index=features.index)
            position[ma_fast > ma_slow] = position_size
            position[ma_fast < ma_slow] = -position_size * 0.5  # Short position smaller
            
            # Add volatility filter
            vol_filter = features["volatility_20"] < features["volatility_20"].rolling(60).quantile(0.8)
            position = position * vol_filter.astype(float)
            
            strategy_params = {
                "type": strategy_type,
                "fast_ma": fast_ma,
                "slow_ma": slow_ma,
                "position_size": position_size,
                "volatility_filter": True,
                "regime": regime
            }
            
            state["strategy_params"] = strategy_params
            state["position"] = {primary: position}
            
            self.log(f"StrategyAgent: Created {strategy_type} strategy")
            return state
            
        except Exception as e:
            self.log(f"StrategyAgent: Error - {str(e)}")
            raise
    
    async def risk_agent(self, state: PortfolioState) -> PortfolioState:
        """Risk Agent: Analyze risk metrics and generate risk notes"""
        try:
            self.log("RiskAgent: Calculating risk metrics...")
            
            primary = state["primary"]
            close = state["features"][primary]["close"]
            position = state["position"][primary]
            
            # Run backtest
            backtest_results = self._run_backtest(
                close, position, 
                state["fee_bps"], state["slip_bps"]
            )
            
            # Risk analysis
            risk_notes = []
            
            # Maximum drawdown analysis
            max_dd = backtest_results["max_drawdown"]
            if max_dd < -0.25:
                risk_notes.append("⚠️ Max Drawdown > 25% - Consider position size reduction")
            elif max_dd < -0.15:
                risk_notes.append("⚠️ Max Drawdown > 15% - Monitor risk levels closely")
            
            # Sharpe ratio analysis
            sharpe = backtest_results["sharpe_ratio"]
            if sharpe < 0.5:
                risk_notes.append("⚠️ Sharpe Ratio < 0.5 - Strategy may need refinement")
            elif sharpe > 1.5:
                risk_notes.append("✅ Sharpe Ratio > 1.5 - Strong risk-adjusted returns")
            
            # Volatility analysis
            current_vol = state["features"][primary]["volatility_20"].iloc[-1]
            if current_vol > 0.3:
                risk_notes.append("⚠️ High current volatility - Consider reducing position size")
            
            # Correlation risk
            if len(state["tickers"]) > 1:
                corr_matrix = state["prices"].corr()
                high_corr_pairs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        if abs(corr_matrix.iloc[i, j]) > 0.8:
                            high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j]))
                
                if high_corr_pairs:
                    risk_notes.append(f"⚠️ High correlation pairs detected: {high_corr_pairs}")
            
            if not risk_notes:
                risk_notes.append("✅ Risk metrics within acceptable ranges")
            
            state["backtest_results"] = backtest_results
            state["risk_notes"] = risk_notes
            
            self.log(f"RiskAgent: MaxDD={max_dd:.1%}, Sharpe={sharpe:.2f}")
            return state
            
        except Exception as e:
            self.log(f"RiskAgent: Error - {str(e)}")
            raise
    
    async def execution_agent(self, state: PortfolioState) -> PortfolioState:
        """Execution Agent: Generate trade plan and execution details"""
        try:
            self.log("ExecutionAgent: Creating trade execution plan...")
            
            primary = state["primary"]
            current_price = state["features"][primary]["close"].iloc[-1]
            current_position = state["position"][primary].iloc[-1]
            atr = state["features"][primary]["atr_20"].iloc[-1]
            
            # Generate trade plan
            trade_plan = [
                f"Asset: {primary}",
                f"Current Price: ${current_price:.2f}",
                f"Strategy: {state['strategy_params']['type']}",
                f"Position Size: {current_position:.1%}",
                f"Stop Loss: ${current_price - 2*atr:.2f} (2× ATR)",
                f"Take Profit: ${current_price + 3*atr:.2f} (3× ATR)",
                f"Risk per Trade: {abs(current_position) * 2*atr/current_price:.1%}",
                f"Regime: {state['regime']}",
                f"Execution: Market order during normal hours",
                f"Rebalance: Weekly on Friday close"
            ]
            
            # Add regime-specific notes
            if state["regime"] == "High Volatility":
                trade_plan.append("⚠️ High volatility - Use smaller position sizes")
            elif state["regime"] == "Bear":
                trade_plan.append("⚠️ Bear market - Consider hedging strategies")
            
            state["trade_plan"] = trade_plan
            
            self.log("ExecutionAgent: Trade plan completed")
            return state
            
        except Exception as e:
            self.log(f"ExecutionAgent: Error - {str(e)}")
            raise
    
    async def run_portfolio_workflow(self, config: Dict[str, Any]) -> PortfolioState:
        """Run the complete portfolio management workflow"""
        try:
            # Initialize state
            self.state = {
                "tickers": config["tickers"],
                "primary": config["primary"],
                "start": config["start"],
                "end": config["end"],
                "fee_bps": config["fee_bps"],
                "slip_bps": config["slip_bps"],
                "agent_log": []
            }
            
            # Run agents sequentially
            self.state = await self.data_agent(self.state)
            self.state = await self.research_agent(self.state)
            self.state = await self.strategy_agent(self.state)
            self.state = await self.risk_agent(self.state)
            self.state = await self.execution_agent(self.state)
            
            self.log("Portfolio workflow completed successfully")
            return self.state
            
        except Exception as e:
            self.log(f"Portfolio workflow failed: {str(e)}")
            raise
    
    def _calculate_atr(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Average True Range"""
        high = prices  # Simplified - using close as proxy
        low = prices
        close = prices
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> tuple:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, lower_band
    
    def _run_backtest(self, prices: pd.Series, position: pd.Series, fee_bps: float, slip_bps: float) -> Dict[str, Any]:
        """Run backtest with transaction costs"""
        returns = prices.pct_change().fillna(0.0)
        position = position.reindex(returns.index).fillna(0.0)
        
        # Transaction costs
        trade_cost = (fee_bps + slip_bps) / 10000
        costs = position.diff().abs().fillna(position.abs()) * trade_cost
        
        # Strategy returns
        strategy_returns = position.shift(1).fillna(0.0) * returns - costs
        
        # Calculate metrics
        equity = (1 + strategy_returns).cumprod()
        drawdown = equity / equity.cummax() - 1
        
        # Annualized metrics
        annual_return = (equity.iloc[-1] ** (252/len(equity))) - 1 if len(equity) > 0 else 0
        annual_volatility = strategy_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        max_drawdown = drawdown.min()
        
        # Win rate
        winning_trades = (strategy_returns > 0).sum()
        total_trades = (strategy_returns != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            "returns": strategy_returns,
            "equity": equity,
            "drawdown": drawdown,
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "total_return": equity.iloc[-1] - 1,
            "calmar_ratio": annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        }
