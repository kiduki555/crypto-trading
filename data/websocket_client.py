import json
import websockets
import asyncio
import logging
from typing import Callable, Dict, Any
from datetime import datetime

class BinanceWebSocket:
    def __init__(self, symbol: str, interval: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Binance WebSocket 클라이언트
        
        Args:
            symbol: 거래 심볼 (소문자, 예: 'btcusdt')
            interval: 캔들스틱 간격 (1m, 5m, 15m, 1h 등)
            callback: 데이터 수신시 호출할 콜백 함수
        """
        self.symbol = symbol.lower()
        self.interval = interval
        self.callback = callback
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{interval}"
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        
    async def connect(self):
        """WebSocket 연결 및 데이터 수신"""
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.is_connected = True
                    self.logger.info(f"Connected to Binance WebSocket for {self.symbol}")
                    
                    while True:
                        message = await websocket.recv()
                        await self._handle_message(message)
                        
            except websockets.ConnectionClosed:
                self.logger.warning("WebSocket connection closed, reconnecting...")
                self.is_connected = False
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"WebSocket error: {str(e)}")
                self.is_connected = False
                await asyncio.sleep(5)
    
    async def _handle_message(self, message: str):
        """수신된 메시지 처리"""
        try:
            data = json.loads(message)
            kline = data['k']
            
            market_data = {
                'symbol': self.symbol,
                'timestamp': kline['t'],
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
                'is_closed': kline['x']
            }
            
            # 캔들이 완성된 경우에만 콜백 호출
            if market_data['is_closed']:
                self.callback(market_data)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            
    def start(self):
        """WebSocket 연결 시작"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect()) 