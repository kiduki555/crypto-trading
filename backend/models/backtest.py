from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Trade(BaseModel):
    """개별 거래 정보"""
    timestamp: datetime
    symbol: str
    position_type: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    position_size: float
    pnl: float
    stop_loss: float
    take_profit: float
    exit_reason: str  # 'stop_loss', 'take_profit', 'signal'
    holding_period: int  # minutes

class BacktestResult(BaseModel):
    """백테스트 결과"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 백테스트 설정
    symbol: str
    strategy: str
    risk_management: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    strategy_params: Dict
    risk_params: Dict
    
    # 백테스트 결과
    final_capital: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Trade]
    
    # 추가 메타데이터
    indicators: Optional[Dict] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """MongoDB에 저장하기 위한 딕셔너리 변환"""
        return {
            **self.dict(),
            'trades': [trade.dict() for trade in self.trades]
        } 