from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from strategies.base_strategy import BaseStrategy
from risk_management.base_risk import BaseRiskManagement
from backtesting import Backtest, Strategy

class Backtester:
    def __init__(self,
                 strategies: List[BaseStrategy],
                 risk_manager: BaseRiskManagement,
                 initial_balance: float = 10000,
                 commission: float = 0.0004):  # 0.04% per trade
        """
        백테스터 초기화
        
        Args:
            strategies: 전략 리스트 (BaseStrategy 인스턴스의 리스트)
            risk_manager: 리스크 관리자 (BaseRiskManagement 인스턴스)
            initial_balance: 초기 잔고 (float)
            commission: 거래 수수료 (float, 기본값: 0.0004)
        """
        # 전략, 리스크 관리자, 초기 잔고 및 수수료 설정
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.initial_balance = initial_balance
        self.commission = commission
        self.balance = initial_balance  # 현재 잔고 초기화
        self.positions = []  # 현재 열려 있는 포지션 리스트
        self.trades = []  # 거래 기록 리스트
        self.logger = logging.getLogger(__name__)  # 로거 초기화

    def run(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        백테스트 실행
        
        Args:
            data: OHLCV 데이터 (pandas DataFrame)
        Returns:
            백테스트 결과 (딕셔너리 형태)
        """
        try:
            # Backtest 인스턴스 생성
            bt = Backtest(data, self.strategies[0], cash=self.initial_balance, commission=self.commission)
            # 백테스트 실행
            stats = bt.run()
            # 결과 반환
            return stats._asdict()
        except Exception as e:
            self.logger.error(f"Error in backtest: {str(e)}")
            raise

    def _validate_signals(self, signals: List[Dict[str, Any]]) -> str:
        """전략 신호 검증
        
        Args:
            signals: 각 전략에서 생성된 신호 리스트
        Returns:
            합의된 신호 ('long', 'short' 또는 None)
            
        Note:
            - 전략들의 신호를 집계하여 다수결 원칙으로 최종 신호 결정
            - 과반수 이상의 전략이 같은 방향의 신호를 생성할 때 해당 신호 채택
        """
        long_count = sum(1 for signal in signals if signal.get('direction') == 'long')
        short_count = sum(1 for signal in signals if signal.get('direction') == 'short')
        
        # 과반수 기준으로 변경 (전체 전략 수의 절반 이상)
        threshold = len(self.strategies) / 2
        
        if long_count > threshold:
            return 'long'
        elif short_count > threshold:
            return 'short'
        return None

    def _open_position(self, signal: str, data: pd.Series, timestamp: datetime):
        """새로운 포지션 진입
        
        Args:
            signal: 진입할 포지션의 신호 ('long' 또는 'short')
            data: 현재 시점의 OHLCV 데이터 (pandas Series)
            timestamp: 포지션 진입 시각 (datetime)
        """
        position_size = self.balance * self.risk_manager.risk_per_trade  # 포지션 크기 계산
        entry_price = data['close']  # 진입 가격
        
        # 리스크 파라미터 계산
        stop_loss, take_profit, leverage = self.risk_manager.calculate_risk_params(
            entry_price,
            position_size
        )
        
        # 수수료 계산
        commission = position_size * self.commission
        self.balance -= commission  # 잔고에서 수수료 차감
        
        # 포지션 정보 저장
        position = {
            'type': signal,
            'entry_price': entry_price,
            'size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'leverage': leverage,
            'entry_time': timestamp,
            'entry_commission': commission
        }
        
        # 포지션 진입 정보 로깅
        self.logger.info(
            f"Opening {signal.upper()} position at {timestamp}:\n"
            f"Entry Price: {entry_price:.2f}\n"
            f"Position Size: {position_size:.2f}\n"
            f"Leverage: {leverage}x\n"
            f"Stop Loss: {stop_loss:.2f} ({((stop_loss - entry_price) / entry_price * 100):.2f}%)\n"
            f"Take Profit: {take_profit:.2f} ({((take_profit - entry_price) / entry_price * 100):.2f}%)\n"
            f"Commission: {commission:.2f}"
        )
        
        self.positions.append(position)  # 포지션 리스트에 추가

    def _update_positions(self, data: pd.Series):
        """포지션 업데이트 및 청산 조건 확인
        
        Args:
            data: 현재 시점의 OHLCV 데이터 (pandas Series)
        """
        if not self.positions:  # 열려 있는 포지션이 없으면 종료
            return
            
        position = self.positions[0]  # 현재는 단일 포지션만 지원
        current_price = data['close']  # 현재 가격
        
        # 스탑로스/익절 확인
        if position['type'] == 'long':
            if current_price <= position['stop_loss']:
                self._close_position(data, data.name, "Stop Loss")  # 스탑로스에 도달 시 청산
            elif current_price >= position['take_profit']:
                self._close_position(data, data.name, "Take Profit")  # 익절에 도달 시 청산
        else:  # short
            if current_price >= position['stop_loss']:
                self._close_position(data, data.name, "Stop Loss")  # 스탑로스에 도달 시 청산
            elif current_price <= position['take_profit']:
                self._close_position(data, data.name, "Take Profit")  # 익절에 도달 시 청산

    def _close_position(self, data: pd.Series, timestamp: datetime, reason: str):
        """포지션 청산
        
        Args:
            data: 현재 시점의 OHLCV 데이터 (pandas Series)
            timestamp: 포지션 청산 시각 (datetime)
            reason: 청산 사유 (str)
        """
        position = self.positions[0]  # 청산할 포지션 정보
        exit_price = data['close']  # 청산 가격
        
        # PnL 계산
        if position['type'] == 'long':
            pnl = (exit_price - position['entry_price']) / position['entry_price']  # 롱 포지션의 PnL
        else:
            pnl = (position['entry_price'] - exit_price) / position['entry_price']  # 숏 포지션의 PnL
            
        pnl *= position['size'] * position['leverage']  # 최종 PnL 계산
        
        # 수수료 계산
        exit_commission = position['size'] * self.commission
        total_commission = position['entry_commission'] + exit_commission  # 총 수수료
        
        # 잔고 업데이트
        self.balance += position['size'] + pnl - exit_commission
        
        # 포지션 청산 정보 로깅
        price_change_pct = ((exit_price - position['entry_price']) / position['entry_price'] * 100)
        price_change_pct = price_change_pct if position['type'] == 'long' else -price_change_pct
        
        self.logger.info(
            f"Closing {position['type'].upper()} position at {timestamp} - {reason}:\n"
            f"Entry Price: {position['entry_price']:.2f}\n"
            f"Exit Price: {exit_price:.2f}\n"
            f"Price Change: {price_change_pct:.2f}%\n"
            f"Position Size: {position['size']:.2f}\n"
            f"Leverage: {position['leverage']}x\n"
            f"PnL: {pnl:.2f} ({(pnl / position['size'] * 100):.2f}%)\n"
            f"Total Commission: {total_commission:.2f}\n"
            f"Position Duration: {timestamp - position['entry_time']}"
        )
        
        # 거래 기록 저장
        trade = {
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'type': position['type'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'size': position['size'],
            'pnl': pnl,
            'commission': total_commission,
            'reason': reason
        }
        
        self.trades.append(trade)  # 거래 기록 리스트에 추가
        self.positions = []  # 포지션 리스트 초기화

    def _generate_results(self) -> Dict[str, Any]:
        """백테스트 결과 생성
        
        Returns:
            백테스트 결과 (딕셔너리 형태)
        """
        if not self.trades:  # 거래가 없을 경우 기본 결과 반환
            return {
                'initial_balance': self.initial_balance,
                'final_balance': self.balance,
                'total_return': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_commission': 0,
                'total_pnl': 0,
                'trades': [],
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_trade_duration': pd.Timedelta(0)
            }
            
        trades_df = pd.DataFrame(self.trades)  # 거래 기록을 DataFrame으로 변환
        
        # 결과 계산
        results = {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return': (self.balance - self.initial_balance) / self.initial_balance * 100,
            'total_trades': len(self.trades),
            'winning_trades': len(trades_df[trades_df['pnl'] > 0]),
            'losing_trades': len(trades_df[trades_df['pnl'] <= 0]),
            'total_commission': trades_df['commission'].sum(),
            'total_pnl': trades_df['pnl'].sum(),
            'trades': self.trades,
            'win_rate': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) * 100,
            'avg_win': trades_df[trades_df['pnl'] > 0]['pnl'].mean() if len(trades_df[trades_df['pnl'] > 0]) > 0 else 0,
            'avg_loss': trades_df[trades_df['pnl'] <= 0]['pnl'].mean() if len(trades_df[trades_df['pnl'] <= 0]) > 0 else 0,
            'largest_win': trades_df['pnl'].max(),
            'largest_loss': trades_df['pnl'].min(),
            'avg_trade_duration': (trades_df['exit_time'] - trades_df['entry_time']).mean()
        }
            
        return results  # 최종 결과 반환
