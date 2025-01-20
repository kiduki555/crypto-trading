from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

class PositionManager:
    def __init__(self, config: Dict[str, Any]):
        """
        Position Manager 초기화
        
        Args:
            config: 설정 값들
        """
        self.config = config
        self.active_positions: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def open_position(self, order: Dict[str, Any]) -> bool:
        """
        새로운 포지션 오픈
        
        Args:
            order: 주문 정보
        Returns:
            성공 여부
        """
        try:
            position = {
                'id': len(self.active_positions) + 1,
                'entry_time': datetime.now(),
                'entry_price': order['entry_price'],
                'size': order['size'],
                'side': order['side'],
                'stop_loss': order['stop_loss'],
                'take_profit': order['take_profit'],
                'leverage': order['leverage'],
                'status': 'OPEN'
            }
            
            self.active_positions.append(position)
            self.logger.info(f"Position opened: {position}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening position: {str(e)}")
            return False

    def close_position(self, position_id: int, price: float) -> bool:
        """
        포지션 종료
        
        Args:
            position_id: 포지션 ID
            price: 종료 가격
        Returns:
            성공 여부
        """
        try:
            position = self.get_position(position_id)
            if position:
                position['exit_time'] = datetime.now()
                position['exit_price'] = price
                position['status'] = 'CLOSED'
                position['pnl'] = self._calculate_pnl(position, price)
                
                self.logger.info(f"Position closed: {position}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing position: {str(e)}")
            return False

    def get_position(self, position_id: int) -> Optional[Dict[str, Any]]:
        """
        포지션 정보 조회
        
        Args:
            position_id: 포지션 ID
        Returns:
            포지션 정보
        """
        for position in self.active_positions:
            if position['id'] == position_id and position['status'] == 'OPEN':
                return position
        return None

    def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        활성화된 모든 포지션 조회
        
        Returns:
            활성 포지션 리스트
        """
        return [p for p in self.active_positions if p['status'] == 'OPEN']

    def _calculate_pnl(self, position: Dict[str, Any], current_price: float) -> float:
        """
        손익 계산
        
        Args:
            position: 포지션 정보
            current_price: 현재가
        Returns:
            손익률
        """
        if position['side'] == 'long':
            return ((current_price - position['entry_price']) / position['entry_price']) * 100 * position['leverage']
        else:
            return ((position['entry_price'] - current_price) / position['entry_price']) * 100 * position['leverage']
