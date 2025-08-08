from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import json

# Import our custom modules
from database import DatabaseManager
from alpaca_client import AlpacaClient
from stock_filter import StockFilter
from trading_strategies import TradingStrategy

app = FastAPI(title="Algorithmic Trading System", version="1.0.0")

# Initialize components
db_manager = DatabaseManager()
alpaca_client = AlpacaClient()
stock_filter = StockFilter(alpaca_client)
trading_strategy = TradingStrategy(alpaca_client, db_manager)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_startup
async def startup_event():
    """Initialize database and connections on startup"""
    await db_manager.initialize()
    await alpaca_client.initialize()
    print("🚀 Trading System Started Successfully!")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    with open("static/index.html", "r") as file:
        return HTMLResponse(content=file.read())

@app.get("/api/account")
async def get_account_info():
    """Get Alpaca account information"""
    try:
        account = await alpaca_client.get_account()
        return {
            "account_number": account.account_number,
            "buying_power": float(account.buying_power),
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "status": account.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    try:
        positions = await alpaca_client.get_positions()
        return [
            {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": pos.side,
                "market_value": float(pos.market_value),
                "unrealized_pl": float(pos.unrealized_pl),
                "unrealized_plpc": float(pos.unrealized_plpc)
            }
            for pos in positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filter-stocks")
async def filter_stocks(filter_params: dict):
    """Filter stocks based on criteria"""
    try:
        filtered_stocks = await stock_filter.filter_stocks(
            min_price=filter_params.get('min_price', 1.0),
            max_price=filter_params.get('max_price', 500.0),
            min_volume=filter_params.get('min_volume', 100000),
            min_market_cap=filter_params.get('min_market_cap', 100000000),
            sector=filter_params.get('sector'),
            limit=filter_params.get('limit', 50)
        )
        return {"stocks": filtered_stocks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-strategy")
async def execute_strategy(strategy_params: dict):
    """Execute a trading strategy"""
    try:
        result = await trading_strategy.execute_strategy(
            strategy_name=strategy_params.get('strategy_name'),
            symbols=strategy_params.get('symbols', []),
            parameters=strategy_params.get('parameters', {})
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades")
async def get_trades(limit: int = 100):
    """Get recent trades from database"""
    try:
        trades = await db_manager.get_recent_trades(limit)
        return {"trades": trades}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/place-order")
async def place_order(order_params: dict):
    """Place a manual order"""
    try:
        order = await alpaca_client.place_order(
            symbol=order_params['symbol'],
            qty=order_params['qty'],
            side=order_params['side'],
            type=order_params.get('type', 'market'),
            time_in_force=order_params.get('time_in_force', 'day')
        )
        
        # Log order to database
        await db_manager.log_trade(
            symbol=order_params['symbol'],
            side=order_params['side'],
            qty=order_params['qty'],
            order_id=order.id,
            strategy_name="manual"
        )
        
        return {"order_id": order.id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)