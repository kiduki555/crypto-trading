from typing import Dict, Any
import pandas as pd
import numpy as np
from backtesting import Strategy

class RSIStrategy(Strategy):
    # 클래스 변수로 파라미터 정의
    rsi_period = 14
    oversold = 30
    overbought = 70
    position_size = 0.3  # 레버리지를 포함한 포지션 크기 (자본금의 30%)

    def init(self):
        """전략 초기화"""
        # RSI 계산
        close = pd.Series(self.data.Close)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        self.rsi = self.I(lambda: 100 - (100 / (1 + rs)))

    def next(self):
        """매 캔들마다 호출되는 메서드"""
        # 포지션이 없을 때
        if not self.position:
            # 과매도 상태에서 매수
            if self.rsi[-1] < self.oversold:
                self.buy(size=self.position_size)
            # 과매수 상태에서 매도
            elif self.rsi[-1] > self.overbought:
                self.sell(size=self.position_size)
        
        # 롱 포지션 보유 중
        elif self.position.is_long:
            # 과매수 상태에서 청산
            if self.rsi[-1] > self.overbought:
                self.position.close()
        
        # 숏 포지션 보유 중
        elif self.position.is_short:
            # 과매도 상태에서 청산
            if self.rsi[-1] < self.oversold:
                self.position.close()
