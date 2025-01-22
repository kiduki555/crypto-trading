import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import ccxt
import sqlite3
from binance.client import Client

class DataLoader:
    def __init__(self, config: Dict[str, Any]):
        """
        데이터 로더 초기화
        
        Args:
            config: 설정 정보
        """
        self.config = config
        self.db_path = config.get('database', 'data/market_data.db')
        self.client = Client(config.get('api_key', ''), config.get('api_secret', ''))
        self.logger = logging.getLogger(__name__)

    def fetch_historical_data(self, 
                            symbol: str,
                            timeframe: str = '1m',
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        과거 데이터 조회
        
        Args:
            symbol: 거래 심볼
            timeframe: 시간 간격
            start_time: 시작 시간
            end_time: 종료 시간
        Returns:
            OHLCV 데이터프레임
        """
        try:
            # 데이터베이스에서 먼저 확인
            data = self._load_from_database(symbol, timeframe, start_time, end_time)
            
            if data is not None and not data.empty:
                return data
                
            # API에서 데이터 조회
            if start_time is None:
                start_time = datetime.now() - timedelta(days=30)  # 기본값 30일
            if end_time is None:
                end_time = datetime.now()

            # Binance API의 klines 사용
            klines = self.client.get_historical_klines(
                symbol,
                timeframe,
                start_time.strftime("%d %b %Y %H:%M:%S"),
                end_time.strftime("%d %b %Y %H:%M:%S")
            )

            df = pd.DataFrame(
                klines,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore']
            )
            
            # 필요한 컬럼만 선택
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # 데이터 타입 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.set_index('timestamp', inplace=True)
            
            # 데이터베이스에 저장
            self._save_to_database(df, symbol, timeframe)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()

    def _load_from_database(self,
                          symbol: str,
                          timeframe: str,
                          start_time: Optional[datetime],
                          end_time: Optional[datetime]) -> Optional[pd.DataFrame]:
        """
        데이터베이스에서 데이터 로드
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 테이블이 없는 경우 생성
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp DATETIME,
                    symbol TEXT,
                    timeframe TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY (timestamp, symbol, timeframe)
                )
            """)
            
            query = f"""
                SELECT * FROM market_data 
                WHERE symbol = '{symbol}' 
                AND timeframe = '{timeframe}'
            """
            
            if start_time:
                query += f" AND timestamp >= '{start_time}'"
            if end_time:
                query += f" AND timestamp <= '{end_time}'"
                
            query += " ORDER BY timestamp ASC"  # timestamp로 정렬
                
            df = pd.read_sql_query(query, conn, index_col='timestamp', parse_dates=['timestamp'])
            conn.close()
            
            if df.empty:
                return None
                
            # 인덱스를 datetime으로 변환하고 정렬
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # 중복된 인덱스 제거
            df = df[~df.index.duplicated(keep='last')]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading from database: {str(e)}")
            return None

    def _save_to_database(self,
                         df: pd.DataFrame,
                         symbol: str,
                         timeframe: str):
        """
        데이터베이스에 데이터 저장
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 테이블이 없는 경우 생성
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp DATETIME,
                    symbol TEXT,
                    timeframe TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY (timestamp, symbol, timeframe)
                )
            """)
            
            # 데이터프레임을 SQL로 저장
            df = df.copy()  # 원본 데이터프레임 보존
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            
            # 중복된 데이터 처리를 위해 기존 데이터 삭제
            delete_query = f"""
                DELETE FROM market_data 
                WHERE symbol = '{symbol}' 
                AND timeframe = '{timeframe}'
                AND timestamp >= '{df.index.min()}'
                AND timestamp <= '{df.index.max()}'
            """
            conn.execute(delete_query)
            
            # 새 데이터 저장
            df.to_sql('market_data', conn, if_exists='append', index=True)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {str(e)}")

    def ensure_historical_data(self,
                             symbol: str,
                             timeframe: str = '1m',
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             days: int = 30) -> bool:
        """
        백테스팅을 위한 충분한 과거 데이터가 있는지 확인하고, 없으면 데이터를 가져와서 저장
        
        Args:
            symbol: 거래 심볼
            timeframe: 시간 간격
            start_time: 시작 시간 (지정하지 않으면 현재 시간 - days)
            end_time: 종료 시간 (지정하지 않으면 현재 시간)
            days: start_time이 지정되지 않았을 때 사용할 과거 데이터 기간 (일)
        Returns:
            bool: 데이터 준비 성공 여부
        """
        try:
            if end_time is None:
                end_time = datetime.now()
            if start_time is None:
                start_time = end_time - timedelta(days=days)
                
            # 지표 계산을 위해 시작 시간보다 더 이전의 데이터를 가져옴
            extended_start_time = start_time - timedelta(days=100)  # 100일 추가
            
            # 데이터베이스에서 데이터 확인
            existing_data = self._load_from_database(symbol, timeframe, extended_start_time, end_time)
            
            if existing_data is not None and not existing_data.empty:
                self.logger.info(f"Historical data already exists for {symbol}")
                return True
                
            # 데이터가 없으면 API에서 가져오기
            self.logger.info(f"Fetching historical data for {symbol} from {extended_start_time} to {end_time}")
            
            df = self.fetch_historical_data(symbol, timeframe, extended_start_time, end_time)
            
            if df.empty:
                self.logger.error(f"Failed to fetch historical data for {symbol}")
                return False
                
            self.logger.info(f"Successfully fetched and stored historical data for {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring historical data: {str(e)}")
            return False
