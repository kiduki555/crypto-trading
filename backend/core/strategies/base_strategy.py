from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

class BaseStrategy(ABC):
    """
    모든 거래 전략의 기본 클래스
    """
    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.validate_params()

    @abstractmethod
    def validate_params(self):
        """
        전략 파라미터 유효성 검사
        """
        pass

    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        거래 신호 계산

        Args:
            data: OHLCV 데이터

        Returns:
            Dict with:
                - direction: 'long' | 'short' | None
                - entry_price: Optional[float]
                - stop_loss: Optional[float]
                - take_profit: Optional[float]
                - metadata: Optional[Dict[str, Any]] (지표값 등 추가 정보)
        """
        pass

    @abstractmethod
    def get_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        전략에서 사용하는 기술적 지표 계산

        Args:
            data: OHLCV 데이터

        Returns:
            지표명과 값의 딕셔너리
        """
        pass

    def calculate_position_size(self, 
                              capital: float, 
                              current_price: float,
                              risk_per_trade: float) -> float:
        """
        포지션 크기 계산 (선택적 구현)

        Args:
            capital: 계좌 자본금
            current_price: 현재 가격
            risk_per_trade: 거래당 리스크 비율 (0.01 = 1%)

        Returns:
            포지션 크기
        """
        return (capital * risk_per_trade) / current_price

    @property
    def name(self) -> str:
        """
        전략 이름
        """
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """
        전략 설명 (선택적 구현)
        """
        return "No description provided"

    @property
    def default_params(self) -> Dict[str, Any]:
        """
        기본 파라미터 (선택적 구현)
        """
        return {} 