from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional

class BaseRiskManager(ABC):
    """리스크 관리 기본 클래스"""
    
    name: str
    description: str
    default_params: Dict
    
    def __init__(self, params: Dict):
        """
        리스크 관리자 초기화
        
        Args:
            params: 리스크 관리 파라미터
        """
        self.params = {**self.default_params, **params}
        self.validate_params()
    
    @abstractmethod
    def validate_params(self):
        """파라미터 유효성 검사"""
        pass
    
    @abstractmethod
    def calculate_stop_loss(self,
                          entry_price: float,
                          position_type: str,
                          volatility: Optional[float] = None) -> float:
        """
        손절가 계산
        
        Args:
            entry_price: 진입가
            position_type: 포지션 타입 ('long' or 'short')
            volatility: 변동성
            
        Returns:
            손절가
        """
        pass
    
    @abstractmethod
    def calculate_take_profit(self,
                            entry_price: float,
                            position_type: str,
                            stop_loss: float) -> float:
        """
        이익실현가 계산
        
        Args:
            entry_price: 진입가
            position_type: 포지션 타입 ('long' or 'short')
            stop_loss: 손절가
            
        Returns:
            이익실현가
        """
        pass
    
    @abstractmethod
    def should_close_position(self,
                            position_type: str,
                            entry_price: float,
                            current_price: float,
                            stop_loss: float,
                            take_profit: float,
                            unrealized_pnl: float,
                            holding_period: int) -> Tuple[bool, str]:
        """
        포지션 청산 여부 확인
        
        Args:
            position_type: 포지션 타입 ('long' or 'short')
            entry_price: 진입가
            current_price: 현재가
            stop_loss: 손절가
            take_profit: 이익실현가
            unrealized_pnl: 미실현 손익
            holding_period: 보유 기간 (분)
            
        Returns:
            (청산 여부, 청산 이유)
        """
        pass 