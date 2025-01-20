from typing import Dict, Any, Tuple
import numpy as np
from .base_risk import BaseRiskManagement

class DynamicRiskManagement(BaseRiskManagement):
    def __init__(self, params: Dict[str, Any]):
        """
        동적 리스크 관리 전략 초기화
        
        Args:
            params: {
                'atr_period': ATR 기간,
                'stop_loss_atr_multiplier': 손절 ATR 승수,
                'take_profit_atr_multiplier': 익절 ATR 승수,
                'trailing_stop_start_pct': 트레일링 스탑 시작 비율
            }
        """
        super().__init__(params)
        self.atr_period = params.get('atr_period', 14)
        self.stop_loss_multiplier = params.get('stop_loss_atr_multiplier', 2)
        self.take_profit_multiplier = params.get('take_profit_atr_multiplier', 4)
        self.trailing_stop_start = params.get('trailing_stop_start_pct', 0.02)  # 2%
        self.leverage = min(params.get('leverage', 3), self.max_leverage)

    def calculate_risk_params(self, entry_price: float, position_size: float) -> Tuple[float, float, float]:
        """
        ATR 기반 동적 리스크 파라미터 계산
        
        Args:
            entry_price: 진입 가격
            position_size: 포지션 크기
        Returns:
            (스탑로스, 익절가, 레버리지)
        """
        atr = self._calculate_atr(entry_price)
        
        stop_loss = entry_price - (atr * self.stop_loss_multiplier) if position_size > 0 else \
                   entry_price + (atr * self.stop_loss_multiplier)
        
        take_profit = entry_price + (atr * self.take_profit_multiplier) if position_size > 0 else \
                     entry_price - (atr * self.take_profit_multiplier)
        
        return stop_loss, take_profit, self.leverage

    def update_risk_params(self, current_price: float, position_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        트레일링 스탑 기반 동적 리스크 파라미터 업데이트
        
        Args:
            current_price: 현재 가격
            position_data: 포지션 정보
        Returns:
            (새로운 스탑로스, 새로운 익절가)
        """
        entry_price = position_data['entry_price']
        original_stop_loss = position_data['stop_loss']
        take_profit = position_data['take_profit']
        position_size = position_data['size']
        
        # 수익률 계산
        profit_pct = (current_price - entry_price) / entry_price if position_size > 0 else \
                    (entry_price - current_price) / entry_price
        
        # 트레일링 스탑 적용
        if profit_pct > self.trailing_stop_start:
            atr = self._calculate_atr(current_price)
            new_stop_loss = current_price - (atr * self.stop_loss_multiplier) if position_size > 0 else \
                           current_price + (atr * self.stop_loss_multiplier)
            
            # 롱 포지션의 경우 새로운 스탑로스가 기존보다 높을 때만 업데이트
            if position_size > 0:
                stop_loss = max(original_stop_loss, new_stop_loss)
            # 숏 포지션의 경우 새로운 스탑로스가 기존보다 낮을 때만 업데이트
            else:
                stop_loss = min(original_stop_loss, new_stop_loss)
                
            return stop_loss, take_profit
            
        return original_stop_loss, take_profit

    def _calculate_atr(self, current_price: float) -> float:
        """
        ATR(Average True Range) 계산
        실제 구현시 OHLCV 데이터를 사용해야 함
        
        Args:
            current_price: 현재 가격
        Returns:
            ATR 값
        """
        # 임시로 현재가의 1%를 ATR로 사용
        # 실제 구현시 proper ATR 계산 필요
        return current_price * 0.01
