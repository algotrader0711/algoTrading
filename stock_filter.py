from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

class StockFilter:
    def __init__(self, alpaca_client):
        self.alpaca_client = alpaca_client
    
    async def filter_stocks(self, min_price: float = 1.0, max_price: float = 500.0,
                          min_volume: int = 100000, min_market_cap: int = None,
                          sector: str = None, limit: int = 50) -> List[Dict]:
        """Filter stocks based on various criteria"""
        
        # Get all tradeable assets
        assets = await self.alpaca_client.get_tradeable_assets()
        
        # Filter basic criteria
        filtered_assets = []
        for asset in assets[:200]:  # Limit API calls for demo
            try:
                # Get recent bar data for price and volume
                bars_data = await self.alpaca_client.get_stock_bars(
                    [asset['symbol']], days_back=5
                )
                
                if asset['symbol'] in bars_data and bars_data[asset['symbol']]:
                    latest_bar = bars_data[asset['symbol']][-1]
                    price = latest_bar['close']
                    volume = latest_bar['volume']
                    
                    # Apply filters
                    if (min_price <= price <= max_price and 
                        volume >= min_volume):
                        
                        filtered_assets.append({
                            'symbol': asset['symbol'],
                            'name': asset['name'],
                            'price': price,
                            'volume': volume,
                            'shortable': asset['shortable'],
                            'easy_to_borrow': asset['easy_to_borrow']
                        })
                        
                        if len(filtered_assets) >= limit:
                            break
                            
            except Exception as e:
                print(f"Error processing {asset['symbol']}: {e}")
                continue
        
        return filtered_assets