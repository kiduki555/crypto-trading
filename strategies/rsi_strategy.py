from typing import Dict, Any
import pandas as pd
import ta
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any]):
        """
        RSI 전략 초기화
        
        Args:
            params: {
                'rsi_period': RSI 기간,
                'oversold_threshold': 과매도 기준값,
                'overbought_threshold': 과매수 기준값
            }
        """
        super().__init__(params)
        self.rsi_period = params.get('rsi_period', 14)
        self.oversold = params.get('oversold_threshold', 30)
        self.overbought = params.get('overbought_threshold', 70)

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        RSI 기반 매매 신호 계산
        
        Args:
            data: OHLCV 데이터
        Returns:
            매매 신호 정보
        """
        if not self._validate_data(data):
            return {'direction': None, 'strength': 0}

        # RSI 계산
        rsi = ta.momentum.RSIIndicator(
            close=data['close'], 
            window=self.rsi_period
        ).rsi()

        current_rsi = rsi.iloc[-1]
        
        # 신호 생성
        if current_rsi < self.oversold:
            return {
                'direction': 'long',
                'strength': (self.oversold - current_rsi) / self.oversold,
                'rsi': current_rsi
            }
        elif current_rsi > self.overbought:
            return {
                'direction': 'short',
                'strength': (current_rsi - self.overbought) / (100 - self.overbought),
                'rsi': current_rsi
            }
        
        return {'direction': None, 'strength': 0, 'rsi': current_rsi}
