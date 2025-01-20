from typing import Dict, Any
import pandas as pd
import ta
from .base_strategy import BaseStrategy

class BollingerStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any]):
        """
        볼린저 밴드 전략 초기화
        
        Args:
            params: {
                'window': 이동평균 기간 (기본값: 20),
                'std_dev': 표준편차 승수 (기본값: 2.0),
                'entry_threshold': 진입 임계값 (기본값: 1.0),
                'exit_threshold': 청산 임계값 (기본값: 0.5)
            }
        """
        super().__init__(params)
        self.window = params.get('window', 20)
        self.std_dev = params.get('std_dev', 2.0)
        self.entry_threshold = params.get('entry_threshold', 1.0)
        self.exit_threshold = params.get('exit_threshold', 0.5)

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        볼린저 밴드 기반 매매 신호 계산
        
        Args:
            data: OHLCV 데이터
        Returns:
            매매 신호 정보
        """
        if not self._validate_data(data):
            return {'direction': None, 'strength': 0}

        # 볼린저 밴드 계산
        bollinger = ta.volatility.BollingerBands(
            close=data['close'],
            window=self.window,
            window_dev=self.std_dev
        )
        
        upper = bollinger.bollinger_hband()
        lower = bollinger.bollinger_lband()
        middle = bollinger.bollinger_mavg()
        
        current_price = data['close'].iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        current_middle = middle.iloc[-1]
        
        # 밴드폭 계산 (변동성 측정)
        bandwidth = (current_upper - current_lower) / current_middle
        
        # 가격이 밴드를 벗어난 정도 계산
        upper_distance = (current_price - current_upper) / (bandwidth * current_middle)
        lower_distance = (current_lower - current_price) / (bandwidth * current_middle)
        
        # 신호 생성
        if lower_distance > self.entry_threshold:
            # 하단 밴드 아래로 크게 벗어난 경우 매수
            return {
                'direction': 'long',
                'strength': min(lower_distance / 2, 1.0),
                'price': current_price,
                'upper_band': current_upper,
                'lower_band': current_lower,
                'middle_band': current_middle
            }
        elif upper_distance > self.entry_threshold:
            # 상단 밴드 위로 크게 벗어난 경우 매도
            return {
                'direction': 'short',
                'strength': min(upper_distance / 2, 1.0),
                'price': current_price,
                'upper_band': current_upper,
                'lower_band': current_lower,
                'middle_band': current_middle
            }
        elif abs(current_price - current_middle) < (bandwidth * self.exit_threshold):
            # 중간 밴드에 가까워진 경우 포지션 청산
            return {
                'direction': 'exit',
                'strength': 1.0,
                'price': current_price,
                'upper_band': current_upper,
                'lower_band': current_lower,
                'middle_band': current_middle
            }
            
        return {
            'direction': None,
            'strength': 0,
            'price': current_price,
            'upper_band': current_upper,
            'lower_band': current_lower,
            'middle_band': current_middle
        } 