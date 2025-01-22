from typing import Dict, Any
import pandas as pd
import numpy as np
from backtesting.lib import crossover
from .base_strategy import BaseStrategy

class BollingerStrategy(BaseStrategy):
    # 클래스 변수로 파라미터 정의
    window = 20
    std_dev = 2.0
    entry_threshold = 1.0
    exit_threshold = 0.5

    def init(self):
        """전략 초기화"""
        # 볼린저 밴드 계산
        self.close = self.data.Close
        self.sma = self.I(lambda: pd.Series(self.close).rolling(window=self.window).mean())
        self.std = self.I(lambda: pd.Series(self.close).rolling(window=self.window).std())
        
        self.upper = self.I(lambda: self.sma + self.std_dev * self.std)
        self.lower = self.I(lambda: self.sma - self.std_dev * self.std)
        
        # 밴드폭 계산
        self.bandwidth = self.I(lambda: (self.upper - self.lower) / self.sma)

    def next(self):
        """매 캔들마다 호출되는 메서드"""
        # 현재 가격이 밴드를 벗어난 정도 계산
        upper_distance = (self.close[-1] - self.upper[-1]) / (self.bandwidth[-1] * self.sma[-1])
        lower_distance = (self.lower[-1] - self.close[-1]) / (self.bandwidth[-1] * self.sma[-1])
        
        # 포지션이 없을 때
        if not self.position:
            # 하단 밴드 아래로 크게 벗어난 경우 매수
            if lower_distance > self.entry_threshold:
                self.buy()
            # 상단 밴드 위로 크게 벗어난 경우 매도
            elif upper_distance > self.entry_threshold:
                self.sell()
        
        # 롱 포지션 보유 중
        elif self.position.is_long:
            # 중간 밴드에 가까워진 경우 청산
            if abs(self.close[-1] - self.sma[-1]) < (self.bandwidth[-1] * self.exit_threshold):
                self.position.close()
        
        # 숏 포지션 보유 중
        elif self.position.is_short:
            # 중간 밴드에 가까워진 경우 청산
            if abs(self.close[-1] - self.sma[-1]) < (self.bandwidth[-1] * self.exit_threshold):
                self.position.close() 