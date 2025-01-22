from typing import Dict, Any
import pandas as pd
import numpy as np
from backtesting.lib import crossover
from backtesting import Strategy

class MACrossoverStrategy(Strategy):
    # 클래스 변수로 파라미터 정의
    short_window = 10
    long_window = 20
    ma_type = 'sma'
    position_size = 0.3  # 레버리지를 포함한 포지션 크기 (자본금의 30%)

    def init(self):
        """전략 초기화"""
        # 이동평균 계산
        if self.ma_type == 'ema':
            self.fast_ma = self.I(lambda x: pd.Series(x).ewm(span=self.short_window).mean(), self.data.Close)
            self.slow_ma = self.I(lambda x: pd.Series(x).ewm(span=self.long_window).mean(), self.data.Close)
        else:
            self.fast_ma = self.I(lambda x: pd.Series(x).rolling(window=self.short_window).mean(), self.data.Close)
            self.slow_ma = self.I(lambda x: pd.Series(x).rolling(window=self.long_window).mean(), self.data.Close)

    def next(self):
        """매 캔들마다 호출되는 메서드"""
        # 포지션이 없을 때
        if not self.position:
            # 골든 크로스 (매수 신호)
            if crossover(self.fast_ma, self.slow_ma):
                self.buy(size=self.position_size)
            # 데드 크로스 (매도 신호)
            elif crossover(self.slow_ma, self.fast_ma):
                self.sell(size=self.position_size)
        
        # 롱 포지션 보유 중
        elif self.position.is_long:
            # 데드 크로스 (청산 신호)
            if crossover(self.slow_ma, self.fast_ma):
                self.position.close()
        
        # 숏 포지션 보유 중
        elif self.position.is_short:
            # 골든 크로스 (청산 신호)
            if crossover(self.fast_ma, self.slow_ma):
                self.position.close()
