from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from strategies.base_strategy import BaseStrategy
from risk_management.base_risk import BaseRiskManagement

class TradingExecutor:
    def __init__(self, 
                 strategies: List[BaseStrategy],
                 risk_manager: BaseRiskManagement,
                 config: Dict[str, Any]):
        """
        Trading Executor 초기화
        
        Args:
            strategies: 사용할 전략 리스트
            risk_manager: 리스크 관리 모듈
            config: 설정 값들
        """
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.config = config
        self.position = None
        self.logger = logging.getLogger(__name__)

    def process_market_data(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        시장 데이터를 처리하고 매매 신호 생성
        
        Args:
            market_data: OHLCV 데이터
        Returns:
            매매 주문 정보 또는 None
        """
        try:
            # 전략 시그널 수집
            signals = [strategy.calculate_signals(market_data) for strategy in self.strategies]
            
            # 시그널 검증
            consensus_signal = self._validate_signals(signals)
            
            if consensus_signal:
                # 포지션 크기 계산
                position_size = self._calculate_position_size(market_data)
                
                # 리스크 파라미터 계산
                stop_loss, take_profit, leverage = self.risk_manager.calculate_risk_params(
                    market_data['close'],
                    position_size
                )
                
                return self._create_order(
                    signal=consensus_signal,
                    size=position_size,
                    risk_params=(stop_loss, take_profit, leverage),
                    price=market_data['close']
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing market data: {str(e)}")
            return None

    def _validate_signals(self, signals: List[Dict[str, Any]]) -> Optional[str]:
        """
        여러 전략의 시그널을 검증
        
        Args:
            signals: 각 전략의 시그널 리스트
        Returns:
            검증된 시그널 방향 ('long', 'short', None)
        """
        long_count = sum(1 for signal in signals if signal.get('direction') == 'long')
        short_count = sum(1 for signal in signals if signal.get('direction') == 'short')
        
        # 3개 이상의 전략에서 동일한 시그널이 발생한 경우
        if long_count >= 3:
            return 'long'
        elif short_count >= 3:
            return 'short'
        return None

    def _calculate_position_size(self, market_data: Dict[str, Any]) -> float:
        """
        적정 포지션 크기 계산
        
        Args:
            market_data: 시장 데이터
        Returns:
            포지션 크기
        """
        account_balance = self.config.get('account_balance', 0)
        risk_per_trade = self.config.get('risk_per_trade', 0.01)  # 1%
        
        return account_balance * risk_per_trade

    def _create_order(self, 
                     signal: str, 
                     size: float, 
                     risk_params: Tuple[float, float, float],
                     price: float) -> Dict[str, Any]:
        """
        주문 생성
        
        Args:
            signal: 매매 방향
            size: 포지션 크기
            risk_params: (스탑로스, 익절가, 레버리지)
            price: 현재가
        Returns:
            주문 정보
        """
        stop_loss, take_profit, leverage = risk_params
        
        return {
            'type': 'market',
            'side': signal,
            'size': size,
            'leverage': leverage,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_price': price,
            'timestamp': datetime.now().isoformat()
        }
