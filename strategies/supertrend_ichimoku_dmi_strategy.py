import numpy as np
import pandas as pd
import ta
from backtesting import Strategy
from backtesting.lib import crossover
from strategies.base_strategy import BaseStrategy

class SupertrendIchimokuDmiStrategy(Strategy):
    """
    SuperTrend, Ichimoku Cloud, DMI 및 모멘텀 지표들을 결합한 전략
    """
    
    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        
        # SuperTrend 파라미터
        self.st_ichi_multiplier = params.get('st_ichi_multiplier', 1)
        self.st_ichi_length = params.get('st_ichi_length', 14)
        self.st_dmi_multiplier = params.get('st_dmi_multiplier', 2)
        self.st_dmi_length = params.get('st_dmi_length', 14)
        
        # DMI 파라미터
        self.dmi_length = params.get('dmi_length', 14)
        self.adx_smoothing = params.get('adx_smoothing', 14)
        self.strong_trend = params.get('strong_trend', 20)
        self.weak_trend = params.get('weak_trend', 15)
        
        # Ichimoku 파라미터
        self.conversion_periods = params.get('conversion_periods', 9)
        self.base_periods = params.get('base_periods', 26)
        self.lagging_span2_periods = params.get('lagging_span2_periods', 52)
        self.displacement = params.get('displacement', 26)

        # RSI 파라미터
        self.rsi_length = params.get('rsi_length', 14)
        self.rsi_overbought = params.get('rsi_overbought', 70)
        self.rsi_oversold = params.get('rsi_oversold', 30)

        # Stochastic 파라미터
        self.stoch_k = params.get('stoch_k', 14)
        self.stoch_d = params.get('stoch_d', 3)
        self.stoch_smooth = params.get('stoch_smooth', 3)
        self.stoch_overbought = params.get('stoch_overbought', 80)
        self.stoch_oversold = params.get('stoch_oversold', 20)

        # MACD 파라미터
        self.macd_fast = params.get('macd_fast', 12)
        self.macd_slow = params.get('macd_slow', 26)
        self.macd_signal = params.get('macd_signal', 9)

        # 리스크 관리 파라미터
        self.stop_loss_atr = params.get('stop_loss_atr', 2.0)
        self.take_profit_atr = params.get('take_profit_atr', 4.0)
        self.trailing_stop_atr = params.get('trailing_stop_atr', 2.5)
        self.max_risk_per_trade = params.get('max_risk_per_trade', 0.02)

    def calculate_stochastic(self, high, low, close, k_window, d_window, smooth_window):
        """Stochastic Oscillator 계산"""
        # %K 계산
        lowest_low = np.zeros_like(low)
        highest_high = np.zeros_like(high)
        
        for i in range(k_window - 1, len(close)):
            lowest_low[i] = np.min(low[i-k_window+1:i+1])
            highest_high[i] = np.max(high[i-k_window+1:i+1])
        
        stoch_k = np.zeros_like(close)
        denom = highest_high - lowest_low
        mask = denom != 0
        stoch_k[mask] = 100 * (close[mask] - lowest_low[mask]) / denom[mask]
        
        # %K Smoothing
        smooth_k = np.zeros_like(stoch_k)
        for i in range(smooth_window - 1, len(stoch_k)):
            smooth_k[i] = np.mean(stoch_k[i-smooth_window+1:i+1])
        
        # %D 계산 (Smoothed %K의 이동평균)
        stoch_d = np.zeros_like(smooth_k)
        for i in range(d_window - 1, len(smooth_k)):
            stoch_d[i] = np.mean(smooth_k[i-d_window+1:i+1])
            
        return smooth_k, stoch_d

    def init(self):
        """전략 초기화 및 지표 계산"""
        # SuperTrend 계산
        self.st_ichi, self.dir_ichi = self.I(self.calculate_supertrend, 
            self.data.High, self.data.Low, self.data.Close,
            self.st_ichi_multiplier, self.st_ichi_length)
        
        # RSI 계산
        self.rsi = self.I(ta.momentum.rsi, pd.Series(self.data.Close), window=self.rsi_length)
        
        # ATR 계산
        self.atr = self.I(self.calculate_atr, self.data.High, self.data.Low, self.data.Close, 14)

        # 트레일링 스탑을 위한 변수 초기화
        self.highest_price = self.data.Close[0]
        self.lowest_price = self.data.Close[0]

    def next(self):
        """다음 거래 결정"""
        # 매수 조건: SuperTrend 상향돌파만 사용
        bullish = (
            (self.data.Close[-1] > self.st_ichi[-1]) and      # 현재 가격이 SuperTrend 위
            (self.data.Close[-2] <= self.st_ichi[-2]) and     # 이전 가격이 SuperTrend 아래
            (self.data.Close[-1] > self.data.Close[-2])       # 상승 추세
        )
        
        # 매도 조건: SuperTrend 하향돌파만 사용
        bearish = (
            (self.data.Close[-1] < self.st_ichi[-1]) and      # 현재 가격이 SuperTrend 아래
            (self.data.Close[-2] >= self.st_ichi[-2]) and     # 이전 가격이 SuperTrend 위
            (self.data.Close[-1] < self.data.Close[-2])       # 하락 추세
        )

        # 현재 ATR 값
        current_atr = self.atr[-1]

        # 포지션 진입/청산
        if not self.position:  # 포지션이 없을 때
            # RSI 필터
            rsi_filter = (
                (self.rsi[-1] > 30) and                       # RSI가 30 이상
                (self.rsi[-1] < 70)                           # RSI가 70 이하
            )

            # 진입 크기 계산 (리스크 기반)
            risk_amount = self.equity * self.max_risk_per_trade
            stop_distance = current_atr * self.stop_loss_atr
            position_size = max(0.01, min(1.0, risk_amount / (self.data.Close[-1] * stop_distance)))

            if bullish and rsi_filter:
                self.buy(size=position_size)
                self.highest_price = self.data.Close[-1]
            elif bearish and rsi_filter:
                self.sell(size=position_size)
                self.lowest_price = self.data.Close[-1]
        
        else:  # 포지션이 있을 때
            # 트레일링 스탑 계산
            trailing_distance = current_atr * self.trailing_stop_atr
            take_profit_distance = current_atr * self.take_profit_atr
            
            if self.position.is_long:
                # 롱 포지션 트레일링 스탑
                self.highest_price = max(self.highest_price, self.data.Close[-1])
                if (
                    (self.data.Close[-1] <= (self.highest_price - trailing_distance)) or  # 트레일링 스탑
                    (self.data.Close[-1] < self.st_ichi[-1]) or                          # SuperTrend 하향돌파
                    (self.data.Close[-1] >= self.highest_price + take_profit_distance)    # 이익실현
                ):
                    self.position.close()
            
            elif self.position.is_short:
                # 숏 포지션 트레일링 스탑
                self.lowest_price = min(self.lowest_price, self.data.Close[-1])
                if (
                    (self.data.Close[-1] >= (self.lowest_price + trailing_distance)) or  # 트레일링 스탑
                    (self.data.Close[-1] > self.st_ichi[-1]) or                         # SuperTrend 상향돌파
                    (self.data.Close[-1] <= self.lowest_price - take_profit_distance)    # 이익실현
                ):
                    self.position.close()

    def calculate_supertrend(self, high, low, close, multiplier, length):
        """SuperTrend 지표 계산"""
        # ATR 계산
        tr1 = abs(high - low)
        tr2 = abs(high - np.roll(close, 1))
        tr3 = abs(low - np.roll(close, 1))
        tr = np.maximum.reduce([tr1, tr2, tr3])
        
        # 단순이동평균으로 ATR 계산
        atr = np.zeros_like(close)
        atr[length-1] = np.mean(tr[:length])
        for i in range(length, len(close)):
            atr[i] = (atr[i-1] * (length-1) + tr[i]) / length
        
        # 기본 상하단 밴드 계산
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # SuperTrend 계산
        supertrend = np.zeros_like(close)
        direction = np.zeros_like(close)
        
        # 초기값 설정
        supertrend[0] = upper_band[0]
        direction[0] = 1
        
        # SuperTrend 계산
        for i in range(1, len(close)):
            if close[i-1] <= supertrend[i-1]:
                if close[i] > upper_band[i]:
                    direction[i] = 1
                else:
                    direction[i] = -1
            else:
                if close[i] < lower_band[i]:
                    direction[i] = -1
                else:
                    direction[i] = 1
                    
            if direction[i] == 1:
                supertrend[i] = lower_band[i]
            else:
                supertrend[i] = upper_band[i]
                
        return supertrend, direction

    def calculate_ichimoku(self, high, low):
        """Ichimoku Cloud 지표 계산"""
        # 전환선 (Conversion Line)
        tenkan_sen = np.zeros_like(high)
        kijun_sen = np.zeros_like(high)
        senkou_span_a = np.zeros_like(high)
        senkou_span_b = np.zeros_like(high)
        
        # 전환선 계산
        for i in range(self.conversion_periods - 1, len(high)):
            tenkan_sen[i] = (np.max(high[i-self.conversion_periods+1:i+1]) + 
                           np.min(low[i-self.conversion_periods+1:i+1])) / 2
        
        # 기준선 계산
        for i in range(self.base_periods - 1, len(high)):
            kijun_sen[i] = (np.max(high[i-self.base_periods+1:i+1]) + 
                          np.min(low[i-self.base_periods+1:i+1])) / 2
        
        # 선행스팬 A
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        
        # 선행스팬 B
        for i in range(self.lagging_span2_periods - 1, len(high)):
            senkou_span_b[i] = (np.max(high[i-self.lagging_span2_periods+1:i+1]) + 
                              np.min(low[i-self.lagging_span2_periods+1:i+1])) / 2
        
        # 선행스팬 이동
        senkou_span_a = np.roll(senkou_span_a, self.displacement)
        senkou_span_b = np.roll(senkou_span_b, self.displacement)
        
        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b

    def calculate_dmi(self, high, low, close, length):
        """DMI(Directional Movement Index) 계산"""
        # True Range 계산
        tr1 = abs(high - low)
        tr2 = abs(high - np.roll(close, 1))
        tr3 = abs(low - np.roll(close, 1))
        tr = np.maximum.reduce([tr1, tr2, tr3])
        
        # Directional Movement 계산
        up_move = high - np.roll(high, 1)
        down_move = np.roll(low, 1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed TR and DM 계산
        tr_smooth = np.zeros_like(tr)
        plus_dm_smooth = np.zeros_like(plus_dm)
        minus_dm_smooth = np.zeros_like(minus_dm)
        
        # 첫 번째 값 설정
        tr_smooth[length-1] = np.sum(tr[:length])
        plus_dm_smooth[length-1] = np.sum(plus_dm[:length])
        minus_dm_smooth[length-1] = np.sum(minus_dm[:length])
        
        # Wilder's smoothing
        for i in range(length, len(tr)):
            tr_smooth[i] = tr_smooth[i-1] - (tr_smooth[i-1]/length) + tr[i]
            plus_dm_smooth[i] = plus_dm_smooth[i-1] - (plus_dm_smooth[i-1]/length) + plus_dm[i]
            minus_dm_smooth[i] = minus_dm_smooth[i-1] - (minus_dm_smooth[i-1]/length) + minus_dm[i]
        
        # DI 계산 (0으로 나누는 것 방지)
        plus_di = np.zeros_like(tr_smooth)
        minus_di = np.zeros_like(tr_smooth)
        mask = tr_smooth != 0
        plus_di[mask] = 100 * plus_dm_smooth[mask] / tr_smooth[mask]
        minus_di[mask] = 100 * minus_dm_smooth[mask] / tr_smooth[mask]
        
        # ADX 계산 (0으로 나누는 것 방지)
        dx = np.zeros_like(plus_di)
        sum_di = plus_di + minus_di
        mask = sum_di != 0
        dx[mask] = 100 * np.abs(plus_di[mask] - minus_di[mask]) / sum_di[mask]
        
        adx = np.zeros_like(dx)
        
        # 첫 번째 ADX 값 설정
        adx[2*length-1] = np.mean(dx[length:2*length])
        
        # ADX smoothing
        for i in range(2*length, len(dx)):
            adx[i] = (adx[i-1] * (length-1) + dx[i]) / length
            
        return plus_di, minus_di, adx

    def calculate_atr(self, high, low, close, length):
        """ATR(Average True Range) 계산"""
        tr1 = abs(high - low)
        tr2 = abs(high - np.roll(close, 1))
        tr3 = abs(low - np.roll(close, 1))
        tr = np.maximum.reduce([tr1, tr2, tr3])
        
        atr = np.zeros_like(close)
        atr[length-1] = np.mean(tr[:length])
        
        for i in range(length, len(close)):
            atr[i] = (atr[i-1] * (length-1) + tr[i]) / length
            
        return atr

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SuperTrend, Ichimoku Cloud, DMI 및 모멘텀 지표들을 기반으로 매매 시그널 계산
        """
        # SuperTrend 시그널 계산
        st_ichi, dir_ichi = self.calculate_supertrend(
            df['high'], df['low'], df['close'],
            self.st_ichi_multiplier, self.st_ichi_length
        )
        
        st_dmi, dir_dmi = self.calculate_supertrend(
            df['high'], df['low'], df['close'],
            self.st_dmi_multiplier, self.st_dmi_length
        )
        
        # DMI 지표 계산
        df['dmi_plus'] = ta.trend.dmi_pos(df['high'], df['low'], df['close'], window=self.dmi_length)
        df['dmi_minus'] = ta.trend.dmi_neg(df['high'], df['low'], df['close'], window=self.dmi_length)
        df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=self.dmi_length)
        
        # Ichimoku Cloud 계산
        tenkan, kijun, span_a, span_b = self.calculate_ichimoku(df['high'], df['low'])
        
        # 모멘텀 지표 계산
        rsi, stoch_k, stoch_d, macd_line, macd_signal = self.calculate_momentum_indicators(df)
        
        # 매매 시그널 초기화
        df['signal'] = 0
        
        # 매수 조건
        bullish = (
            (df['close'] > st_ichi) &  # Ichimoku SuperTrend 상향돌파
            (df['close'] > st_dmi) &   # DMI SuperTrend 상향돌파
            (df['dmi_plus'] > df['dmi_minus']) &  # DMI 상승추세
            (df['adx'] > self.strong_trend) &     # 강한 추세
            (tenkan > kijun) &         # 전환선이 기준선 상향돌파
            (df['close'] > span_a) &   # 가격이 구름대 위
            (df['close'] > span_b) &   # 가격이 구름대 위
            (rsi > 50) &               # RSI 상승추세
            (stoch_k > stoch_d) &      # Stochastic 상승추세
            (macd_line > macd_signal)  # MACD 상승추세
        )
        
        # 매도 조건
        bearish = (
            (df['close'] < st_ichi) &  # Ichimoku SuperTrend 하향돌파
            (df['close'] < st_dmi) &   # DMI SuperTrend 하향돌파
            (df['dmi_plus'] < df['dmi_minus']) &  # DMI 하락추세
            (df['adx'] > self.strong_trend) &     # 강한 추세
            (tenkan < kijun) &         # 전환선이 기준선 하향돌파
            (df['close'] < span_a) &   # 가격이 구름대 아래
            (df['close'] < span_b) &   # 가격이 구름대 아래
            (rsi < 50) &               # RSI 하락추세
            (stoch_k < stoch_d) &      # Stochastic 하락추세
            (macd_line < macd_signal)  # MACD 하락추세
        )
        
        df.loc[bullish, 'signal'] = 1
        df.loc[bearish, 'signal'] = -1
        
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        매매 시그널 생성
        """
        df = self.calculate_signals(df)
        return df 