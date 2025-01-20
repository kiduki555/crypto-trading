from typing import Dict, Any, Tuple
from .base_risk import BaseRiskManagement

class FixedStopLoss(BaseRiskManagement):
    def __init__(self, params: Dict[str, Any]):
        """
        고정 손절 전략 초기화
        
        Args:
            params: {
                'stop_loss_pct': 손절 비율,
                'take_profit_pct': 익절 비율,
                'leverage': 레버리지
            }
        """
        super().__init__(params)
        self.stop_loss_pct = params.get('stop_loss_pct', 0.02)  # 2%
        self.take_profit_pct = params.get('take_profit_pct', 0.06)  # 6%
        self.leverage = min(params.get('leverage', 3), self.max_leverage)

    def calculate_risk_params(self, entry_price: float, position_size: float) -> Tuple[float, float, float]:
        """
        고정 비율 기반 리스크 파라미터 계산
        
        Args:
            entry_price: 진입 가격
            position_size: 포지션 크기
        Returns:
            (스탑로스, 익절가, 레버리지)
        """
        stop_loss = entry_price * (1 - self.stop_loss_pct) if position_size > 0 else \
                   entry_price * (1 + self.stop_loss_pct)
        
        take_profit = entry_price * (1 + self.take_profit_pct) if position_size > 0 else \
                     entry_price * (1 - self.take_profit_pct)
        
        return stop_loss, take_profit, self.leverage

    def update_risk_params(self, current_price: float, position_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        고정 손절/익절 업데이트 (변경 없음)
        
        Args:
            current_price: 현재 가격
            position_data: 포지션 정보
        Returns:
            (스탑로스, 익절가)
        """
        return position_data['stop_loss'], position_data['take_profit']
