import json
import asyncio
import logging
from typing import Dict, Optional, Callable
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class BinanceWebSocketClient:
    def __init__(self):
        """바이낸스 WebSocket 클라이언트 초기화"""
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.callbacks: Dict[str, Callable] = {}
        self.reconnect_delay = 1  # 초기 재연결 대기 시간
        self.max_reconnect_delay = 60  # 최대 재연결 대기 시간
        self.reconnect_attempt = 0
        self.max_reconnect_attempts = 5

    async def connect(self, symbol: str, channels: list[str]):
        """
        WebSocket 연결 및 구독

        Args:
            symbol: 거래쌍 (예: 'btcusdt')
            channels: 구독할 채널 목록 (예: ['kline_1m', 'trade'])
        """
        streams = [f"{symbol}@{channel}" for channel in channels]
        url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"

        while True:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    self.is_connected = True
                    self.reconnect_delay = 1
                    self.reconnect_attempt = 0
                    logger.info(f"Connected to Binance WebSocket: {url}")
                    
                    while True:
                        try:
                            message = await ws.recv()
                            await self._handle_message(json.loads(message))
                        except ConnectionClosed:
                            break

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                if not await self._should_reconnect():
                    break
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    async def _should_reconnect(self) -> bool:
        """재연결 시도 여부 결정"""
        self.reconnect_attempt += 1
        if self.reconnect_attempt > self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False
        return True

    async def _handle_message(self, message: Dict):
        """
        WebSocket 메시지 처리

        Args:
            message: 수신된 메시지
        """
        try:
            event_type = message.get('e')
            if event_type and event_type in self.callbacks:
                await self.callbacks[event_type](message)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def add_callback(self, event_type: str, callback: Callable):
        """
        이벤트 타입별 콜백 함수 등록

        Args:
            event_type: 이벤트 타입 (예: 'kline', 'trade')
            callback: 콜백 함수
        """
        self.callbacks[event_type] = callback

    async def close(self):
        """WebSocket 연결 종료"""
        if self.ws:
            await self.ws.close()
            self.is_connected = False 