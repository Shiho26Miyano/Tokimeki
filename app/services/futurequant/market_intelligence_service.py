"""
FutureExploratorium Market Intelligence Service
Advanced market analysis, sentiment analysis, and intelligence gathering
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.trading_models import Symbol, Bar
from app.models.database import get_db
from .market_data_service import market_data_service

logger = logging.getLogger(__name__)

class FutureExploratoriumMarketIntelligenceService:
    """Advanced market intelligence and analysis service"""
    
    def __init__(self):
        self.market_data_service = market_data_service
        
        # Market intelligence configuration
        self.intelligence_config = {
            "sentiment_sources": ["news", "social_media", "analyst_reports", "market_data"],
            "technical_indicators": [
                "SMA", "EMA", "RSI", "MACD", "Bollinger_Bands", 
                "Stochastic", "ATR", "Williams_R", "CCI", "ADX"
            ],
            "fundamental_metrics": [
                "volume_profile", "open_interest", "commitment_of_traders",
                "economic_indicators", "sector_rotation"
            ],
            "risk_factors": [
                "volatility_regime", "correlation_breakdown", "liquidity_crisis",
                "regulatory_changes", "geopolitical_events"
            ]
        }
    
    async def get_comprehensive_market_intelligence(
        self, 
        symbols: List[str], 
        analysis_depth: str = "standard"
    ) -> Dict[str, Any]:
        """Get comprehensive market intelligence for specified symbols"""
        try:
            # Run all intelligence analysis in parallel
            tasks = [
                self._get_market_sentiment(symbols),
                self._get_technical_analysis(symbols, analysis_depth),
                self._get_fundamental_analysis(symbols),
                self._get_risk_assessment(symbols),
                self._get_market_regime_analysis(symbols),
                self._get_correlation_analysis(symbols),
                self._get_volatility_analysis(symbols)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            intelligence = {
                "sentiment_analysis": results[0] if not isinstance(results[0], Exception) else {},
                "technical_analysis": results[1] if not isinstance(results[1], Exception) else {},
                "fundamental_analysis": results[2] if not isinstance(results[2], Exception) else {},
                "risk_assessment": results[3] if not isinstance(results[3], Exception) else {},
                "market_regime": results[4] if not isinstance(results[4], Exception) else {},
                "correlation_analysis": results[5] if not isinstance(results[5], Exception) else {},
                "volatility_analysis": results[6] if not isinstance(results[6], Exception) else {},
                "overall_score": 0.0,
                "recommendations": [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Calculate overall intelligence score
            intelligence["overall_score"] = await self._calculate_overall_score(intelligence)
            
            # Generate recommendations
            intelligence["recommendations"] = await self._generate_intelligence_recommendations(intelligence)
            
            return {
                "success": True,
                "intelligence": intelligence,
                "symbols": symbols,
                "analysis_depth": analysis_depth
            }
            
        except Exception as e:
            logger.error(f"Market intelligence error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_market_sentiment(self, symbols: List[str]) -> Dict[str, Any]:
        """Get market sentiment analysis"""
        try:
            sentiment_data = {}
            
            for symbol in symbols:
                # Simulate sentiment analysis
                # In a real implementation, this would integrate with news APIs, social media APIs, etc.
                sentiment_scores = {
                    "overall_sentiment": np.random.choice(["bullish", "bearish", "neutral"], p=[0.4, 0.3, 0.3]),
                    "news_sentiment": np.random.uniform(-1, 1),  # -1 to 1 scale
                    "social_sentiment": np.random.uniform(-1, 1),
                    "analyst_sentiment": np.random.uniform(-1, 1),
                    "technical_sentiment": np.random.uniform(-1, 1),
                    "confidence": np.random.uniform(0.6, 0.9)
                }
                
                # Calculate weighted sentiment score
                weights = {"news": 0.3, "social": 0.2, "analyst": 0.3, "technical": 0.2}
                weighted_score = sum(sentiment_scores[f"{source}_sentiment"] * weight 
                                   for source, weight in weights.items())
                
                sentiment_data[symbol] = {
                    **sentiment_scores,
                    "weighted_score": weighted_score,
                    "sentiment_strength": abs(weighted_score),
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Overall market sentiment
            overall_sentiment = np.mean([data["weighted_score"] for data in sentiment_data.values()])
            
            return {
                "symbol_sentiments": sentiment_data,
                "overall_market_sentiment": {
                    "score": overall_sentiment,
                    "interpretation": "bullish" if overall_sentiment > 0.2 else "bearish" if overall_sentiment < -0.2 else "neutral",
                    "strength": abs(overall_sentiment)
                },
                "sentiment_trend": "improving" if overall_sentiment > 0 else "deteriorating"
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return {}
    
    async def _get_technical_analysis(self, symbols: List[str], analysis_depth: str) -> Dict[str, Any]:
        """Get technical analysis for symbols"""
        try:
            technical_data = {}
            
            for symbol in symbols:
                # Get historical data for technical analysis
                db = next(get_db())
                symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
                
                if not symbol_obj:
                    continue
                
                # Get recent bars
                bars = db.query(Bar).filter(
                    Bar.symbol_id == symbol_obj.id
                ).order_by(Bar.timestamp.desc()).limit(100).all()
                
                if len(bars) < 20:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                } for bar in reversed(bars)])
                
                # Calculate technical indicators
                indicators = await self._calculate_technical_indicators(df, analysis_depth)
                
                # Trend analysis
                trend_analysis = await self._analyze_trend(df)
                
                # Support and resistance
                support_resistance = await self._find_support_resistance(df)
                
                technical_data[symbol] = {
                    "indicators": indicators,
                    "trend_analysis": trend_analysis,
                    "support_resistance": support_resistance,
                    "technical_score": np.random.uniform(0, 1),  # Simulated
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            return {
                "symbol_analysis": technical_data,
                "market_technical_score": np.mean([data["technical_score"] for data in technical_data.values()]) if technical_data else 0.5
            }
            
        except Exception as e:
            logger.error(f"Technical analysis error: {str(e)}")
            return {}
    
    async def _calculate_technical_indicators(self, df: pd.DataFrame, analysis_depth: str) -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            indicators = {}
            
            # Basic indicators
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Moving averages
            indicators['sma_20'] = float(df['close'].rolling(window=20).mean().iloc[-1]) if len(df) >= 20 else None
            indicators['sma_50'] = float(df['close'].rolling(window=50).mean().iloc[-1]) if len(df) >= 50 else None
            indicators['ema_12'] = float(df['close'].ewm(span=12).mean().iloc[-1])
            indicators['ema_26'] = float(df['close'].ewm(span=26).mean().iloc[-1])
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = float(100 - (100 / (1 + rs)).iloc[-1]) if not pd.isna(rs.iloc[-1]) else None
            
            # MACD
            macd_line = indicators['ema_12'] - indicators['ema_26'] if indicators['ema_12'] and indicators['ema_26'] else None
            signal_line = df['close'].ewm(span=9).mean().iloc[-1] if macd_line else None
            indicators['macd'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = macd_line - signal_line if macd_line and signal_line else None
            
            # Bollinger Bands
            if len(df) >= 20:
                sma_20 = df['close'].rolling(window=20).mean()
                std_20 = df['close'].rolling(window=20).std()
                indicators['bb_upper'] = float((sma_20 + (std_20 * 2)).iloc[-1])
                indicators['bb_middle'] = float(sma_20.iloc[-1])
                indicators['bb_lower'] = float((sma_20 - (std_20 * 2)).iloc[-1])
                indicators['bb_width'] = float((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'])
            
            # Stochastic
            if len(df) >= 14:
                low_14 = df['low'].rolling(window=14).min()
                high_14 = df['high'].rolling(window=14).max()
                k_percent = 100 * ((df['close'] - low_14) / (high_14 - low_14))
                indicators['stoch_k'] = float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else None
                indicators['stoch_d'] = float(k_percent.rolling(window=3).mean().iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else None
            
            # ATR (Average True Range)
            if len(df) >= 14:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                true_range = np.maximum(high_low, np.maximum(high_close, low_close))
                indicators['atr'] = float(true_range.rolling(window=14).mean().iloc[-1])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Technical indicators calculation error: {str(e)}")
            return {}
    
    async def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend direction and strength"""
        try:
            if len(df) < 20:
                return {"trend": "insufficient_data"}
            
            # Simple trend analysis
            recent_prices = df['close'].tail(20)
            trend_slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
            
            # Moving average trend
            sma_20 = df['close'].rolling(window=20).mean()
            sma_50 = df['close'].rolling(window=50).mean()
            
            current_price = df['close'].iloc[-1]
            sma_20_current = sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else current_price
            sma_50_current = sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else current_price
            
            # Trend determination
            if current_price > sma_20_current > sma_50_current:
                trend_direction = "uptrend"
            elif current_price < sma_20_current < sma_50_current:
                trend_direction = "downtrend"
            else:
                trend_direction = "sideways"
            
            # Trend strength
            trend_strength = abs(trend_slope) * 1000  # Scale for readability
            
            return {
                "trend": trend_direction,
                "strength": trend_strength,
                "slope": trend_slope,
                "price_vs_sma20": (current_price - sma_20_current) / sma_20_current * 100,
                "price_vs_sma50": (current_price - sma_50_current) / sma_50_current * 100
            }
            
        except Exception as e:
            logger.error(f"Trend analysis error: {str(e)}")
            return {"trend": "error"}
    
    async def _find_support_resistance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find support and resistance levels"""
        try:
            if len(df) < 20:
                return {"support": None, "resistance": None}
            
            # Simple support/resistance using recent highs and lows
            recent_highs = df['high'].tail(20)
            recent_lows = df['low'].tail(20)
            
            # Find resistance (recent highs)
            resistance_levels = recent_highs.nlargest(3).tolist()
            
            # Find support (recent lows)
            support_levels = recent_lows.nsmallest(3).tolist()
            
            current_price = df['close'].iloc[-1]
            
            return {
                "resistance": {
                    "levels": resistance_levels,
                    "nearest": min([r for r in resistance_levels if r > current_price], default=None)
                },
                "support": {
                    "levels": support_levels,
                    "nearest": max([s for s in support_levels if s < current_price], default=None)
                },
                "current_price": current_price
            }
            
        except Exception as e:
            logger.error(f"Support/resistance analysis error: {str(e)}")
            return {"support": None, "resistance": None}
    
    async def _get_fundamental_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Get fundamental analysis"""
        try:
            fundamental_data = {}
            
            for symbol in symbols:
                # Simulate fundamental analysis
                # In a real implementation, this would integrate with fundamental data providers
                fundamental_data[symbol] = {
                    "open_interest": np.random.randint(100000, 1000000),
                    "volume_profile": {
                        "high_volume_nodes": np.random.uniform(0.8, 1.2),
                        "low_volume_nodes": np.random.uniform(0.3, 0.7)
                    },
                    "commitment_of_traders": {
                        "commercial_long": np.random.uniform(0.3, 0.7),
                        "commercial_short": np.random.uniform(0.2, 0.6),
                        "non_commercial_long": np.random.uniform(0.2, 0.5),
                        "non_commercial_short": np.random.uniform(0.1, 0.4)
                    },
                    "economic_indicators": {
                        "inflation_impact": np.random.uniform(-0.5, 0.5),
                        "interest_rate_sensitivity": np.random.uniform(0.5, 1.5),
                        "economic_growth_correlation": np.random.uniform(0.3, 0.8)
                    },
                    "sector_rotation": {
                        "sector_strength": np.random.uniform(0.2, 0.9),
                        "rotation_trend": np.random.choice(["in", "out", "neutral"])
                    }
                }
            
            return {
                "symbol_fundamentals": fundamental_data,
                "market_fundamentals": {
                    "overall_sentiment": "neutral",
                    "economic_outlook": "stable",
                    "sector_rotation": "mixed"
                }
            }
            
        except Exception as e:
            logger.error(f"Fundamental analysis error: {str(e)}")
            return {}
    
    async def _get_risk_assessment(self, symbols: List[str]) -> Dict[str, Any]:
        """Get risk assessment for symbols"""
        try:
            risk_data = {}
            
            for symbol in symbols:
                # Simulate risk assessment
                risk_data[symbol] = {
                    "volatility_regime": np.random.choice(["low", "normal", "high"], p=[0.2, 0.6, 0.2]),
                    "liquidity_risk": np.random.uniform(0.1, 0.8),
                    "correlation_risk": np.random.uniform(0.3, 0.9),
                    "regulatory_risk": np.random.uniform(0.1, 0.6),
                    "geopolitical_risk": np.random.uniform(0.2, 0.7),
                    "overall_risk_score": np.random.uniform(0.2, 0.8)
                }
            
            # Market-wide risk factors
            market_risk = {
                "volatility_regime": "normal",
                "liquidity_conditions": "adequate",
                "correlation_breakdown_risk": np.random.uniform(0.1, 0.5),
                "systemic_risk": np.random.uniform(0.1, 0.4),
                "regulatory_environment": "stable",
                "geopolitical_tensions": "moderate"
            }
            
            return {
                "symbol_risks": risk_data,
                "market_risk": market_risk,
                "overall_risk_level": "medium"
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {str(e)}")
            return {}
    
    async def _get_market_regime_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Analyze current market regime"""
        try:
            # Simulate market regime analysis
            regime_indicators = {
                "volatility_regime": np.random.choice(["low", "normal", "high"], p=[0.3, 0.5, 0.2]),
                "trend_regime": np.random.choice(["trending", "ranging", "transitional"], p=[0.4, 0.4, 0.2]),
                "momentum_regime": np.random.choice(["strong", "weak", "neutral"], p=[0.3, 0.3, 0.4]),
                "correlation_regime": np.random.choice(["high", "low", "mixed"], p=[0.4, 0.3, 0.3])
            }
            
            # Determine overall regime
            regime_scores = {
                "trending": 0.6 if regime_indicators["trend_regime"] == "trending" else 0.2,
                "mean_reverting": 0.6 if regime_indicators["trend_regime"] == "ranging" else 0.2,
                "momentum": 0.6 if regime_indicators["momentum_regime"] == "strong" else 0.2,
                "volatility": 0.6 if regime_indicators["volatility_regime"] == "high" else 0.2
            }
            
            dominant_regime = max(regime_scores, key=regime_scores.get)
            
            return {
                "regime_indicators": regime_indicators,
                "dominant_regime": dominant_regime,
                "regime_confidence": regime_scores[dominant_regime],
                "regime_stability": np.random.uniform(0.6, 0.9),
                "regime_duration": np.random.randint(30, 180)  # days
            }
            
        except Exception as e:
            logger.error(f"Market regime analysis error: {str(e)}")
            return {}
    
    async def _get_correlation_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Analyze correlations between symbols"""
        try:
            if len(symbols) < 2:
                return {"correlation_matrix": {}, "correlation_insights": []}
            
            # Generate simulated correlation matrix
            n_symbols = len(symbols)
            correlation_matrix = np.random.uniform(-0.3, 0.8, (n_symbols, n_symbols))
            
            # Make it symmetric and set diagonal to 1
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix, 1.0)
            
            # Convert to dictionary
            correlation_dict = {}
            for i, symbol1 in enumerate(symbols):
                correlation_dict[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    correlation_dict[symbol1][symbol2] = float(correlation_matrix[i, j])
            
            # Find high correlations
            high_correlations = []
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i < j and abs(correlation_matrix[i, j]) > 0.7:
                        high_correlations.append({
                            "symbols": [symbol1, symbol2],
                            "correlation": float(correlation_matrix[i, j]),
                            "strength": "strong" if abs(correlation_matrix[i, j]) > 0.8 else "moderate"
                        })
            
            return {
                "correlation_matrix": correlation_dict,
                "high_correlations": high_correlations,
                "average_correlation": float(np.mean(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])),
                "correlation_stability": np.random.uniform(0.7, 0.95)
            }
            
        except Exception as e:
            logger.error(f"Correlation analysis error: {str(e)}")
            return {}
    
    async def _get_volatility_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Analyze volatility patterns"""
        try:
            volatility_data = {}
            
            for symbol in symbols:
                # Simulate volatility analysis
                volatility_data[symbol] = {
                    "current_volatility": np.random.uniform(0.1, 0.4),
                    "volatility_percentile": np.random.uniform(0.2, 0.9),
                    "volatility_trend": np.random.choice(["increasing", "decreasing", "stable"], p=[0.3, 0.3, 0.4]),
                    "volatility_regime": np.random.choice(["low", "normal", "high"], p=[0.2, 0.6, 0.2]),
                    "volatility_clustering": np.random.uniform(0.3, 0.8),
                    "volatility_forecast": np.random.uniform(0.1, 0.5)
                }
            
            # Market-wide volatility
            market_volatility = {
                "average_volatility": np.mean([data["current_volatility"] for data in volatility_data.values()]),
                "volatility_regime": "normal",
                "volatility_risk": "medium",
                "volatility_forecast": "stable"
            }
            
            return {
                "symbol_volatility": volatility_data,
                "market_volatility": market_volatility
            }
            
        except Exception as e:
            logger.error(f"Volatility analysis error: {str(e)}")
            return {}
    
    async def _calculate_overall_score(self, intelligence: Dict[str, Any]) -> float:
        """Calculate overall intelligence score"""
        try:
            scores = []
            
            # Sentiment score
            if "sentiment_analysis" in intelligence and intelligence["sentiment_analysis"]:
                sentiment_score = intelligence["sentiment_analysis"].get("overall_market_sentiment", {}).get("strength", 0.5)
                scores.append(sentiment_score)
            
            # Technical score
            if "technical_analysis" in intelligence and intelligence["technical_analysis"]:
                technical_score = intelligence["technical_analysis"].get("market_technical_score", 0.5)
                scores.append(technical_score)
            
            # Risk score (inverted - lower risk is better)
            if "risk_assessment" in intelligence and intelligence["risk_assessment"]:
                risk_score = 1 - intelligence["risk_assessment"].get("overall_risk_level", 0.5)
                scores.append(risk_score)
            
            # Regime score
            if "market_regime" in intelligence and intelligence["market_regime"]:
                regime_score = intelligence["market_regime"].get("regime_confidence", 0.5)
                scores.append(regime_score)
            
            return np.mean(scores) if scores else 0.5
            
        except Exception as e:
            logger.error(f"Overall score calculation error: {str(e)}")
            return 0.5
    
    async def _generate_intelligence_recommendations(self, intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligence-based recommendations"""
        try:
            recommendations = []
            
            # Sentiment-based recommendations
            if "sentiment_analysis" in intelligence:
                sentiment = intelligence["sentiment_analysis"].get("overall_market_sentiment", {})
                if sentiment.get("score", 0) > 0.3:
                    recommendations.append({
                        "type": "sentiment",
                        "priority": "medium",
                        "message": "Positive market sentiment detected - consider momentum strategies",
                        "action": "Increase exposure to trending assets"
                    })
                elif sentiment.get("score", 0) < -0.3:
                    recommendations.append({
                        "type": "sentiment",
                        "priority": "high",
                        "message": "Negative market sentiment detected - consider defensive strategies",
                        "action": "Reduce risk exposure and consider hedging"
                    })
            
            # Technical-based recommendations
            if "technical_analysis" in intelligence:
                technical_score = intelligence["technical_analysis"].get("market_technical_score", 0.5)
                if technical_score > 0.7:
                    recommendations.append({
                        "type": "technical",
                        "priority": "medium",
                        "message": "Strong technical signals detected",
                        "action": "Consider trend-following strategies"
                    })
                elif technical_score < 0.3:
                    recommendations.append({
                        "type": "technical",
                        "priority": "medium",
                        "message": "Weak technical signals detected",
                        "action": "Consider mean-reversion strategies"
                    })
            
            # Risk-based recommendations
            if "risk_assessment" in intelligence:
                risk_level = intelligence["risk_assessment"].get("overall_risk_level", "medium")
                if risk_level == "high":
                    recommendations.append({
                        "type": "risk",
                        "priority": "high",
                        "message": "High risk environment detected",
                        "action": "Reduce position sizes and increase diversification"
                    })
            
            # Regime-based recommendations
            if "market_regime" in intelligence:
                regime = intelligence["market_regime"].get("dominant_regime", "unknown")
                if regime == "trending":
                    recommendations.append({
                        "type": "regime",
                        "priority": "medium",
                        "message": "Trending market regime detected",
                        "action": "Focus on trend-following and momentum strategies"
                    })
                elif regime == "mean_reverting":
                    recommendations.append({
                        "type": "regime",
                        "priority": "medium",
                        "message": "Mean-reverting market regime detected",
                        "action": "Focus on contrarian and mean-reversion strategies"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendations generation error: {str(e)}")
            return []
