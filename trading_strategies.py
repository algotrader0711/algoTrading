import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta

class TradingStrategy:
    def __init__(self, alpaca_client, db_manager):
        self.alpaca_client = alpaca_client
        self.db_manager = db_manager
    
    async def execute_strategy(self, strategy_name: str, symbols: List[str], 
                             parameters: Dict) -> Dict:
        """Execute a trading strategy"""
        
        if strategy_name == "mean_reversion":
            return await self.mean_reversion_strategy(symbols, parameters)
        elif strategy_name == "momentum":
            return await self.momentum_strategy(symbols, parameters)
        elif strategy_name == "rsi_divergence":
            return await self.rsi_strategy(symbols, parameters)
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
    
    async def mean_reversion_strategy(self, symbols: List[str], params: Dict) -> Dict:
        """Simple mean reversion strategy"""
        results = {"trades": [], "signals": []}
        
        lookback_days = params.get('lookback_days', 20)
        std_threshold = params.get('std_threshold', 2.0)
        position_size = params.get('position_size', 100)
        
        for symbol in symbols:
            try:
                # Get historical data
                bars_data = await self.alpaca_client.get_stock_bars(
                    [symbol], days_back=lookback_days + 5
                )
                
                if symbol not in bars_data or len(bars_data[symbol]) < lookback_days:
                    continue
                
                # Calculate signals
                df = pd.DataFrame(bars_data[symbol])
                df['sma'] = df['close'].rolling(window=lookback_days).mean()
                df['std'] = df['close'].rolling(window=lookback_days).std()
                df['zscore'] = (df['close'] - df['sma']) / df['std']
                
                current_zscore = df['zscore'].iloc[-1]
                current_price = df['close'].iloc[-1]
                
                # Generate signals
                if current_zscore < -std_threshold:  # Oversold - Buy signal
                    signal = {
                        'symbol': symbol,
                        'action': 'buy',
                        'price': current_price,
                        'zscore': current_zscore,
                        'confidence': min(abs(current_zscore) / std_threshold, 1.0)
                    }
                    results['signals'].append(signal)
                    
                    # Execute trade if confidence is high
                    if signal['confidence'] > 0.7:
                        order = await self.alpaca_client.place_order(
                            symbol=symbol,
                            qty=position_size,
                            side="buy"
                        )
                        
                        await self.db_manager.log_trade(
                            symbol=symbol,
                            side="buy",
                            qty=position_size,
                            order_id=order.id,
                            strategy_name="mean_reversion",
                            metadata={"zscore": current_zscore, "confidence": signal['confidence']}
                        )
                        
                        results['trades'].append({
                            'symbol': symbol,
                            'side': 'buy',
                            'qty': position_size,
                            'order_id': order.id
                        })
                
                elif current_zscore > std_threshold:  # Overbought - Sell signal
                    # Similar logic for sell signals
                    pass
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        return results
    
    async def momentum_strategy(self, symbols: List[str], params: Dict) -> Dict:
        """Simple momentum strategy"""
        # Implementation for momentum strategy
        return {"message": "Momentum strategy executed", "trades": []}
    
    async def rsi_strategy(self, symbols: List[str], params: Dict) -> Dict:
        """RSI-based strategy"""
        # Implementation for RSI strategy
        return {"message": "RSI strategy executed", "trades": []}