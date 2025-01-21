from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .backtest import Trade

class SimulationResult(BaseModel):
    """시뮬레이션 결과"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "running"  # running, completed, error
    
    # 시뮬레이션 설정
    symbol: str
    strategy: str
    risk_management: str
    start_time: datetime
    end_time: Optional[datetime] = None
    initial_capital: float
    strategy_params: Dict
    risk_params: Dict
    
    # 실시간 시뮬레이션 상태
    current_capital: float
    current_position: Optional[Dict] = None  # 현재 포지션 정보
    total_pnl: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    current_drawdown: float = 0
    max_drawdown: float = 0
    trades: List[Trade] = []
    
    # 추가 메타데이터
    indicators: Optional[Dict] = None
    error_message: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """MongoDB에 저장하기 위한 딕셔너리 변환"""
        return {
            **self.dict(),
            'trades': [trade.dict() for trade in self.trades]
        }

    def update_metrics(self, trade: Trade):
        """새로운 거래 추가 시 지표 업데이트"""
        self.trades.append(trade)
        self.total_trades += 1
        self.total_pnl += trade.pnl
        
        if trade.pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
            
        # 자본금 업데이트
        self.current_capital += trade.pnl
        
        # 드로다운 계산
        peak_capital = max(self.initial_capital, self.current_capital)
        self.current_drawdown = (peak_capital - self.current_capital) / peak_capital
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown) 