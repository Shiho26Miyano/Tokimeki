"""
ETF Analytics Service
Service for calculating risk metrics, technical indicators, and holdings analysis
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, timedelta

from app.models.etf_models import (
    ETFRiskMetrics, ETFTechnicalIndicators, ETFHolding,
    ETFSectorDistribution, ETFIndustryDistribution
)

logger = logging.getLogger(__name__)


class ETFAnalyticsService:
    """Analytics service for ETF data"""
    
    def __init__(self):
        pass
    
    def calculate_volatility(self, prices: List[float], window: int = 30, annualized: bool = True) -> Optional[float]:
        """Calculate volatility from price series"""
        if len(prices) < window + 1:
            return None
        
        try:
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    returns.append((prices[i] - prices[i-1]) / prices[i-1])
                else:
                    returns.append(0)
            
            if len(returns) < window:
                return None
            
            # Get last window returns
            window_returns = returns[-window:]
            
            # Calculate standard deviation
            std_dev = np.std(window_returns)
            
            # Annualize if requested (assuming 252 trading days)
            if annualized:
                volatility = std_dev * np.sqrt(252) * 100  # As percentage
            else:
                volatility = std_dev * 100
            
            return round(volatility, 2)
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return None
    
    def calculate_beta(self, etf_prices: List[float], benchmark_prices: List[float]) -> Optional[float]:
        """Calculate Beta vs benchmark"""
        if len(etf_prices) != len(benchmark_prices) or len(etf_prices) < 2:
            return None
        
        try:
            # Calculate returns
            etf_returns = []
            benchmark_returns = []
            
            for i in range(1, len(etf_prices)):
                if etf_prices[i-1] > 0 and benchmark_prices[i-1] > 0:
                    etf_returns.append((etf_prices[i] - etf_prices[i-1]) / etf_prices[i-1])
                    benchmark_returns.append((benchmark_prices[i] - benchmark_prices[i-1]) / benchmark_prices[i-1])
            
            if len(etf_returns) < 2:
                return None
            
            # Calculate covariance and variance
            covariance = np.cov(etf_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            
            if benchmark_variance == 0:
                return None
            
            beta = covariance / benchmark_variance
            return round(beta, 2)
            
        except Exception as e:
            logger.error(f"Error calculating beta: {str(e)}")
            return None
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> Optional[float]:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return None
        
        try:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return None
            
            # Annualize (assuming 252 trading days)
            annualized_return = mean_return * 252
            annualized_std = std_return * np.sqrt(252)
            
            sharpe = (annualized_return - risk_free_rate) / annualized_std
            return round(sharpe, 2)
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            return None
    
    def calculate_max_drawdown(self, prices: List[float]) -> Tuple[Optional[float], Optional[int]]:
        """Calculate maximum drawdown and duration"""
        if len(prices) < 2:
            return None, None
        
        try:
            peak = prices[0]
            max_drawdown = 0
            max_drawdown_duration = 0
            current_drawdown_duration = 0
            
            for price in prices:
                if price > peak:
                    peak = price
                    current_drawdown_duration = 0
                else:
                    drawdown = (peak - price) / peak if peak > 0 else 0
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                    current_drawdown_duration += 1
                    if current_drawdown_duration > max_drawdown_duration:
                        max_drawdown_duration = current_drawdown_duration
            
            return round(max_drawdown * 100, 2), max_drawdown_duration
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {str(e)}")
            return None, None
    
    def calculate_current_drawdown(self, prices: List[float]) -> Optional[float]:
        """Calculate current drawdown from peak"""
        if len(prices) < 2:
            return None
        
        try:
            peak = max(prices)
            current_price = prices[-1]
            
            if peak > 0:
                drawdown = (peak - current_price) / peak * 100
                return round(drawdown, 2)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating current drawdown: {str(e)}")
            return None
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> Optional[float]:
        """Calculate Value at Risk"""
        if len(returns) < 2:
            return None
        
        try:
            percentile = (1 - confidence_level) * 100
            var = np.percentile(returns, percentile)
            return round(var * 100, 2)  # As percentage
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {str(e)}")
            return None
    
    def calculate_rsi(self, prices: List[float], window: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < window + 1:
            return None
        
        try:
            # Calculate price changes
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            # Separate gains and losses
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            # Calculate average gain and loss over window
            avg_gain = np.mean(gains[-window:])
            avg_loss = np.mean(losses[-window:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return None
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return None, None, None
        
        try:
            # Convert to pandas Series for easier calculation
            series = pd.Series(prices)
            
            # Calculate EMAs
            ema_fast = series.ewm(span=fast, adjust=False).mean()
            ema_slow = series.ewm(span=slow, adjust=False).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line (EMA of MACD)
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            
            # Histogram
            histogram = macd_line - signal_line
            
            # Get latest values
            macd = round(float(macd_line.iloc[-1]), 4)
            signal = round(float(signal_line.iloc[-1]), 4)
            hist = round(float(histogram.iloc[-1]), 4)
            
            return macd, signal, hist
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return None, None, None
    
    def calculate_moving_averages(self, prices: List[float]) -> Dict[str, Optional[float]]:
        """Calculate various moving averages"""
        result = {
            'sma_20': None,
            'sma_50': None,
            'sma_200': None,
            'ema_12': None,
            'ema_26': None
        }
        
        try:
            series = pd.Series(prices)
            
            if len(prices) >= 20:
                result['sma_20'] = round(float(series.tail(20).mean()), 2)
            if len(prices) >= 50:
                result['sma_50'] = round(float(series.tail(50).mean()), 2)
            if len(prices) >= 200:
                result['sma_200'] = round(float(series.tail(200).mean()), 2)
            if len(prices) >= 12:
                result['ema_12'] = round(float(series.ewm(span=12, adjust=False).mean().iloc[-1]), 2)
            if len(prices) >= 26:
                result['ema_26'] = round(float(series.ewm(span=26, adjust=False).mean().iloc[-1]), 2)
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {str(e)}")
        
        return result
    
    def calculate_bollinger_bands(self, prices: List[float], window: int = 20, num_std: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands"""
        if len(prices) < window:
            return None, None, None
        
        try:
            series = pd.Series(prices)
            sma = series.tail(window).mean()
            std = series.tail(window).std()
            
            upper = sma + (num_std * std)
            middle = sma
            lower = sma - (num_std * std)
            
            return round(float(upper), 2), round(float(middle), 2), round(float(lower), 2)
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return None, None, None
    
    def calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], window: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        if len(highs) < window + 1 or len(lows) < window + 1 or len(closes) < window + 1:
            return None
        
        try:
            true_ranges = []
            for i in range(1, len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            if len(true_ranges) < window:
                return None
            
            atr = np.mean(true_ranges[-window:])
            return round(atr, 2)
            
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return None
    
    def calculate_risk_metrics(
        self,
        symbol: str,
        prices: List[float],
        benchmark_prices: Optional[List[float]] = None,
        risk_free_rate: float = 0.02
    ) -> ETFRiskMetrics:
        """Calculate comprehensive risk metrics"""
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
            else:
                returns.append(0)
        
        # Volatility
        volatility_30d = self.calculate_volatility(prices, window=30)
        volatility_60d = self.calculate_volatility(prices, window=60)
        volatility_1y = self.calculate_volatility(prices, window=min(252, len(prices)-1))
        
        # Beta
        beta = None
        if benchmark_prices and len(benchmark_prices) == len(prices):
            beta = self.calculate_beta(prices, benchmark_prices)
        
        # Sharpe ratio
        sharpe_ratio = None
        if len(returns) >= 30:
            sharpe_ratio = self.calculate_sharpe_ratio(returns, risk_free_rate)
        
        # Max drawdown
        max_drawdown, max_drawdown_duration = self.calculate_max_drawdown(prices)
        current_drawdown = self.calculate_current_drawdown(prices)
        
        # VaR
        var_95 = None
        var_99 = None
        if len(returns) >= 30:
            var_95 = self.calculate_var(returns, confidence_level=0.95)
            var_99 = self.calculate_var(returns, confidence_level=0.99)
        
        return ETFRiskMetrics(
            symbol=symbol,
            analysis_date=date.today(),
            volatility_30d=volatility_30d,
            volatility_60d=volatility_60d,
            volatility_1y=volatility_1y,
            beta=beta,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            current_drawdown=current_drawdown,
            var_95=var_95,
            var_99=var_99
        )
    
    def calculate_technical_indicators(
        self,
        symbol: str,
        dates: List[date],
        prices: List[float],
        highs: Optional[List[float]] = None,
        lows: Optional[List[float]] = None,
        closes: Optional[List[float]] = None
    ) -> List[ETFTechnicalIndicators]:
        """Calculate technical indicators for all dates"""
        indicators = []
        
        if closes is None:
            closes = prices
        
        try:
            # Calculate moving averages
            ma_data = self.calculate_moving_averages(prices)
            
            # Calculate RSI
            rsi = self.calculate_rsi(prices)
            
            # Calculate MACD
            macd, macd_signal, macd_hist = self.calculate_macd(prices)
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
            
            # Calculate ATR
            atr = None
            if highs and lows and closes:
                atr = self.calculate_atr(highs, lows, closes)
            
            # Create indicator for latest date
            latest_date = dates[-1] if dates else date.today()
            
            indicator = ETFTechnicalIndicators(
                symbol=symbol,
                date=latest_date,
                sma_20=ma_data.get('sma_20'),
                sma_50=ma_data.get('sma_50'),
                sma_200=ma_data.get('sma_200'),
                ema_12=ma_data.get('ema_12'),
                ema_26=ma_data.get('ema_26'),
                rsi_14=rsi,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_hist,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                atr_14=atr
            )
            
            indicators.append(indicator)
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
        
        return indicators
    
    def analyze_holdings(self, holdings: List[ETFHolding]) -> Dict[str, Any]:
        """Analyze ETF holdings"""
        if not holdings:
            return {
                'total_holdings': 0,
                'top_10_concentration': None,
                'sector_distribution': [],
                'industry_distribution': []
            }
        
        # Calculate top 10 concentration
        sorted_holdings = sorted(holdings, key=lambda h: h.weight or 0, reverse=True)
        top_10 = sorted_holdings[:10]
        top_10_concentration = sum(h.weight or 0 for h in top_10)
        
        # Sector distribution
        sector_dict = {}
        for holding in holdings:
            if holding.sector:
                if holding.sector not in sector_dict:
                    sector_dict[holding.sector] = {'weight': 0, 'count': 0}
                sector_dict[holding.sector]['weight'] += holding.weight or 0
                sector_dict[holding.sector]['count'] += 1
        
        sector_distribution = [
            ETFSectorDistribution(
                sector=sector,
                weight=round(data['weight'], 2),
                holdings_count=data['count']
            )
            for sector, data in sector_dict.items()
        ]
        
        # Industry distribution
        industry_dict = {}
        for holding in holdings:
            if holding.industry:
                if holding.industry not in industry_dict:
                    industry_dict[holding.industry] = {'weight': 0, 'count': 0}
                industry_dict[holding.industry]['weight'] += holding.weight or 0
                industry_dict[holding.industry]['count'] += 1
        
        industry_distribution = [
            ETFIndustryDistribution(
                industry=industry,
                weight=round(data['weight'], 2),
                holdings_count=data['count']
            )
            for industry, data in industry_dict.items()
        ]
        
        return {
            'total_holdings': len(holdings),
            'top_10_concentration': round(top_10_concentration, 2),
            'sector_distribution': sector_distribution,
            'industry_distribution': industry_distribution
        }
    
    def calculate_top_holdings(self, holdings: List[ETFHolding], top_n: int = 10) -> List[ETFHolding]:
        """Get top N holdings by weight"""
        if not holdings:
            return []
        
        sorted_holdings = sorted(holdings, key=lambda h: h.weight or 0, reverse=True)
        return sorted_holdings[:top_n]

