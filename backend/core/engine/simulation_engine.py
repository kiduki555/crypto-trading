from typing import Dict, Optional, Callable
from datetime import datetime
import asyncio
from models.simulation import SimulationResult, Trade
from core.strategies import get_strategy
from core.risk_management import get_risk_manager
from utils.logger import logger

class SimulationEngine:
    def __init__(self,
                 symbol: str,
                 strategy_name: str,
                 risk_name: str,
                 initial_capital: float,
                 strategy_params: Dict,
                 risk_params: Dict,
                 on_update: Optional[Callable[[SimulationResult], None]] = None):
        """
        시뮬레이션 엔진 초기화

        Args:
            symbol: 거래쌍
            strategy_name: 전략 이름
            risk_name: 리스크 관리 전략 이름
            initial_capital: 초기 자본금
            strategy_params: 전략 파라미터
            risk_params: 리스크 관리 파라미터
            on_update: 결과 업데이트 콜백
        """
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.on_update = on_update
        
        # 전략 및 리스크 관리 초기화
        self.strategy = get_strategy(strategy_name, strategy_params)
        self.risk_manager = get_risk_manager(risk_name, risk_params)
        
        # 시뮬레이션 상태
        self.result = SimulationResult(
            symbol=symbol,
            strategy=strategy_name,
            risk_management=risk_name,
            start_time=datetime.now(),
            initial_capital=initial_capital,
            current_capital=initial_capital,
            strategy_params=strategy_params,
            risk_params=risk_params
        )
        
        self.running = False
        self._lock = asyncio.Lock()

    def _calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        """포지션 크기 계산"""
        risk_amount = self.result.current_capital * self.risk_manager.params['risk_per_trade']
        stop_distance = abs(entry_price - stop_loss)
        return risk_amount / stop_distance if stop_distance > 0 else 0

    async def process_update(self, data: Dict):
        """
        새로운 데이터 처리

        Args:
            data: OHLCV 데이터
        """
        async with self._lock:
            try:
                if not self.running:
                    return

                # 전략 신호 계산
                signals = self.strategy.calculate_signals(data)
                
                # 현재 포지션이 없는 경우, 새로운 포지션 진입 검토
                if not self.result.current_position and signals['direction']:
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
                        self.result.current_position = {
                            'type': signals['direction'],
                            'entry_price': entry_price,
                            'size': position_size,
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'entry_time': datetime.now()
                        }
                
                # 현재 포지션이 있는 경우, 청산 조건 검토
                elif self.result.current_position:
                    current_price = data['close']
                    holding_period = (datetime.now() - self.result.current_position['entry_time']).total_seconds() / 60
                    
                    # 미실현 손익 계산
                    if self.result.current_position['type'] == 'long':
                        unrealized_pnl = (current_price - self.result.current_position['entry_price']) * self.result.current_position['size']
                    else:
                        unrealized_pnl = (self.result.current_position['entry_price'] - current_price) * self.result.current_position['size']
                    
                    # 청산 여부 확인
                    should_close, reason = self.risk_manager.should_close_position(
                        self.result.current_position['type'],
                        self.result.current_position['entry_price'],
                        current_price,
                        self.result.current_position['stop_loss'],
                        self.result.current_position['take_profit'],
                        unrealized_pnl,
                        int(holding_period)
                    )
                    
                    if should_close or signals.get('exit_signal'):
                        trade = Trade(
                            timestamp=datetime.now(),
                            symbol=self.symbol,
                            position_type=self.result.current_position['type'],
                            entry_price=self.result.current_position['entry_price'],
                            exit_price=current_price,
                            position_size=self.result.current_position['size'],
                            pnl=unrealized_pnl,
                            stop_loss=self.result.current_position['stop_loss'],
                            take_profit=self.result.current_position['take_profit'],
                            exit_reason=reason or 'signal',
                            holding_period=int(holding_period)
                        )
                        self.result.update_metrics(trade)
                        self.result.current_position = None
                
                # 결과 업데이트 콜백 호출
                if self.on_update:
                    await self.on_update(self.result)

            except Exception as e:
                logger.error(f"Simulation update error: {e}")
                self.result.error_message = str(e)
                self.running = False
                raise

    async def start(self):
        """시뮬레이션 시작"""
        async with self._lock:
            if self.running:
                return
            
            self.running = True
            self.result.status = 'running'
            logger.info(f"Started simulation for {self.symbol}")

    async def stop(self):
        """시뮬레이션 중지"""
        async with self._lock:
            if not self.running:
                return
            
            self.running = False
            self.result.status = 'completed'
            self.result.end_time = datetime.now()
            logger.info(f"Stopped simulation for {self.symbol}") 