from typing import Dict, Type
from .base_risk import BaseRiskManagement
from .fixed_risk import FixedRiskManagement
from .atr_risk import ATRRiskManagement
from .base_risk_manager import BaseRiskManager
from .basic_risk_manager import BasicRiskManager

# 사용 가능한 리스크 관리 전략 목록
AVAILABLE_RISK_MANAGERS: Dict[str, Type[BaseRiskManager]] = {
    'fixed': FixedRiskManagement,
    'atr': ATRRiskManagement,
    'basic': BasicRiskManager
}

def get_risk_manager(name: str, params: Dict) -> BaseRiskManager:
    """
    리스크 관리자 인스턴스 생성
    
    Args:
        name: 리스크 관리 전략 이름
        params: 리스크 관리 파라미터
        
    Returns:
        리스크 관리자 인스턴스
        
    Raises:
        ValueError: 존재하지 않는 리스크 관리 전략
    """
    if name not in AVAILABLE_RISK_MANAGERS:
        raise ValueError(f"Risk manager not found: {name}")
    
    risk_manager_class = AVAILABLE_RISK_MANAGERS[name]
    return risk_manager_class(params) 