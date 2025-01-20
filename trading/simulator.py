from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.dummy_account import DummyAccount
from strategies.base_strategy import BaseStrategy
from risk_management.base_risk import BaseRiskManager

class TradingSimulator:
    def __init__(self, db_path: str, strategies: List[BaseStrategy],
                 risk_manager: BaseRiskManager, account_id: Optional[str] = None,
                 commission_rate: float = 0.001):
        """
        거래 시뮬레이터
        
        Args:
            db_path: 데이터베이스 경로
            strategies: 거래 전략 리스트
            risk_manager: 리스크 관리자
            account_id: 더미 계정 ID (None인 경우 새로 생성)
            commission_rate: 수수료율 (기본값: 0.1%)
        """
        self.account = DummyAccount(db_path, account_id)
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.commission_rate = commission_rate
        self.logger = logging.getLogger(__name__)
        
        # 캔들스틱 데이터 저장용 딕셔너리
        self.ohlcv_data = {
            'timestamp': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': []
        }
        
    def initialize_account(self, initial_balance: float) -> bool:
        """계정 초기화"""
        return self.account.create_account(initial_balance)
        
    def process_market_data(self, market_data: Dict[str, Any]) -> None:
        """
        실시간 시장 데이터 처리
        
        Args:
            market_data: {
                'symbol': str,
                'timestamp': int,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': float
            }
        """
        # 시장 데이터 로깅
        self.logger.info(
            f"[{market_data['symbol']}] "
            f"Price: {market_data['close']:.2f} | "
            f"Volume: {market_data['volume']:.3f} | "
            f"O: {market_data['open']:.2f} "
            f"H: {market_data['high']:.2f} "
            f"L: {market_data['low']:.2f} "
            f"C: {market_data['close']:.2f}"
        )
        
        # 캔들스틱 데이터 업데이트
        for key in self.ohlcv_data:
            self.ohlcv_data[key].append(market_data[key])
        
        # 최근 100개 데이터만 유지
        if len(self.ohlcv_data['timestamp']) > 100:
            for key in self.ohlcv_data:
                self.ohlcv_data[key] = self.ohlcv_data[key][-100:]
        
        # DataFrame 생성
        df = pd.DataFrame(self.ohlcv_data)
        
        # 각 전략별 신호 수집
        signals = []
        for strategy in self.strategies:
            strategy_name = strategy.__class__.__name__
            signal = strategy.calculate_signals(df)
            
            if signal['direction'] is not None:
                self.logger.info(
                    f"[{strategy_name}] Signal: {signal['direction']} | "
                    f"Strength: {signal.get('strength', 0):.2f}"
                )
                signals.append(signal)
        
        # 종합 신호 결정 (과반수 기준)
        final_direction = self._combine_signals(signals)
        if final_direction is not None:
            self.logger.info(f"Combined Signal: {final_direction}")
            
            # 현재 포지션 확인
            positions = self.account.get_positions()
            current_position = next(
                (p for p in positions if p['symbol'] == market_data['symbol']),
                None
            )
            
            # 현재 포지션 로깅
            if current_position:
                self.logger.info(
                    f"Current Position: {current_position['direction']} | "
                    f"Size: {current_position['position_size']:.4f} | "
                    f"Entry: {current_position['entry_price']:.2f} | "
                    f"PnL: {current_position['unrealized_pnl']:.2f}"
                )
            
            # 리스크 관리 적용
            risk_params = self.risk_manager.calculate_risk_params(
                {'direction': final_direction, 'strength': 1.0},
                market_data['close'],
                self.account.get_balance()
            )
            
            # 거래 실행
            self._execute_trade(
                market_data['symbol'],
                {'direction': final_direction, 'strength': 1.0},
                risk_params,
                market_data['close'],
                current_position,
                'combined'
            )
            
    def _combine_signals(self, signals: List[Dict[str, Any]]) -> Optional[str]:
        """
        여러 전략의 신호를 하나로 통합
        
        Args:
            signals: 각 전략의 신호 목록
        Returns:
            최종 매매 방향
        """
        if not signals:
            return None
            
        long_count = sum(1 for signal in signals if signal.get('direction') == 'long')
        short_count = sum(1 for signal in signals if signal.get('direction') == 'short')
        
        # 과반수 기준으로 결정 (전체 전략 수의 절반 이상)
        threshold = len(self.strategies) / 2
        
        if long_count > threshold:
            return 'long'
        elif short_count > threshold:
            return 'short'
        elif any(signal.get('direction') == 'exit' for signal in signals):
            return 'exit'
        return None
        
    def _execute_trade(self, symbol: str, signal: Dict[str, Any],
                      risk_params: Dict[str, Any], current_price: float,
                      current_position: Optional[Dict[str, Any]],
                      strategy_name: str) -> None:
        """거래 실행"""
        # 포지션 종료 조건 확인
        if current_position and (
            signal['direction'] == 'exit' or
            signal['direction'] != current_position['direction']
        ):
            # 청산 수수료 계산
            commission = current_position['position_size'] * current_price * self.commission_rate
            
            # 손익 계산
            realized_pnl = (
                (current_price - current_position['entry_price'])
                * current_position['position_size']
            )
            if current_position['direction'] == 'short':
                realized_pnl *= -1
            
            # 거래 기록
            self.account.record_trade(
                symbol=symbol,
                direction='exit',
                quantity=current_position['position_size'],
                price=current_price,
                realized_pnl=realized_pnl,
                commission=commission,
                strategy=strategy_name
            )
            
            # 잔고 업데이트
            new_balance = (
                self.account.get_balance()
                + realized_pnl
                - commission
            )
            self.account.update_balance(new_balance)
            
            # 포지션 제거
            self.account.update_position(
                symbol=symbol,
                position_size=0,
                entry_price=0,
                current_price=current_price,
                direction='none',
                strategy=strategy_name
            )
            
            self.logger.info(
                f"[{strategy_name}] Position closed: {symbol}, "
                f"PnL: {realized_pnl:.2f}"
            )
            
        # 새로운 포지션 진입
        if signal['direction'] in ['long', 'short'] and (
            not current_position or
            current_position['position_size'] == 0
        ):
            # 포지션 크기 계산
            position_size = risk_params['position_size']
            
            # 진입 수수료 계산
            commission = position_size * current_price * self.commission_rate
            
            # 필요한 증거금 확인
            required_margin = position_size * current_price * risk_params['margin_ratio']
            
            if required_margin + commission > self.account.get_balance():
                self.logger.warning(
                    f"[{strategy_name}] Insufficient balance for new position"
                )
                return
                
            # 거래 기록
            self.account.record_trade(
                symbol=symbol,
                direction=signal['direction'],
                quantity=position_size,
                price=current_price,
                realized_pnl=None,
                commission=commission,
                strategy=strategy_name
            )
            
            # 잔고 업데이트
            new_balance = self.account.get_balance() - commission
            self.account.update_balance(new_balance)
            
            # 포지션 업데이트
            self.account.update_position(
                symbol=symbol,
                position_size=position_size,
                entry_price=current_price,
                current_price=current_price,
                direction=signal['direction'],
                strategy=strategy_name
            )
            
            self.logger.info(
                f"[{strategy_name}] New position: {symbol}, "
                f"{signal['direction']}, Size: {position_size:.4f}, "
                f"Price: {current_price:.2f}"
            ) 