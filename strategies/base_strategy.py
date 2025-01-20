from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
import numpy as np
import ta

class BaseStrategy(ABC):
    def __init__(self, params: Dict[str, Any]):
        """
        기본 전략 클래스 초기화
        
        Args:
            params: 전략 파라미터
        """
        self.params = params
        
    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        매매 신호 계산
        
        Args:
            data: OHLCV 데이터
        Returns:
            매매 신호 정보
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
        required_columns = ['open', 'high', 'low', 'close', 'volume']
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
