from typing import Dict
import pandas as pd
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI 전략"""
    
    name = "RSI"
    description = "RSI(Relative Strength Index) 기반 매매 전략"
    default_params = {
        'period': 14,  # RSI 계산 기간
        'overbought': 70,  # 과매수 기준
        'oversold': 30,  # 과매도 기준
        'exit_threshold': 50,  # 청산 기준
    }
    
    def validate_params(self):
        """파라미터 유효성 검사"""
        if not isinstance(self.params['period'], int) or self.params['period'] < 1:
            raise ValueError("RSI period must be a positive integer")
        
        if not 0 < self.params['oversold'] < self.params['overbought'] < 100:
            raise ValueError("Invalid RSI thresholds")
    
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
        
        # RSI 계산
        close = data['close']
        delta = close.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['period']).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        current_price = close.iloc[-1]
        
        # 포지션 방향 결정
        direction = None
        if current_rsi < self.params['oversold']:
            direction = 'long'
        elif current_rsi > self.params['overbought']:
            direction = 'short'
        
        # 청산 신호 계산
        exit_signal = False
        if direction is None:  # 포지션이 없는 경우
            if current_rsi > self.params['exit_threshold']:
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
        # RSI 계산
        close = data['close']
        delta = close.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['period']).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return {
            'rsi': rsi.tolist(),
            'overbought': [self.params['overbought']] * len(data),
            'oversold': [self.params['oversold']] * len(data),
            'exit_threshold': [self.params['exit_threshold']] * len(data)
        } 