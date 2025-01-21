from typing import Dict
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class BollingerStrategy(BaseStrategy):
    """볼린저 밴드 전략"""
    
    name = "Bollinger"
    description = "볼린저 밴드를 이용한 매매 전략"
    default_params = {
        'period': 20,  # 이동평균 기간
        'std_dev': 2,  # 표준편차 배수
        'exit_threshold': 0.5,  # 중심선 대비 청산 임계값
    }
    
    def validate_params(self):
        """파라미터 유효성 검사"""
        if not isinstance(self.params['period'], int) or self.params['period'] < 1:
            raise ValueError("Period must be a positive integer")
        
        if not isinstance(self.params['std_dev'], (int, float)) or self.params['std_dev'] <= 0:
            raise ValueError("Standard deviation multiplier must be positive")
        
        if not 0 < self.params['exit_threshold'] < 1:
            raise ValueError("Exit threshold must be between 0 and 1")
    
    def calculate_signals(self, data: pd.DataFrame) -> Dict:
        """
        거래 신호 계산
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            거래 신호
        """
        if len(data) < self.params['period']:
            return {
                'direction': None,
                'entry_price': 0,
                'exit_signal': False,
                'volatility': 0
            }
        
        # 볼린저 밴드 계산
        close = data['close']
        sma = close.rolling(window=self.params['period']).mean()
        std = close.rolling(window=self.params['period']).std()
        
        upper = sma + (std * self.params['std_dev'])
        lower = sma - (std * self.params['std_dev'])
        
        current_price = close.iloc[-1]
        current_sma = sma.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        
        # 포지션 방향 결정
        direction = None
        if current_price < current_lower:
            direction = 'long'
        elif current_price > current_upper:
            direction = 'short'
        
        # 청산 신호 계산
        exit_signal = False
        if direction is None:  # 포지션이 없는 경우
            # 중심선(SMA)에 가까워졌을 때 청산
            distance_to_sma = abs(current_price - current_sma) / (current_upper - current_lower)
            if distance_to_sma < self.params['exit_threshold']:
                exit_signal = True
        
        return {
            'direction': direction,
            'entry_price': current_price,
            'exit_signal': exit_signal,
            'volatility': self._calculate_volatility(data)
        }
    
    def get_indicators(self, data: pd.DataFrame) -> Dict:
        """
        지표 데이터 반환
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            지표 데이터
        """
        close = data['close']
        sma = close.rolling(window=self.params['period']).mean()
        std = close.rolling(window=self.params['period']).std()
        
        upper = sma + (std * self.params['std_dev'])
        lower = sma - (std * self.params['std_dev'])
        
        return {
            'middle': sma.tolist(),
            'upper': upper.tolist(),
            'lower': lower.tolist(),
            'width': ((upper - lower) / sma * 100).tolist()  # 밴드폭
        } 