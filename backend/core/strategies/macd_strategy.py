from typing import Dict
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    """MACD 전략"""
    
    name = "MACD"
    description = "MACD(Moving Average Convergence Divergence) 기반 매매 전략"
    default_params = {
        'fast_period': 12,  # 단기 이동평균 기간
        'slow_period': 26,  # 장기 이동평균 기간
        'signal_period': 9,  # 시그널 이동평균 기간
        'exit_threshold': 0  # 청산 임계값
    }
    
    def validate_params(self):
        """파라미터 유효성 검사"""
        if not isinstance(self.params['fast_period'], int) or self.params['fast_period'] < 1:
            raise ValueError("Fast period must be a positive integer")
        
        if not isinstance(self.params['slow_period'], int) or self.params['slow_period'] < 1:
            raise ValueError("Slow period must be a positive integer")
        
        if not isinstance(self.params['signal_period'], int) or self.params['signal_period'] < 1:
            raise ValueError("Signal period must be a positive integer")
        
        if self.params['fast_period'] >= self.params['slow_period']:
            raise ValueError("Fast period must be less than slow period")
    
    def _calculate_macd(self, data: pd.DataFrame) -> tuple:
        """
        MACD 계산
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            (MACD 라인, 시그널 라인, MACD 히스토그램)
        """
        close = data['close']
        
        # 지수이동평균 계산
        exp1 = close.ewm(span=self.params['fast_period'], adjust=False).mean()
        exp2 = close.ewm(span=self.params['slow_period'], adjust=False).mean()
        
        # MACD 라인 계산
        macd_line = exp1 - exp2
        
        # 시그널 라인 계산
        signal_line = macd_line.ewm(span=self.params['signal_period'], adjust=False).mean()
        
        # MACD 히스토그램 계산
        macd_hist = macd_line - signal_line
        
        return macd_line, signal_line, macd_hist
    
    def calculate_signals(self, data: pd.DataFrame) -> Dict:
        """
        거래 신호 계산
        
        Args:
            data: OHLCV 데이터
            
        Returns:
            거래 신호
        """
        if len(data) < self.params['slow_period'] + self.params['signal_period']:
            return {
                'direction': None,
                'entry_price': 0,
                'exit_signal': False,
                'volatility': 0
            }
        
        # MACD 계산
        macd_line, signal_line, macd_hist = self._calculate_macd(data)
        
        current_price = data['close'].iloc[-1]
        current_hist = macd_hist.iloc[-1]
        prev_hist = macd_hist.iloc[-2]
        
        # 포지션 방향 결정
        direction = None
        if prev_hist < 0 and current_hist > 0:  # 골든 크로스
            direction = 'long'
        elif prev_hist > 0 and current_hist < 0:  # 데드 크로스
            direction = 'short'
        
        # 청산 신호 계산
        exit_signal = False
        if direction is None:  # 포지션이 없는 경우
            if abs(current_hist) < self.params['exit_threshold']:
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
        macd_line, signal_line, macd_hist = self._calculate_macd(data)
        
        return {
            'macd': macd_line.tolist(),
            'signal': signal_line.tolist(),
            'histogram': macd_hist.tolist()
        } 