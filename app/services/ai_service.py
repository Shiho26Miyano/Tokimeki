import httpx
import asyncio
import logging
import re
import os
from typing import Dict, Any, List, Optional
from ..core.config import settings

# Define FREE_MODELS locally to avoid circular import issues
FREE_MODELS = {
    "mistral-small": "mistralai/mistral-small-3.2-24b-instruct:free",
    "deepseek-r1": "deepseek/deepseek-r1-0528:free",
    "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
    "llama-3.1-405b": "meta-llama/llama-3.1-405b-instruct:free"
}
from .cache_service import AsyncCacheService
from .stock_service import AsyncStockService

logger = logging.getLogger(__name__)

class AsyncAIService:
    def __init__(self, http_client: httpx.AsyncClient, cache_service: AsyncCacheService, stock_service: AsyncStockService = None):
        self.http_client = http_client
        self.cache_service = cache_service
        self.stock_service = stock_service
        
        # Try to get API key from settings first, then environment variable
        try:
            self.api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
            self.api_url = settings.openrouter_api_url
        except Exception as e:
            logger.warning(f"Error getting API settings: {e}")
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        logger.info(f"AI Service initialized with API key: {self.api_key[:20] + '...' if self.api_key else 'None'}")
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
    
    async def call_api(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "mistral-small", 
        temperature: float = 0.7, 
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Make async API call to OpenRouter"""
        
        logger.info(f"Calling API with key: {self.api_key[:20] + '...' if self.api_key else 'None'}")
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        if model not in FREE_MODELS:
            raise ValueError(f"Invalid model: {model}")
        
        # Generate cache key
        cache_key = f"ai_api:{model}:{hash(str(messages) + str(temperature) + str(max_tokens))}"
        
        # Check cache first
        cached_response = await self.cache_service.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for AI API call: {model}")
            return cached_response
        
        # Prepare request
        payload = {
            "model": FREE_MODELS[model],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Debug: Log the headers being sent
        logger.info(f"API Key being used: {self.api_key[:20] + '...' if self.api_key else 'None'}")
        logger.info(f"Authorization header: Bearer {self.api_key[:20] + '...' if self.api_key else 'None'}")
        logger.info(f"Full headers: {headers}")
        logger.info(f"Request URL: {self.api_url}")
        logger.info(f"Request payload: {payload}")
        
        try:
            logger.info(f"Making API call to {model}")
            response = await self.http_client.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60.0  # Increased from 30.0 to 60.0 seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache successful response
                await self.cache_service.set(cache_key, result, ttl=300)
                return result
            else:
                error_msg = f"API call failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except httpx.TimeoutException:
            error_msg = "API call timed out after 60 seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"API call error: {e}")
            raise
    
    async def compare_models(
        self, 
        prompt: str, 
        models: List[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800  # Increased from 500 for better responses
    ) -> List[Dict[str, Any]]:
        """Compare multiple models concurrently with optimizations"""
        
        try:
            if models is None:
                # Use fewer models for faster comparison
                models = ["mistral-small", "deepseek-chat"]
            
            # Validate models
            for model in models:
                if model not in FREE_MODELS:
                    logger.warning(f"Invalid model requested: {model}, using default")
                    models = ["mistral-small", "deepseek-chat"]
                    break
        except Exception as e:
            logger.error(f"Error in compare_models setup: {e}")
            # Fallback to safe defaults
            models = ["mistral-small"]
        
        # Generate cache key for the entire comparison
        comparison_cache_key = f"model_comparison:{hash(prompt + str(models) + str(temperature) + str(max_tokens))}"
        
        # Check if we have cached comparison results
        cached_comparison = await self.cache_service.get(comparison_cache_key)
        if cached_comparison:
            logger.info(f"Cache hit for model comparison")
            return cached_comparison
        
        # Create tasks for concurrent execution with optimized timeouts
        tasks = []
        for model in models:
            messages = [{"role": "user", "content": prompt}]
            # Use increased timeout for comparison calls
            task = self._call_api_optimized(messages, model, temperature, max_tokens, timeout=45.0)  # Increased from 25.0 to 45.0
            tasks.append(task)
        
        # Execute all tasks concurrently with increased timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=60.0  # Increased from 30.0 to 60.0 seconds
            )
        except asyncio.TimeoutError:
            logger.warning("Model comparison timed out after 60 seconds")
            return [{"model": model, "error": "Request timed out after 60 seconds", "success": False} for model in models]
        
        # Process results with timing
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "model": models[i],
                    "error": str(result),
                    "success": False,
                    "response_time": 0,
                    "token_count": 0,
                    "word_count": 0,
                    "avg_word_length": 0
                })
            else:
                # Extract response content and usage
                response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = result.get("usage", {})
                token_count = usage.get("total_tokens", 0)
                
                # Calculate word statistics
                words = response_content.split() if response_content else []
                word_count = len(words)
                avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
                
                # Estimate response time based on token count (rough approximation)
                estimated_response_time = 2.0 + (token_count / 100)  # Base 2s + 0.01s per token
                
                processed_results.append({
                    "model": models[i],
                    "response": response_content,
                    "usage": usage,
                    "success": True,
                    "response_time": estimated_response_time,
                    "token_count": token_count,
                    "word_count": word_count,
                    "avg_word_length": avg_word_length
                })
        
        # Cache the comparison results
        await self.cache_service.set(comparison_cache_key, processed_results, ttl=600)  # 10 minutes
        
        return processed_results
    
    async def _call_api_optimized(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "mistral-small", 
        temperature: float = 0.7, 
        max_tokens: int = 1000,
        timeout: float = 45.0  # Increased from 15.0 to 45.0 seconds
    ) -> Dict[str, Any]:
        """Optimized API call with increased timeout for comparisons"""
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        if model not in FREE_MODELS:
            raise ValueError(f"Invalid model: {model}")
        
        # Generate cache key
        cache_key = f"ai_api:{model}:{hash(str(messages) + str(temperature) + str(max_tokens))}"
        
        # Check cache first
        cached_response = await self.cache_service.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for AI API call: {model}")
            return cached_response
        
        # Prepare request
        payload = {
            "model": FREE_MODELS[model],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Making optimized API call to {model}")
            response = await self.http_client.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache successful response with shorter TTL for comparisons
                await self.cache_service.set(cache_key, result, ttl=180)  # 3 minutes for comparisons
                return result
            else:
                error_msg = f"API call failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except httpx.TimeoutException:
            error_msg = f"API call timed out for {model} after {timeout} seconds"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"API call error for {model}: {e}")
            raise
    
    async def chat(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        model: str = "mistral-small",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Chat with AI model"""
        
        # Build messages list
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        # Make API call
        result = await self.call_api(messages, model, temperature, max_tokens)
        
        # Extract response
        response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Update conversation history
        if conversation_history is None:
            conversation_history = []
        
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response_content})
        
        return {
            "response": response_content,
            "model": model,
            "usage": result.get("usage", {}),
            "conversation_history": conversation_history
        }
    
    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models"""
        return [
            {"id": model_id, "name": model_name} 
            for model_id, model_name in FREE_MODELS.items()
        ]
    
    def _extract_stock_symbol(self, message: str) -> Optional[str]:
        """Extract stock symbol from message"""
        message_upper = message.upper()
        
        # Company name to symbol mapping
        company_to_symbol = {
            'APPLE': 'AAPL',
            'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL',
            'ALPHABET': 'GOOGL',
            'AMAZON': 'AMZN',
            'TESLA': 'TSLA',
            'META': 'META',
            'FACEBOOK': 'META',
            'NVIDIA': 'NVDA',
            'NETFLIX': 'NFLX',
            'AMD': 'AMD',
            'INTEL': 'INTC',
            'BERKSHIRE': 'BRK-B',
            'JOHNSON': 'JNJ',
            'VISA': 'V',
            'JPMORGAN': 'JPM',
            'WALMART': 'WMT',
            'PROCTER': 'PG',
            'COCA': 'KO',
            'EXXON': 'XOM',
            'SPY': 'SPY',
            'QQQ': 'QQQ',
            'VOO': 'VOO',
            'ARKK': 'ARKK',
            'EEM': 'EEM',
            'XLF': 'XLF'
        }
        
        # First check for exact stock symbols (1-5 letters)
        stock_pattern = r'\b([A-Z]{1,5})\b'
        matches = re.findall(stock_pattern, message_upper)
        
        # Common stock symbols
        common_symbols = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
            'BRK-B', 'JNJ', 'V', 'JPM', 'WMT', 'PG', 'KO', 'XOM', 'SPY', 'QQQ', 'VOO',
            'ARKK', 'EEM', 'XLF', 'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'MES=F', 'MNQ=F',
            'MYM=F', 'M2K=F', 'GC=F', 'SI=F', 'CL=F', 'BZ=F', 'NG=F', 'HG=F', 'ZC=F',
            'ZS=F', 'ZW=F', 'VX=F', 'BTC=F', 'ETH=F'
        ]
        
        # Check for exact stock symbols first
        for match in matches:
            if match in common_symbols:
                return match
        
        # Check for company names
        for company_name, symbol in company_to_symbol.items():
            if company_name in message_upper:
                return symbol
        
        return None
    
    async def analyze_stock_performance(
        self, 
        symbol: str, 
        days: int = 365,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze stock performance using yfinance data"""
        
        if not self.stock_service:
            raise ValueError("Stock service not available")
        
        try:
            # Get stock data
            data = await self.stock_service.get_stock_data(symbol, days)
            if not data:
                return {
                    "success": False,
                    "error": f"No data available for {symbol}"
                }
            
            # Calculate performance metrics
            prices = [day['Close'] for day in data['data']]
            dates = [day['Date'] for day in data['data']]
            
            # Basic metrics
            start_price = prices[0]
            end_price = prices[-1]
            total_return = ((end_price / start_price) - 1) * 100
            
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
            
            # Risk metrics
            volatility = (sum(returns) / len(returns)) * 252 if returns else 0  # Annualized
            sharpe_ratio = (volatility / (sum(returns) / len(returns))) if volatility > 0 else 0
            
            # Maximum drawdown
            peak = prices[0]
            max_drawdown = 0
            drawdown_period = 0
            for i, price in enumerate(prices):
                if price > peak:
                    peak = price
                drawdown = (peak - price) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    drawdown_period = i
            
            # 7-day performance
            if len(prices) >= 7:
                week_return = ((prices[-1] / prices[-7]) - 1) * 100
            else:
                week_return = total_return
            
            # Recent performance (last 30 days)
            if len(prices) >= 30:
                month_return = ((prices[-1] / prices[-30]) - 1) * 100
            else:
                month_return = total_return
            
            # Price ranges
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            # Volume analysis
            volumes = [day['Volume'] for day in data['data']]
            avg_volume = sum(volumes) / len(volumes) if volumes else 0
            
            analysis_result = {
                "success": True,
                "symbol": symbol,
                "period_days": days,
                "metrics": {
                    "total_return_percent": round(total_return, 2),
                    "week_return_percent": round(week_return, 2),
                    "month_return_percent": round(month_return, 2),
                    "volatility": round(volatility * 100, 2),
                    "sharpe_ratio": round(sharpe_ratio, 2),
                    "max_drawdown_percent": round(max_drawdown * 100, 2),
                    "price_range": {
                        "min": round(min_price, 2),
                        "max": round(max_price, 2),
                        "avg": round(avg_price, 2),
                        "current": round(end_price, 2)
                    },
                    "volume_avg": int(avg_volume)
                },
                "summary": {
                    "risk_assessment": "High" if volatility > 0.3 else "Medium" if volatility > 0.15 else "Low",
                    "performance_rating": "Excellent" if total_return > 20 else "Good" if total_return > 10 else "Poor" if total_return < -10 else "Average",
                    "drawdown_severity": "Severe" if max_drawdown > 0.3 else "Moderate" if max_drawdown > 0.15 else "Mild"
                }
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Stock analysis error for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat_with_stock_analysis(
        self, 
        message: str, 
        model: str = "mistral-small",
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """Enhanced chat with comprehensive stock analysis capabilities"""
        
        # Extract stock symbol from message
        symbol = self._extract_stock_symbol(message)
        
        if symbol and self.stock_service:
            try:
                # Get comprehensive stock data
                comprehensive_data = await self.stock_service.get_comprehensive_stock_data(symbol)
                
                if comprehensive_data:
                    # Extract key data
                    company_info = comprehensive_data.get('company_info', {})
                    market_data = comprehensive_data.get('market_data', {})
                    historical_data = comprehensive_data.get('historical_data', {})
                    financial_data = comprehensive_data.get('financial_data', {})
                    analyst_data = comprehensive_data.get('analyst_data', {})
                    
                    # Create comprehensive analysis prompt
                    analysis_prompt = f"""
                    **COMPREHENSIVE STOCK ANALYSIS FOR {symbol.upper()}**

                    **Company Information:**
                    • Name: {company_info.get('name', 'N/A')}
                    • Sector: {company_info.get('sector', 'N/A')}
                    • Industry: {company_info.get('industry', 'N/A')}
                    • Employees: {company_info.get('employees', 'N/A'):,}
                    • Description: {company_info.get('description', 'N/A')[:200]}...

                    **Market Data:**
                    • Current Price: ${market_data.get('current_price', 0):.2f}
                    • Market Cap: ${market_data.get('market_cap', 0):,.0f}
                    • P/E Ratio: {market_data.get('pe_ratio', 0):.2f}
                    • Dividend Yield: {market_data.get('dividend_yield', 0):.2f}%
                    • Beta: {market_data.get('beta', 0):.2f}
                    • Volume: {market_data.get('volume', 0):,}

                    **Historical Performance (1 Year):**
                    • Start Price: ${historical_data.get('start_price', 0):.2f}
                    • End Price: ${historical_data.get('end_price', 0):.2f}
                    • Total Return: {historical_data.get('percent_change', 0):.2f}%
                    • Min Price: ${historical_data.get('min_price', 0):.2f}
                    • Max Price: ${historical_data.get('max_price', 0):.2f}
                    • Volatility: {historical_data.get('volatility', 0):.2f}%
                    • Total Volume: {historical_data.get('total_volume', 0):,}

                    **Financial Metrics:**
                    • Data Availability: {financial_data.get('available', 'N/A')}

                    **Analyst Sentiment:**
                    • Data Availability: {analyst_data.get('available', 'N/A')}

                    **User Question:** {message}

                    Please provide a comprehensive analysis with:
                    1. **Company Overview** - Business model and competitive position
                    2. **Market Performance** - Price trends, volatility, and returns
                    3. **Risk Assessment** - Market, sector, and company-specific risks
                    4. **Valuation Analysis** - P/E, growth prospects, and fair value
                    5. **Investment Recommendation** - Buy/Hold/Sell with reasoning
                    6. **Key Catalysts** - Upcoming events that could impact the stock

                    Note: Financial statements and analyst data require premium access. Focus on available market data and technical analysis.
                    Format your response with clear bullet points and actionable insights.
                    """
                    
                    # Get AI response
                    result = await self.call_api([{"role": "user", "content": analysis_prompt}], model, temperature, max_tokens)
                    
                    response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        "response": response_content,
                        "model": model,
                        "usage": result.get("usage", {}),
                        "stock_analysis": {
                            "symbol": symbol,
                            "company_name": company_info.get('name', ''),
                            "current_price": market_data.get('current_price', 0),
                            "market_cap": market_data.get('market_cap', 0),
                            "total_return": historical_data.get('percent_change', 0),
                            "volatility": historical_data.get('volatility', 0),
                            "pe_ratio": market_data.get('pe_ratio', 0),
                            "dividend_yield": market_data.get('dividend_yield', 0),
                            "beta": market_data.get('beta', 0),
                            "sector": company_info.get('sector', ''),
                            "industry": company_info.get('industry', ''),
                        },
                        "symbol_analyzed": symbol
                    }
                    
            except Exception as e:
                logger.error(f"Error in comprehensive stock analysis for {symbol}: {e}")
        
        # Fallback to regular chat
        return await self.chat(message, model=model, temperature=temperature, max_tokens=max_tokens)
    
    def _extract_revenue_growth(self, financial_data: Dict) -> str:
        """Extract revenue growth from financial data"""
        try:
            financials = financial_data.get('financials', {})
            if financials and 'Total Revenue' in financials:
                revenue_data = financials['Total Revenue']
                if len(revenue_data) >= 2:
                    recent_revenue = list(revenue_data.values())[0]
                    prev_revenue = list(revenue_data.values())[1]
                    growth = ((recent_revenue - prev_revenue) / prev_revenue) * 100
                    return f"{growth:.1f}%"
            return "N/A"
        except:
            return "N/A"
    
    def _extract_profit_margins(self, financial_data: Dict) -> str:
        """Extract profit margins from financial data"""
        try:
            financials = financial_data.get('financials', {})
            if financials and 'Net Income' in financials and 'Total Revenue' in financials:
                net_income = list(financials['Net Income'].values())[0]
                revenue = list(financials['Total Revenue'].values())[0]
                margin = (net_income / revenue) * 100
                return f"{margin:.1f}%"
            return "N/A"
        except:
            return "N/A"
    
    def _extract_debt_levels(self, financial_data: Dict) -> str:
        """Extract debt levels from financial data"""
        try:
            balance_sheet = financial_data.get('balance_sheet', {})
            if balance_sheet and 'Total Debt' in balance_sheet:
                debt = list(balance_sheet['Total Debt'].values())[0]
                return f"${debt:,.0f}"
            return "N/A"
        except:
            return "N/A"
    
    def _extract_recommendations(self, analyst_data: Dict) -> str:
        """Extract analyst recommendations"""
        try:
            recommendations = analyst_data.get('recommendations', {})
            if recommendations:
                recent_recs = list(recommendations.values())[-1] if recommendations else []
                if recent_recs:
                    buy_count = sum(1 for rec in recent_recs if 'Buy' in str(rec))
                    hold_count = sum(1 for rec in recent_recs if 'Hold' in str(rec))
                    sell_count = sum(1 for rec in recent_recs if 'Sell' in str(rec))
                    return f"Buy: {buy_count}, Hold: {hold_count}, Sell: {sell_count}"
            return "N/A"
        except:
            return "N/A"
    
    def _extract_price_targets(self, analyst_data: Dict) -> str:
        """Extract analyst price targets"""
        try:
            price_targets = analyst_data.get('price_targets', {})
            if price_targets:
                targets = list(price_targets.values())
                if targets:
                    avg_target = sum(targets) / len(targets)
                    return f"${avg_target:.2f}"
            return "N/A"
        except:
            return "N/A" 