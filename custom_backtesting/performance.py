from typing import Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from backtesting.lib import plot_heatmaps

class PerformanceAnalyzer:
    def __init__(self, results: Dict[str, Any]):
        """
        성능 분석기 초기화
        
        Args:
            results: 백테스트 결과
        """
        self.results = results
        self.trades_df = pd.DataFrame(results['trades'])
        
    def calculate_metrics(self) -> Dict[str, Any]:
        """상세 성능 지표 계산"""
        metrics = {
            'total_return_pct': self.results['total_return'],
            'win_rate': self.results.get('win_rate', 0),
            'total_trades': self.results['total_trades'],
            'profit_factor': self._calculate_profit_factor(),
            'sharpe_ratio': self._calculate_sharpe_ratio(),
            'max_drawdown': self._calculate_max_drawdown(),
            'avg_trade_duration': self.results.get('avg_trade_duration', pd.Timedelta(0))
        }
        
        return metrics
        
    def plot_equity_curve(self) -> None:
        """자본금 변화 곡선 플롯"""
        if self.trades_df.empty:
            return
            
        plt.figure(figsize=(12, 6))
        
        # 누적 수익 계산
        equity_curve = self._calculate_equity_curve()
        
        plt.plot(equity_curve.index, equity_curve.values)
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Account Value')
        plt.grid(True)
        plt.show()
        
    def plot_drawdown(self) -> None:
        """드로다운 플롯"""
        if self.trades_df.empty:
            return
            
        equity_curve = self._calculate_equity_curve()
        drawdown = self._calculate_drawdown_series(equity_curve)
        
        plt.figure(figsize=(12, 6))
        plt.plot(drawdown.index, drawdown.values)
        plt.title('Drawdown')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.grid(True)
        plt.show()
        
    def plot_monthly_returns(self) -> None:
        """월별 수익률 히트맵"""
        if self.trades_df.empty:
            return
        
        # 월별 수익률 계산
        monthly_returns = self._calculate_monthly_returns()
        
        # backtesting 패키지의 plot_heatmaps 사용
        plot_heatmaps(monthly_returns, title='Monthly Returns (%)')

    def _calculate_equity_curve(self) -> pd.Series:
        """자본금 변화 곡선 계산"""
        equity = self.results['initial_balance']
        equity_curve = []
        dates = []
        
        for trade in self.trades_df.itertuples():
            equity += trade.pnl - trade.commission
            equity_curve.append(equity)
            dates.append(trade.exit_time)
            
        return pd.Series(equity_curve, index=dates)

    def _calculate_profit_factor(self) -> float:
        """수익 팩터 계산"""
        if self.trades_df.empty:
            return 0
            
        gross_profit = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(self.trades_df[self.trades_df['pnl'] <= 0]['pnl'].sum())
        
        return gross_profit / gross_loss if gross_loss != 0 else float('inf')

    def _calculate_sharpe_ratio(self) -> float:
        """샤프 비율 계산"""
        if self.trades_df.empty:
            return 0
            
        returns = self.trades_df['pnl'] / self.results['initial_balance']
        return np.sqrt(252) * returns.mean() / returns.std() if returns.std() != 0 else 0

    def _calculate_max_drawdown(self) -> float:
        """최대 드로다운 계산"""
        equity_curve = self._calculate_equity_curve()
        return self._calculate_drawdown_series(equity_curve).min()

    def _calculate_drawdown_series(self, equity_curve: pd.Series) -> pd.Series:
        """드로다운 시리즈 계산"""
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max * 100
        return drawdown

    def _calculate_monthly_returns(self) -> pd.Series:
        """월별 수익률 계산"""
        if self.trades_df.empty:
            return pd.Series()
            
        self.trades_df['month'] = self.trades_df['exit_time'].dt.to_period('M')
        monthly_returns = self.trades_df.groupby('month')['pnl'].sum()
        monthly_returns = monthly_returns / self.results['initial_balance'] * 100
        
        return monthly_returns

    def _validate_signals(self, signals: List[Dict[str, Any]]) -> str:
        """전략 신호 검증
        
        Args:
            signals: 각 전략에서 생성된 신호 리스트
        Returns:
            합의된 신호 ('long', 'short' 또는 None)
            
        Note:
            - 전략들의 신호를 집계하여 다수결 원칙으로 최종 신호 결정
            - 전략 개수별 threshold 기준:
              1개: 해당 신호 그대로 채택
              2개: 두 전략이 동일한 신호일 때만 채택
              3개 이상: 과반수(절반 초과) 이상일 때 채택
        """
        total_strategies = len(signals)
        long_count = sum(1 for signal in signals if signal.get('direction') == 'long')
        short_count = sum(1 for signal in signals if signal.get('direction') == 'short')
        
        # 전략 개수별 threshold 설정
        if total_strategies == 1:
            if long_count == 1:
                return 'long'
            elif short_count == 1:
                return 'short'
        elif total_strategies == 2:
            if long_count == 2:
                return 'long'
            elif short_count == 2:
                return 'short'
        else:
            # 3개 이상일 경우 과반수(절반 초과) 기준 적용
            threshold = total_strategies / 2
            if long_count > threshold:
                return 'long'
            elif short_count > threshold:
                return 'short'
        
        return None

    def run(self, data: pd.DataFrame) -> Dict[str, Any]:
        try:
            self.balance = self.initial_balance
            self.positions = []
            self.trades = []
            
            for index, row in data.iterrows():
                signals = [
                    strategy.calculate_signals(data.loc[:index])
                    for strategy in self.strategies
                ]
                
                # 신호 로깅 추가
                self.logger.debug(f"Time: {index}")
                for i, signal in enumerate(signals):
                    self.logger.debug(f"Strategy {i+1} signal: {signal}")
                
                consensus_signal = self._validate_signals(signals)
                self.logger.debug(f"Consensus signal: {consensus_signal}")
                
                self._update_positions(row)
                
                if consensus_signal and not self.positions:
                    self.logger.info(f"Opening {consensus_signal} position at {index}")
                    self._open_position(consensus_signal, row, index)
            
            if self.positions:
                self._close_position(data.iloc[-1], data.index[-1], "End of Period")
            
            return self._generate_results()
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {str(e)}")
            raise
