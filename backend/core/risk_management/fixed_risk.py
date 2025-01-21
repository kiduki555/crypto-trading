from typing import Dict, Any, Optional
from .base_risk import BaseRiskManagement

class FixedRiskManagement(BaseRiskManagement):
    """
    고정 리스크 비율을 사용하는 리스크 관리 전략
    """
    def validate_params(self):
        """
        파라미터 유효성 검사
        - risk_per_trade: 거래당 리스크 비율 (0.01 = 1%)
        - risk_reward_ratio: 리스크 대비 보상 비율
        """
        required_params = {'risk_per_trade', 'risk_reward_ratio'}
        if not all(param in self.params for param in required_params):
            raise ValueError(f"Required parameters: {required_params}")
        
        if not 0 < self.params['risk_per_trade'] <= 0.1:
            raise ValueError("risk_per_trade must be between 0 and 0.1")
        
        if self.params['risk_reward_ratio'] <= 0:
            raise ValueError("risk_reward_ratio must be positive")

    def calculate_position_size(self,
                              capital: float,
                              current_price: float,
                              volatility: Optional[float] = None) -> float:
        """
        거래당 리스크 비율에 기반한 포지션 크기 계산
        """
        risk_amount = capital * self.params['risk_per_trade']
        # 변동성이 주어진 경우 이를 활용하여 스탑로스 거리 계산
        if volatility:
            stop_distance = volatility
        else:
            # 기본값으로 현재가의 1% 사용
            stop_distance = current_price * 0.01
        
        position_size = risk_amount / stop_distance
        return position_size

    def calculate_stop_loss(self,
                          entry_price: float,
                          position_type: str,
                          volatility: Optional[float] = None) -> float:
        """
        변동성 기반 스탑로스 계산
        """
        if volatility:
            stop_distance = volatility
        else:
            stop_distance = entry_price * 0.01

        if position_type == 'long':
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance

    def calculate_take_profit(self,
                            entry_price: float,
                            position_type: str,
                            stop_loss: float) -> float:
        """
        리스크 대비 보상 비율에 기반한 익절가 계산
        """
        stop_distance = abs(entry_price - stop_loss)
        take_profit_distance = stop_distance * self.params['risk_reward_ratio']

        if position_type == 'long':
            return entry_price + take_profit_distance
        else:  # short
            return entry_price - take_profit_distance

    @property
    def description(self) -> str:
        return "고정 리스크 비율과 리스크 대비 보상 비율을 사용하는 리스크 관리 전략"

    @property
    def default_params(self) -> Dict[str, Any]:
        return {
            'risk_per_trade': 0.02,  # 2%
            'risk_reward_ratio': 2.0  # 1:2
        } 