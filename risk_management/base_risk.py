from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import pandas as pd

class BaseRiskManager:
    def __init__(self, params: Dict[str, Any]):
        """
        기본 리스크 관리 클래스
        
        Args:
            params: {
                'risk_per_trade': 거래당 리스크 비율 (기본값: 0.01),
                'max_leverage': 최대 레버리지 (기본값: 3),
                'margin_ratio': 필요 증거금 비율 (기본값: 0.1)
            }
        """
        self.risk_per_trade = params.get('risk_per_trade', 0.01)  # 1%
        self.max_leverage = params.get('max_leverage', 3)
        self.margin_ratio = params.get('margin_ratio', 0.1)  # 10%
        
    def calculate_risk_params(self, signal: Dict[str, Any],
                            current_price: float,
                            account_balance: float) -> Dict[str, Any]:
        """
        리스크 파라미터 계산
        
        Args:
            signal: 전략 신호
            current_price: 현재 가격
            account_balance: 계좌 잔고
            
        Returns:
            {
                'position_size': 포지션 크기,
                'stop_loss': 손절가,
                'take_profit': 익절가,
                'margin_ratio': 증거금 비율
            }
        """
        # 기본 포지션 크기 계산 (계좌 잔고 * 리스크 비율)
        position_size = (account_balance * self.risk_per_trade) / current_price
        
        # 레버리지 제한 적용
        max_position = (account_balance * self.max_leverage) / current_price
        position_size = min(position_size, max_position)
        
        # 신호 강도에 따른 포지션 크기 조정
        if 'strength' in signal:
            position_size *= signal['strength']
            
        return {
            'position_size': position_size,
            'stop_loss': None,  # 하위 클래스에서 구현
            'take_profit': None,  # 하위 클래스에서 구현
            'margin_ratio': self.margin_ratio
        }

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
