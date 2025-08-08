import asyncpg
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json

class DatabaseManager:
    def __init__(self):
        self.db_url = "postgresql://algotrader_user:tEoYIGyieB89Cg7kFCpAAISskaz1ViTM@dpg-d2auhqogjchc73ennud0-a.oregon-postgres.render.com/algotrader"
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool and create tables"""
        self.pool = await asyncpg.create_pool(self.db_url)
        await self.create_tables()
    
    async def create_tables(self):
        """Create necessary tables for the trading system"""
        async with self.pool.acquire() as conn:
            # Trades table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    symbol VARCHAR(10) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    qty DECIMAL(10,2) NOT NULL,
                    price DECIMAL(10,2),
                    order_id VARCHAR(50),
                    strategy_name VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'pending',
                    profit_loss DECIMAL(10,2),
                    metadata JSONB
                );
            """)
            
            # Stock data table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    price DECIMAL(10,2),
                    volume BIGINT,
                    market_cap BIGINT,
                    sector VARCHAR(100),
                    pe_ratio DECIMAL(10,2),
                    metadata JSONB
                );
            """)
            
            # Strategy performance table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id SERIAL PRIMARY KEY,
                    strategy_name VARCHAR(100) NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    total_pnl DECIMAL(10,2) DEFAULT 0,
                    win_rate DECIMAL(5,2),
                    metadata JSONB
                );
            """)
    
    async def log_trade(self, symbol: str, side: str, qty: float, 
                       order_id: str = None, strategy_name: str = None, 
                       price: float = None, metadata: dict = None):
        """Log a trade to the database"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO trades (symbol, side, qty, price, order_id, strategy_name, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, symbol, side, qty, price, order_id, strategy_name, json.dumps(metadata or {}))
    
    async def update_trade_status(self, order_id: str, status: str, price: float = None):
        """Update trade status and price"""
        async with self.pool.acquire() as conn:
            if price:
                await conn.execute("""
                    UPDATE trades SET status = $1, price = $2 
                    WHERE order_id = $3
                """, status, price, order_id)
            else:
                await conn.execute("""
                    UPDATE trades SET status = $1 WHERE order_id = $2
                """, status, order_id)
    
    async def get_recent_trades(self, limit: int = 100) -> List[Dict]:
        """Get recent trades from database"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM trades 
                ORDER BY timestamp DESC 
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def store_stock_data(self, symbol: str, price: float, volume: int, 
                             market_cap: int = None, sector: str = None, 
                             pe_ratio: float = None, metadata: dict = None):
        """Store stock data for analysis"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO stock_data (symbol, price, volume, market_cap, sector, pe_ratio, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, symbol, price, volume, market_cap, sector, pe_ratio, json.dumps(metadata or {}))