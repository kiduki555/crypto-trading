from typing import Dict, Type
from .base_strategy import BaseStrategy
from .rsi_strategy import RSIStrategy
from .bollinger_strategy import BollingerStrategy
from .macd_strategy import MACDStrategy

# 사용 가능한 전략 목록
AVAILABLE_STRATEGIES: Dict[str, Type[BaseStrategy]] = {
    'rsi': RSIStrategy,
    'bollinger': BollingerStrategy,
    'macd': MACDStrategy
}

def get_strategy(name: str, params: Dict) -> BaseStrategy:
    """
    전략 인스턴스 생성
    
    Args:
        name: 전략 이름
        params: 전략 파라미터
        
    Returns:
        전략 인스턴스
        
    Raises:
        ValueError: 존재하지 않는 전략
    """
    if name not in AVAILABLE_STRATEGIES:
        raise ValueError(f"Strategy not found: {name}")
    
    strategy_class = AVAILABLE_STRATEGIES[name]
    return strategy_class(params) 