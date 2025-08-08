from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetAssetsRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

class AlpacaClient:
    def __init__(self):
        self.api_key = "YOUR_ALPACA_API_KEY"
        self.api_secret = "YOUR_ALPACA_SECRET"
        self.base_url = "https://paper-api.alpaca.markets"
        self.trading_client = None
        self.data_client = None
    
    async def initialize(self):
        """Initialize Alpaca clients"""
        self.trading_client = TradingClient(
            api_key=self.api_key,
            secret_key=self.api_secret,
            paper=True
        )
        self.data_client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.api_secret
        )
    
    async def get_account(self):
        """Get account information"""
        return self.trading_client.get_account()
    
    async def get_positions(self):
        """Get current positions"""
        return self.trading_client.get_all_positions()
    
    async def get_tradeable_assets(self) -> List[Dict]:
        """Get all tradeable assets"""
        request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        assets = self.trading_client.get_all_assets(request)
        
        return [
            {
                "symbol": asset.symbol,
                "name": asset.name,
                "tradable": asset.tradable,
                "shortable": asset.shortable,
                "easy_to_borrow": asset.easy_to_borrow
            }
            for asset in assets if asset.tradable
        ]
    
    async def place_order(self, symbol: str, qty: float, side: str, 
                         type: str = "market", time_in_force: str = "day"):
        """Place an order"""
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        
        return self.trading_client.submit_order(order_data=market_order_data)
    
    async def get_stock_bars(self, symbols: List[str], timeframe: str = "1Day", 
                           days_back: int = 30) -> Dict:
        """Get historical stock data"""
        request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=days_back)
        )
        
        bars = self.data_client.get_stock_bars(request_params)
        return bars.dict()