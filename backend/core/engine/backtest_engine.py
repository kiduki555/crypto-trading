from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from models.backtest import BacktestResult, Trade
from core.strategies import get_strategy
from core.risk_management import get_risk_manager
from utils.logger import logger

class BacktestEngine:
    def __init__(self,
                 symbol: str,
                 strategy_name: str,
                 risk_name: str,
                 start_date: datetime,
                 end_date: datetime,
                 initial_capital: float,
                 strategy_params: Dict,
                 risk_params: Dict):
        """
        백테스트 엔진 초기화

        Args:
            symbol: 거래쌍
            strategy_name: 전략 이름
            risk_name: 리스크 관리 전략 이름
            start_date: 시작 날짜
            end_date: 종료 날짜
            initial_capital: 초기 자본금
            strategy_params: 전략 파라미터
            risk_params: 리스크 관리 파라미터
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # 전략 및 리스크 관리 초기화
        self.strategy = get_strategy(strategy_name, strategy_params)
        self.risk_manager = get_risk_manager(risk_name, risk_params)
        
        # 거래 기록
        self.trades: List[Trade] = []
        self.current_position = None
        
        # 성과 지표
        self.peak_capital = initial_capital
        self.max_drawdown = 0
        self.returns = []

    def _update_metrics(self, trade: Trade):
        """거래 후 지표 업데이트"""
        self.trades.append(trade)
        self.current_capital += trade.pnl
        
        # 최대 손실폭 업데이트
        self.peak_capital = max(self.peak_capital, self.current_capital)
        current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        # 수익률 기록
        self.returns.append(trade.pnl / self.initial_capital)

    def _calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """포지션 크기 계산"""
        risk_amount = self.current_capital * self.risk_manager.params['risk_per_trade']
        stop_distance = abs(entry_price - stop_loss)
        return risk_amount / stop_distance if stop_distance > 0 else 0

    def run(self, data: pd.DataFrame) -> BacktestResult:
        """
        백테스트 실행

        Args:
            data: OHLCV 데이터

        Returns:
            백테스트 결과
        """
        try:
            for index, row in data.iterrows():
                # 전략 신호 계산
                signals = self.strategy.calculate_signals(data.loc[:index])
                
                # 현재 포지션이 없는 경우, 새로운 포지션 진입 검토
                if not self.current_position and signals['direction']:
                    entry_price = signals['entry_price']
                    stop_loss = self.risk_manager.calculate_stop_loss(
                        entry_price,
                        signals['direction'],
                        signals.get('volatility')
                    )
                    take_profit = self.risk_manager.calculate_take_profit(
                        entry_price,
                        signals['direction'],
                        stop_loss
                    )
                    
                    position_size = self._calculate_position_size(entry_price, stop_loss)
                    if position_size > 0:
                        self.current_position = {
                            'type': signals['direction'],
                            'entry_price': entry_price,
                            'size': position_size,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'entry_time': index
                        }
                
                # 현재 포지션이 있는 경우, 청산 조건 검토
                elif self.current_position:
                    current_price = row['close']
                    holding_period = (index - self.current_position['entry_time']).total_seconds() / 60
                    
                    # 미실현 손익 계산
                    if self.current_position['type'] == 'long':
                        unrealized_pnl = (current_price - self.current_position['entry_price']) * self.current_position['size']
                    else:
                        unrealized_pnl = (self.current_position['entry_price'] - current_price) * self.current_position['size']
                    
                    # 청산 여부 확인
                    should_close, reason = self.risk_manager.should_close_position(
                        self.current_position['type'],
                        self.current_position['entry_price'],
                        current_price,
                        self.current_position['stop_loss'],
                        self.current_position['take_profit'],
                        unrealized_pnl,
                        int(holding_period)
                    )
                    
                    if should_close or signals.get('exit_signal'):
                        trade = Trade(
                            timestamp=index,
                            symbol=self.symbol,
                            position_type=self.current_position['type'],
                            entry_price=self.current_position['entry_price'],
                            exit_price=current_price,
                            position_size=self.current_position['size'],
                            pnl=unrealized_pnl,
                            stop_loss=self.current_position['stop_loss'],
                            take_profit=self.current_position['take_profit'],
                            exit_reason=reason or 'signal',
                            holding_period=int(holding_period)
                        )
                        self._update_metrics(trade)
                        self.current_position = None

            # 결과 생성
            total_pnl = sum(trade.pnl for trade in self.trades)
            winning_trades = sum(1 for trade in self.trades if trade.pnl > 0)
            
            return BacktestResult(
                symbol=self.symbol,
                strategy=self.strategy.name,
                risk_management=self.risk_manager.name,
                start_date=self.start_date,
                end_date=self.end_date,
                initial_capital=self.initial_capital,
                final_capital=self.current_capital,
                strategy_params=self.strategy.params,
                risk_params=self.risk_manager.params,
                total_pnl=total_pnl,
                total_trades=len(self.trades),
                winning_trades=winning_trades,
                losing_trades=len(self.trades) - winning_trades,
                win_rate=winning_trades / len(self.trades) if self.trades else 0,
                max_drawdown=self.max_drawdown,
                sharpe_ratio=self._calculate_sharpe_ratio(),
                trades=self.trades,
                indicators=self.strategy.get_indicators(data)
            )

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            raise

    def _calculate_sharpe_ratio(self) -> float:
        """샤프 비율 계산"""
        if not self.returns:
            return 0
        
        returns_array = np.array(self.returns)
        excess_returns = returns_array - 0.02 / 252  # 2% 연간 무위험 수익률 가정
        
        if len(excess_returns) < 2:
            return 0
            
        return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns, ddof=1) 