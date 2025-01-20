from typing import Dict, Any
import pandas as pd
import ta
from .base_strategy import BaseStrategy

class MACrossoverStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any]):
        """
        이동평균 크로스오버 전략 초기화
        
        Args:
            params: {
                'fast_ma_period': 단기 이동평균 기간,
                'slow_ma_period': 장기 이동평균 기간,
                'ma_type': 이동평균 타입 ('sma' or 'ema')
            }
        """
        super().__init__(params)
        self.fast_period = params.get('fast_ma_period', 10)
        self.slow_period = params.get('slow_ma_period', 30)
        self.ma_type = params.get('ma_type', 'sma')

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        이동평균 크로스오버 기반 매매 신호 계산
        
        Args:
            data: OHLCV 데이터
        Returns:
            매매 신호 정보
        """
        if not self._validate_data(data):
            return {'direction': None, 'strength': 0}

        # 이동평균 계산
        if self.ma_type == 'ema':
            fast_ma = ta.trend.EMAIndicator(
                close=data['close'], 
                window=self.fast_period
            ).ema_indicator()
            
            slow_ma = ta.trend.EMAIndicator(
                close=data['close'], 
                window=self.slow_period
            ).ema_indicator()
        else:
            fast_ma = ta.trend.SMAIndicator(
                close=data['close'], 
                window=self.fast_period
            ).sma_indicator()
            
            slow_ma = ta.trend.SMAIndicator(
                close=data['close'], 
                window=self.slow_period
            ).sma_indicator()

        # 충분한 데이터가 없는 경우 처리
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return {
                'direction': None,
                'strength': 0,
                'fast_ma': None,
                'slow_ma': None
            }
            
        # NaN 값 처리
        if pd.isna(fast_ma.iloc[-1]) or pd.isna(slow_ma.iloc[-1]) or \
           pd.isna(fast_ma.iloc[-2]) or pd.isna(slow_ma.iloc[-2]):
            return {
                'direction': None,
                'strength': 0,
                'fast_ma': None,
                'slow_ma': None
            }

        current_fast = fast_ma.iloc[-1]
        current_slow = slow_ma.iloc[-1]
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]

        # 신호 생성
        if current_fast > current_slow and prev_fast <= prev_slow:
            return {
                'direction': 'long',
                'strength': (current_fast - current_slow) / current_slow,
                'fast_ma': current_fast,
                'slow_ma': current_slow
            }
        elif current_fast < current_slow and prev_fast >= prev_slow:
            return {
                'direction': 'short',
                'strength': (current_slow - current_fast) / current_slow,
                'fast_ma': current_fast,
                'slow_ma': current_slow
            }
        
        return {
            'direction': None,
            'strength': 0,
            'fast_ma': current_fast,
            'slow_ma': current_slow
        }
