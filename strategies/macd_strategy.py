from typing import Dict, Any
import pandas as pd
import ta
from .base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any]):
        """
        MACD 전략 초기화
        
        Args:
            params: {
                'fast_period': 빠른 이동평균 기간,
                'slow_period': 느린 이동평균 기간,
                'signal_period': 시그널 기간
            }
        """
        super().__init__(params)
        self.fast_period = params.get('fast_period', 12)
        self.slow_period = params.get('slow_period', 26)
        self.signal_period = params.get('signal_period', 9)

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        MACD 기반 매매 신호 계산
        
        Args:
            data: OHLCV 데이터
        Returns:
            매매 신호 정보
        """
        if not self._validate_data(data):
            return {'direction': None, 'strength': 0}

        # MACD 계산
        macd = ta.trend.MACD(
            close=data['close'],
            window_slow=self.slow_period,
            window_fast=self.fast_period,
            window_sign=self.signal_period
        )
        
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        
        # 충분한 데이터가 없는 경우 처리
        if len(macd_line) < 2 or len(signal_line) < 2:
            return {
                'direction': None,
                'strength': 0,
                'macd': None,
                'signal': None
            }
        
        # NaN 값 처리
        if pd.isna(macd_line.iloc[-1]) or pd.isna(signal_line.iloc[-1]) or \
           pd.isna(macd_line.iloc[-2]) or pd.isna(signal_line.iloc[-2]):
            return {
                'direction': None,
                'strength': 0,
                'macd': None,
                'signal': None
            }
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]

        # 신호 생성
        if current_macd > current_signal and prev_macd <= prev_signal:
            return {
                'direction': 'long',
                'strength': abs(current_macd - current_signal),
                'macd': current_macd,
                'signal': current_signal
            }
        elif current_macd < current_signal and prev_macd >= prev_signal:
            return {
                'direction': 'short',
                'strength': abs(current_macd - current_signal),
                'macd': current_macd,
                'signal': current_signal
            }
        
        return {
            'direction': None, 
            'strength': 0,
            'macd': current_macd,
            'signal': current_signal
        }
