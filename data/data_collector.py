import websocket
import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import threading
import time

class DataCollector:
    def __init__(self, 
                 exchange: str,
                 symbol: str,
                 interval: str = '1m',
                 callback: Optional[Callable] = None):
        """
        실시간 데이터 수집기 초기화
        
        Args:
            exchange: 거래소 이름 ('binance', 'bybit')
            symbol: 거래 심볼 (예: 'BTCUSDT')
            interval: 캔들 간격
            callback: 데이터 수신시 실행할 콜백 함수
        """
        self.exchange = exchange.lower()
        self.symbol = symbol.lower()
        self.interval = interval
        self.callback = callback
        self.ws = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        
        # 웹소켓 URL 설정
        if self.exchange == 'binance':
            self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{interval}"
        elif self.exchange == 'bybit':
            self.ws_url = f"wss://stream.bybit.com/realtime"
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

    def start(self):
        """웹소켓 연결 시작"""
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        # 별도 스레드에서 웹소켓 실행
        ws_thread = threading.Thread(target=self._run_websocket)
        ws_thread.daemon = True
        ws_thread.start()

    def stop(self):
        """웹소켓 연결 종료"""
        if self.ws:
            self.ws.close()
        self.is_connected = False

    def _run_websocket(self):
        """웹소켓 연결 유지 및 재연결 처리"""
        while True:
            try:
                self.ws.run_forever()
                if not self.is_connected:
                    break
                self.logger.info("Reconnecting websocket...")
                time.sleep(3)  # 재연결 전 대기
            except Exception as e:
                self.logger.error(f"Websocket error: {str(e)}")
                time.sleep(3)

    def _on_message(self, ws, message):
        """
        웹소켓 메시지 수신 처리
        
        Args:
            ws: 웹소켓 객체
            message: 수신된 메시지
        """
        try:
            data = json.loads(message)
            processed_data = self._process_data(data)
            
            if processed_data and self.callback:
                self.callback(processed_data)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    def _process_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        수신된 데이터 처리
        
        Args:
            raw_data: 원시 데이터
        Returns:
            처리된 데이터
        """
        try:
            if self.exchange == 'binance':
                kline = raw_data['k']
                return {
                    'timestamp': kline['t'],
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v']),
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'is_closed': kline['x']
                }
            elif self.exchange == 'bybit':
                # Bybit 데이터 처리 로직 구현
                pass
                
        except Exception as e:
            self.logger.error(f"Error in data processing: {str(e)}")
            return None

    def _on_error(self, ws, error):
        """웹소켓 에러 처리"""
        self.logger.error(f"Websocket error: {str(error)}")

    def _on_close(self, ws, close_status_code, close_msg):
        """웹소켓 연결 종료 처리"""
        self.logger.info("Websocket connection closed")
        self.is_connected = False

    def _on_open(self, ws):
        """웹소켓 연결 시작 처리"""
        self.logger.info("Websocket connection opened")
        self.is_connected = True
        
        # Bybit의 경우 구독 메시지 전송
        if self.exchange == 'bybit':
            subscribe_message = {
                "op": "subscribe",
                "args": [f"klineV2.{self.interval}.{self.symbol}"]
            }
            ws.send(json.dumps(subscribe_message))
