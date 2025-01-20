from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import pandas as pd

class BaseRiskManagement(ABC):
    def __init__(self, params: Dict[str, Any]):
        """
        기본 리스크 관리 클래스 초기화
        
        Args:
            params: 리스크 관리 파라미터
        """
        self.params = params
        self.max_leverage = params.get('max_leverage', 10)
        self.account_balance = params.get('account_balance', 0)
        self.risk_per_trade = params.get('risk_per_trade', 0.01)  # 1%
        
    @abstractmethod
    def calculate_risk_params(self, entry_price: float, position_size: float) -> Tuple[float, float, float]:
        """
        리스크 파라미터 계산
        
        Args:
            entry_price: 진입 가격
            position_size: 포지션 크기
        Returns:
            (스탑로스, 익절가, 레버리지)
        """
        pass
    
    @abstractmethod
    def update_risk_params(self, current_price: float, position_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        리스크 파라미터 동적 업데이트
        
        Args:
            current_price: 현재 가격
            position_data: 포지션 정보
        Returns:
            (새로운 스탑로스, 새로운 익절가)
        """
        pass
    
    def calculate_max_loss(self, position_size: float) -> float:
        """
        최대 손실 금액 계산
        
        Args:
            position_size: 포지션 크기
        Returns:
            최대 손실 금액
        """
        return self.account_balance * self.risk_per_trade
