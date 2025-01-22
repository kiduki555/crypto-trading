from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
import numpy as np
import ta
from backtesting import Strategy

class BaseStrategy(Strategy):
    def __init__(self, broker=None, data=None, params=None):
        """
        기본 전략 클래스 초기화
        """
        super().__init__(broker, data, params or {})
        
    def init(self):
        """
        전략 초기화 - backtesting 패키지 요구사항
        """
        pass
        
    @abstractmethod
    def next(self):
        """
        매 캔들마다 호출되는 메서드 - backtesting 패키지 요구사항
        여기서 매매 신호를 생성하고 포지션을 진입/청산
        """
        pass
    
    def _validate_data(self, data: pd.DataFrame) -> bool:
        """
        데이터 유효성 검증
        
        Args:
            data: OHLCV 데이터
        Returns:
            유효성 여부
        """
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in data.columns for col in required_columns)

    def get_position_size(self, account_balance: float, risk_per_trade: float) -> float:
        """
        포지션 크기 계산
        
        Args:
            account_balance: 계좌 잔고
            risk_per_trade: 트레이드당 리스크 비율
        Returns:
            포지션 크기
        """
        return account_balance * risk_per_trade
