from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from utils.binance_client import BinanceClient
from utils.websocket_client import BinanceWebSocketClient
from utils.logger import logger

class ExchangeService:
    def __init__(self):
        """거래소 서비스 초기화"""
        self.rest_client = BinanceClient()
        self.ws_client = BinanceWebSocketClient()
        self._subscribers = {}

    async def get_historical_data(self,
                                symbol: str,
                                interval: str,
                                start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        과거 데이터 조회

        Args:
            symbol: 거래쌍
            interval: 시간간격
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            OHLCV 데이터
        """
        try:
            klines = self.rest_client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time
            )
            
            df = pd.DataFrame(klines)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                         'close_time', 'quote_volume', 'trades',
                         'taker_buy_base', 'taker_buy_quote']
            
            # 타입 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            numeric_columns = ['open', 'high', 'low', 'close', 'volume',
                             'quote_volume', 'taker_buy_base', 'taker_buy_quote']
            df[numeric_columns] = df[numeric_columns].astype(float)
            df['trades'] = df['trades'].astype(int)
            
            return df

        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
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
            return self.rest_client.get_exchange_info(symbol)
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise

    def get_account_info(self) -> Dict:
        """
        계정 정보 조회

        Returns:
            계정 정보
        """
        try:
            return self.rest_client.get_account_info()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    async def subscribe_to_klines(self,
                                symbol: str,
                                interval: str,
                                callback) -> str:
        """
        K라인 데이터 구독

        Args:
            symbol: 거래쌍
            interval: 시간간격
            callback: 데이터 수신 콜백

        Returns:
            구독 ID
        """
        try:
            subscription_id = f"{symbol}@kline_{interval}"
            self.ws_client.add_callback(subscription_id, callback)
            await self.ws_client.connect(symbol.lower(), [f"kline_{interval}"])
            return subscription_id
        except Exception as e:
            logger.error(f"Failed to subscribe to klines: {e}")
            raise

    async def unsubscribe_from_klines(self, subscription_id: str):
        """
        K라인 데이터 구독 해제

        Args:
            subscription_id: 구독 ID
        """
        try:
            await self.ws_client.close()
        except Exception as e:
            logger.error(f"Failed to unsubscribe from klines: {e}")
            raise 