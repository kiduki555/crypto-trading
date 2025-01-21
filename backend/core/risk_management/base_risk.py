from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

class BaseRiskManagement(ABC):
    """
    모든 리스크 관리 전략의 기본 클래스
    """
    def __init__(self, params: Dict[str, Any]):
        self.params = params
        self.validate_params()

    @abstractmethod
    def validate_params(self):
        """
        리스크 관리 파라미터 유효성 검사
        """
        pass

    @abstractmethod
    def calculate_position_size(self,
                              capital: float,
                              current_price: float,
                              volatility: Optional[float] = None) -> float:
        """
        적정 포지션 크기 계산

        Args:
            capital: 계좌 자본금
            current_price: 현재 가격
            volatility: 변동성 지표 (ATR 등)

        Returns:
            포지션 크기
        """
        pass

    @abstractmethod
    def calculate_stop_loss(self,
                          entry_price: float,
                          position_type: str,
                          volatility: Optional[float] = None) -> float:
        """
        스탑로스 가격 계산

        Args:
            entry_price: 진입 가격
            position_type: 'long' 또는 'short'
            volatility: 변동성 지표 (ATR 등)

        Returns:
            스탑로스 가격
        """
        pass

    @abstractmethod
    def calculate_take_profit(self,
                            entry_price: float,
                            position_type: str,
                            stop_loss: float) -> float:
        """
        익절 가격 계산

        Args:
            entry_price: 진입 가격
            position_type: 'long' 또는 'short'
            stop_loss: 스탑로스 가격

        Returns:
            익절 가격
        """
        pass

    def should_close_position(self,
                            position_type: str,
                            entry_price: float,
                            current_price: float,
                            stop_loss: float,
                            take_profit: float,
                            unrealized_pnl: float,
                            holding_time: int) -> Tuple[bool, str]:
        """
        포지션 청산 여부 결정 (선택적 구현)

        Args:
            position_type: 'long' 또는 'short'
            entry_price: 진입 가격
            current_price: 현재 가격
            stop_loss: 스탑로스 가격
            take_profit: 익절 가격
            unrealized_pnl: 미실현 손익
            holding_time: 보유 시간 (분)

        Returns:
            (청산 여부, 청산 이유)
        """
        # 기본 구현: 스탑로스 또는 익절 도달 시 청산
        if position_type == 'long':
            if current_price <= stop_loss:
                return True, 'stop_loss'
            if current_price >= take_profit:
                return True, 'take_profit'
        else:  # short
            if current_price >= stop_loss:
                return True, 'stop_loss'
            if current_price <= take_profit:
                return True, 'take_profit'
        
        return False, ''

    def adjust_stop_loss(self,
                        position_type: str,
                        entry_price: float,
                        current_price: float,
                        current_stop_loss: float,
                        unrealized_pnl: float,
                        holding_time: int) -> Optional[float]:
        """
        스탑로스 조정 (선택적 구현)

        Args:
            position_type: 'long' 또는 'short'
            entry_price: 진입 가격
            current_price: 현재 가격
            current_stop_loss: 현재 스탑로스 가격
            unrealized_pnl: 미실현 손익
            holding_time: 보유 시간 (분)

        Returns:
            새로운 스탑로스 가격 또는 None (조정하지 않을 경우)
        """
        return None

    @property
    def name(self) -> str:
        """
        리스크 관리 전략 이름
        """
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """
        리스크 관리 전략 설명 (선택적 구현)
        """
        return "No description provided"

    @property
    def default_params(self) -> Dict[str, Any]:
        """
        기본 파라미터 (선택적 구현)
        """
        return {} 