from typing import Dict, Any
import pandas as pd
import numpy as np
from backtesting.lib import crossover
from backtesting import Strategy

class MACDStrategy(Strategy):
    # 클래스 변수로 파라미터 정의
    fast_period = 12
    slow_period = 26
    signal_period = 9
    position_size = 0.3  # 레버리지를 포함한 포지션 크기 (자본금의 30%)

    def init(self):
        """전략 초기화"""
        # MACD 계산
        self.close = self.data.Close
        
        # EMA 계산
        fast_ema = self.I(lambda x: pd.Series(x).ewm(span=self.fast_period, adjust=False).mean(), self.close)
        slow_ema = self.I(lambda x: pd.Series(x).ewm(span=self.slow_period, adjust=False).mean(), self.close)
        
        # MACD 라인 계산
        self.macd_line = self.I(lambda: fast_ema - slow_ema)
        
        # 시그널 라인 계산
        self.signal_line = self.I(lambda x: pd.Series(x).ewm(span=self.signal_period, adjust=False).mean(), self.macd_line)

    def next(self):
        """매 캔들마다 호출되는 메서드"""
        # 포지션이 없을 때
        if not self.position:
            # 골든 크로스 (매수 신호)
            if crossover(self.macd_line, self.signal_line):
                self.buy(size=self.position_size)
            # 데드 크로스 (매도 신호)
            elif crossover(self.signal_line, self.macd_line):
                self.sell(size=self.position_size)
        
        # 롱 포지션 보유 중
        elif self.position.is_long:
            # 데드 크로스 (청산 신호)
            if crossover(self.signal_line, self.macd_line):
                self.position.close()
        
        # 숏 포지션 보유 중
        elif self.position.is_short:
            # 골든 크로스 (청산 신호)
            if crossover(self.macd_line, self.signal_line):
                self.position.close()
