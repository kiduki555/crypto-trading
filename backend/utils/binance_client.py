import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        """바이낸스 API 클라이언트 초기화"""
        self.client = Client(
            os.getenv('BINANCE_API_KEY'),
            os.getenv('BINANCE_API_SECRET')
        )

    def get_historical_klines(self,
                            symbol: str,
                            interval: str,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> List[Dict]:
        """
        과거 K라인 데이터 조회

        Args:
            symbol: 거래쌍 (예: 'BTCUSDT')
            interval: 시간간격 (예: '1m', '5m', '1h', '1d')
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            K라인 데이터 리스트
        """
        try:
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None,
                end_str=end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None
            )
            
            return [{
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': k[6],
                'quote_volume': float(k[7]),
                'trades': int(k[8]),
                'taker_buy_base': float(k[9]),
                'taker_buy_quote': float(k[10])
            } for k in klines]

        except BinanceAPIException as e:
            logger.error(f"Failed to get historical klines: {e}")
            raise

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict:
        """
        거래소 정보 조회

        Args:
            symbol: 특정 거래쌍 (선택사항)

        Returns:
            거래소 정보
        """
        try:
            if symbol:
                return self.client.get_symbol_info(symbol)
            return self.client.get_exchange_info()
        except BinanceAPIException as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise

    def get_account_info(self) -> Dict:
        """
        계정 정보 조회

        Returns:
            계정 정보
        """
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account info: {e}")
            raise 