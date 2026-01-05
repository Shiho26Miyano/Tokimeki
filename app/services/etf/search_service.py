"""
ETF Search Service
Service for searching and discovering ETFs using external APIs
"""
import os
import logging
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ETFSearchService:
    """Service for searching ETFs"""
    
    def __init__(self):
        # Check if we have Massive API key (optional)
        self.massive_api_key = os.getenv("MASSIVE_API_KEY")
        self.massive_base_url = "https://api.massive.com"
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def search_etfs_massive(
        self,
        search: str = "",
        type: str = "ETF",  # Filter for ETF type
        market: str = "stocks",
        active: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search ETFs using Massive API
        
        Args:
            search: Search term for ticker or company name
            type: Ticker type (default: ETF)
            market: Market type (default: stocks)
            active: Only active tickers (default: True)
            limit: Maximum results (default: 50)
            
        Returns:
            List of ETF tickers matching the search
        """
        if not self.massive_api_key:
            logger.debug("MASSIVE_API_KEY not set, skipping Massive API search")
            return []
        
        try:
            client = await self._get_client()
            url = f"{self.massive_base_url}/v3/reference/tickers"
            
            params = {
                "type": type,
                "market": market,
                "active": str(active).lower(),
                "limit": limit,
                "order": "asc",
                "sort": "ticker"
            }
            
            if search:
                params["search"] = search
            
            headers = {}
            if self.massive_api_key:
                headers["Authorization"] = f"Bearer {self.massive_api_key}"
            
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            logger.info(f"Found {len(results)} ETFs from Massive API for search: {search}")
            return results
            
        except Exception as e:
            logger.warning(f"Error searching ETFs via Massive API: {str(e)}")
            return []
    
    async def search_etfs_yfinance(self, query: str) -> List[Dict[str, Any]]:
        """
        Search ETFs using yfinance (fallback method)
        This is a simple search based on common ETF symbols
        
        Args:
            query: Search query
            
        Returns:
            List of ETF symbols matching the query
        """
        # Common ETF symbols for quick search
        common_etfs = [
            {"ticker": "SPY", "name": "SPDR S&P 500 ETF Trust", "type": "ETF"},
            {"ticker": "QQQ", "name": "Invesco QQQ Trust", "type": "ETF"},
            {"ticker": "VOO", "name": "Vanguard S&P 500 ETF", "type": "ETF"},
            {"ticker": "VTI", "name": "Vanguard Total Stock Market ETF", "type": "ETF"},
            {"ticker": "IWM", "name": "iShares Russell 2000 ETF", "type": "ETF"},
            {"ticker": "DIA", "name": "SPDR Dow Jones Industrial Average ETF", "type": "ETF"},
            {"ticker": "EEM", "name": "iShares MSCI Emerging Markets ETF", "type": "ETF"},
            {"ticker": "EFA", "name": "iShares MSCI EAFE ETF", "type": "ETF"},
            {"ticker": "GLD", "name": "SPDR Gold Trust", "type": "ETF"},
            {"ticker": "SLV", "name": "iShares Silver Trust", "type": "ETF"},
            {"ticker": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "type": "ETF"},
            {"ticker": "HYG", "name": "iShares iBoxx $ High Yield Corporate Bond ETF", "type": "ETF"},
            {"ticker": "XLF", "name": "Financial Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLE", "name": "Energy Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLK", "name": "Technology Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLV", "name": "Health Care Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLI", "name": "Industrial Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLP", "name": "Consumer Staples Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLY", "name": "Consumer Discretionary Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLB", "name": "Materials Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLU", "name": "Utilities Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "XLRE", "name": "Real Estate Select Sector SPDR Fund", "type": "ETF"},
            {"ticker": "ARKK", "name": "ARK Innovation ETF", "type": "ETF"},
            {"ticker": "ARKQ", "name": "ARK Autonomous Technology & Robotics ETF", "type": "ETF"},
            {"ticker": "ARKW", "name": "ARK Next Generation Internet ETF", "type": "ETF"},
            {"ticker": "ARKG", "name": "ARK Genomic Revolution ETF", "type": "ETF"},
            {"ticker": "ARKF", "name": "ARK Fintech Innovation ETF", "type": "ETF"},
            {"ticker": "VEA", "name": "Vanguard FTSE Developed Markets ETF", "type": "ETF"},
            {"ticker": "VWO", "name": "Vanguard FTSE Emerging Markets ETF", "type": "ETF"},
            {"ticker": "BND", "name": "Vanguard Total Bond Market ETF", "type": "ETF"},
        ]
        
        if not query:
            return common_etfs[:limit] if limit else common_etfs
        
        query_lower = query.lower()
        results = []
        
        for etf in common_etfs:
            if (query_lower in etf["ticker"].lower() or 
                query_lower in etf["name"].lower()):
                results.append(etf)
        
        return results[:limit] if limit else results
    
    async def search_etfs(
        self,
        query: str = "",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search ETFs using available APIs
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of ETF search results
        """
        # Try Massive API first if available
        if self.massive_api_key:
            results = await self.search_etfs_massive(
                search=query,
                type="ETF",
                limit=limit
            )
            if results:
                # Format results
                formatted = []
                for result in results:
                    formatted.append({
                        "ticker": result.get("ticker", ""),
                        "name": result.get("name", ""),
                        "type": result.get("type", "ETF"),
                        "market": result.get("market", "stocks"),
                        "active": result.get("active", True),
                        "primary_exchange": result.get("primary_exchange", ""),
                        "currency": result.get("currency_symbol", "USD")
                    })
                return formatted
        
        # Fallback to yfinance common ETFs
        return await self.search_etfs_yfinance(query)
    
    async def get_popular_etfs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of popular ETFs"""
        return await self.search_etfs_yfinance("")
    
    async def close(self):
        """Close HTTP client"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()

