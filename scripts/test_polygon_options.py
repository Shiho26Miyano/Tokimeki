"""
Test script for Polygon Options API using massive library
Tests the RESTClient and prints payload/results
"""
import os
import json
from massive import RESTClient

# Get API key from environment or use hardcoded for testing
API_KEY = os.getenv("POLYGON_API_KEY", "O6Ozj21f8GTPQyXlFFrnRAcK1A50QpXs")

def test_list_options_contracts():
    """Test listing options contracts"""
    print("=" * 80)
    print("Testing Polygon Options API - list_options_contracts")
    print("=" * 80)
    
    client = RESTClient(API_KEY)
    
    # Test with AAPL
    symbol = "AAPL"
    print(f"\nFetching options contracts for {symbol}...")
    print("-" * 80)
    
    contracts = []
    try:
        for contract in client.list_options_contracts(
            underlying_ticker=symbol,
            expired="false",
            limit=10,
            order="asc",
            sort="ticker",
        ):
            contracts.append(contract)
            
            # Print first contract details
            if len(contracts) == 1:
                print("\nFirst contract payload:")
                # Try different ways to convert to dict
                try:
                    contract_dict = vars(contract)
                except:
                    try:
                        contract_dict = contract.__dict__
                    except:
                        contract_dict = {attr: getattr(contract, attr) for attr in dir(contract) if not attr.startswith('_')}
                print(json.dumps(contract_dict, indent=2, default=str))
                print("-" * 80)
    
        print(f"\nTotal contracts fetched: {len(contracts)}")
        
        if contracts:
            print("\nSample contract fields:")
            contract = contracts[0]
            # Get all attributes
            attrs = [attr for attr in dir(contract) if not attr.startswith('_')]
            for attr in attrs:
                try:
                    value = getattr(contract, attr)
                    if not callable(value):
                        print(f"  {attr}: {value} ({type(value).__name__})")
                except:
                    pass
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with different parameters
    print("\n" + "=" * 80)
    print("Testing with filters (expiration, contract type, strike range)...")
    print("-" * 80)
    
    try:
        filtered_contracts = []
        for contract in client.list_options_contracts(
            underlying_ticker=symbol,
            expired="false",
            limit=5,
            sort="expiration_date",
            order="asc",
        ):
            filtered_contracts.append(contract)
            if len(filtered_contracts) <= 3:
                print(f"\nContract {len(filtered_contracts)}:")
                try:
                    contract_dict = vars(contract)
                except:
                    contract_dict = {attr: getattr(contract, attr) for attr in dir(contract) if not attr.startswith('_') and not callable(getattr(contract, attr, None))}
                print(json.dumps(contract_dict, indent=2, default=str))
        
        print(f"\nFiltered contracts: {len(filtered_contracts)}")
        
    except Exception as e:
        print(f"\nError in filtered test: {e}")
        import traceback
        traceback.print_exc()


def test_get_spot_price():
    """Test getting spot price using RESTClient"""
    print("\n" + "=" * 80)
    print("Testing Polygon API - get last trade (spot price)")
    print("=" * 80)
    
    client = RESTClient(API_KEY)
    symbol = "AAPL"
    
    try:
        print(f"\nGetting last trade for {symbol}...")
        last_trade = client.get_last_trade(symbol)
        
        print("\nLast trade payload:")
        try:
            trade_dict = vars(last_trade)
        except:
            trade_dict = {attr: getattr(last_trade, attr) for attr in dir(last_trade) if not attr.startswith('_') and not callable(getattr(last_trade, attr, None))}
        print(json.dumps(trade_dict, indent=2, default=str))
        
        # Try to extract price
        if hasattr(last_trade, 'price'):
            print(f"\nPrice: ${last_trade.price}")
        elif hasattr(last_trade, 'p'):
            print(f"\nPrice: ${last_trade.p}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def test_aggregates():
    """Test getting aggregates (for OI data)"""
    print("\n" + "=" * 80)
    print("Testing Polygon API - get aggregates (OI data)")
    print("=" * 80)
    
    client = RESTClient(API_KEY)
    
    # Get a sample option ticker from contracts
    symbol = "AAPL"
    
    try:
        print(f"\nGetting option ticker from contracts...")
        contracts = []
        for contract in client.list_options_contracts(
            underlying_ticker=symbol,
            expired="false",
            limit=1,
        ):
            contracts.append(contract)
            break
        
        if contracts:
            option_ticker = contracts[0].ticker
            print(f"\nTesting aggregates for option ticker: {option_ticker}")
            
            # Test get_aggs with recent dates
            from datetime import date, timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=5)
            
            print(f"\nFetching aggregates from {start_date} to {end_date}...")
            aggs = client.get_aggs(
                ticker=option_ticker,
                multiplier=1,
                timespan="day",
                from_=start_date.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d"),
            )
            
            print(f"\nAggregates payload (first 3 results):")
            count = 0
            for agg in aggs:
                if count >= 3:
                    break
                try:
                    agg_dict = vars(agg)
                except:
                    agg_dict = {attr: getattr(agg, attr) for attr in dir(agg) if not attr.startswith('_') and not callable(getattr(agg, attr, None))}
                print(f"\nAggregate {count + 1}:")
                print(json.dumps(agg_dict, indent=2, default=str))
                count += 1
                
        else:
            print("\nNo contracts found to test aggregates")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nPolygon Options API Test Script")
    print("=" * 80)
    print(f"API Key: {API_KEY[:10]}... (length: {len(API_KEY)})")
    
    # Test 1: List options contracts
    test_list_options_contracts()
    
    # Test 2: Get spot price (if method exists)
    test_get_spot_price()
    
    # Test 3: Aggregates (if method exists)
    test_aggregates()
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)

