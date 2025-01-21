from typing import Dict, Tuple, Optional
from .base_risk_manager import BaseRiskManager

class BasicRiskManager(BaseRiskManager):
    """기본 리스크 관리 전략"""
    
    name = "Basic"
    description = "기본적인 리스크 관리 전략 (고정 손절/이익실현, 최대 보유기간)"
    default_params = {
        'stop_loss_pct': 2.0,  # 손절 비율 (%)
        'risk_reward_ratio': 2.0,  # 이익실현/손절 비율
        'max_holding_minutes': 1440,  # 최대 보유 기간 (분)
        'trailing_stop_pct': None,  # 트레일링 스탑 비율 (%)
        'risk_per_trade': 0.02,  # 거래당 리스크 비율
    }
    
    def validate_params(self):
        """파라미터 유효성 검사"""
        if not isinstance(self.params['stop_loss_pct'], (int, float)) or self.params['stop_loss_pct'] <= 0:
            raise ValueError("Stop loss percentage must be positive")
        
        if not isinstance(self.params['risk_reward_ratio'], (int, float)) or self.params['risk_reward_ratio'] <= 0:
            raise ValueError("Risk reward ratio must be positive")
        
        if not isinstance(self.params['max_holding_minutes'], int) or self.params['max_holding_minutes'] <= 0:
            raise ValueError("Maximum holding period must be a positive integer")
        
        if self.params['trailing_stop_pct'] is not None:
            if not isinstance(self.params['trailing_stop_pct'], (int, float)) or self.params['trailing_stop_pct'] <= 0:
                raise ValueError("Trailing stop percentage must be positive")
        
        if not 0 < self.params['risk_per_trade'] < 1:
            raise ValueError("Risk per trade must be between 0 and 1")
    
    def calculate_stop_loss(self,
                          entry_price: float,
                          position_type: str,
                          volatility: Optional[float] = None) -> float:
        """
        손절가 계산
        
        Args:
            entry_price: 진입가
            position_type: 포지션 타입 ('long' or 'short')
            volatility: 변동성 (사용하지 않음)
            
        Returns:
            손절가
        """
        stop_loss_ratio = self.params['stop_loss_pct'] / 100
        
        if position_type == 'long':
            return entry_price * (1 - stop_loss_ratio)
        else:  # short
            return entry_price * (1 + stop_loss_ratio)
    
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
        stop_loss_distance = abs(entry_price - stop_loss)
        take_profit_distance = stop_loss_distance * self.params['risk_reward_ratio']
        
        if position_type == 'long':
            return entry_price + take_profit_distance
        else:  # short
            return entry_price - take_profit_distance
    
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
        # 최대 보유기간 초과
        if holding_period >= self.params['max_holding_minutes']:
            return True, 'max_holding_period'
        
        # 손절/이익실현 확인
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
        
        # 트레일링 스탑 확인
        if self.params['trailing_stop_pct'] is not None:
            trailing_stop_ratio = self.params['trailing_stop_pct'] / 100
            
            if position_type == 'long':
                max_price = max(entry_price, current_price)
                trailing_stop = max_price * (1 - trailing_stop_ratio)
                if current_price <= trailing_stop:
                    return True, 'trailing_stop'
            else:  # short
                min_price = min(entry_price, current_price)
                trailing_stop = min_price * (1 + trailing_stop_ratio)
                if current_price >= trailing_stop:
                    return True, 'trailing_stop'
        
        return False, '' 