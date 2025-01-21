from typing import Dict, Optional, List
from datetime import datetime
import asyncio
from models.simulation import SimulationResult
from core.engine.simulation_engine import SimulationEngine
from services.exchange import ExchangeService
from services.database import DatabaseService
from utils.logger import logger

class SimulationService:
    def __init__(self,
                 exchange_service: Optional[ExchangeService] = None,
                 database_service: Optional[DatabaseService] = None):
        """
        시뮬레이션 서비스 초기화

        Args:
            exchange_service: 거래소 서비스 (테스트용)
            database_service: 데이터베이스 서비스 (테스트용)
        """
        self.exchange = exchange_service or ExchangeService()
        self.db = database_service or DatabaseService()
        self.active_simulations: Dict[str, SimulationEngine] = {}

    async def start_simulation(self,
                             symbol: str,
                             strategy: str,
                             risk_management: str,
                             initial_capital: float,
                             strategy_params: Dict,
                             risk_params: Dict,
                             interval: str = '1m') -> str:
        """
        시뮬레이션 시작

        Args:
            symbol: 거래쌍
            strategy: 전략 이름
            risk_management: 리스크 관리 전략 이름
            initial_capital: 초기 자본금
            strategy_params: 전략 파라미터
            risk_params: 리스크 관리 파라미터
            interval: 시간간격

        Returns:
            시뮬레이션 ID
        """
        try:
            # 시뮬레이션 엔진 초기화
            engine = SimulationEngine(
                symbol=symbol,
                strategy_name=strategy,
                risk_name=risk_management,
                initial_capital=initial_capital,
                strategy_params=strategy_params,
                risk_params=risk_params,
                on_update=self._handle_simulation_update
            )
            
            # 시뮬레이션 시작
            await engine.start()
            
            # 결과 저장
            simulation_id = self.db.save_simulation_result(engine.result)
            
            # 활성 시뮬레이션에 추가
            self.active_simulations[simulation_id] = engine
            
            # WebSocket 구독 시작
            await self.exchange.subscribe_to_klines(
                symbol=symbol,
                interval=interval,
                callback=lambda data: self._handle_kline_update(simulation_id, data)
            )
            
            logger.info(f"Started simulation: {simulation_id}")
            return simulation_id

        except Exception as e:
            logger.error(f"Failed to start simulation: {e}")
            raise

    async def stop_simulation(self, simulation_id: str):
        """
        시뮬레이션 중지

        Args:
            simulation_id: 시뮬레이션 ID
        """
        try:
            if simulation_id not in self.active_simulations:
                raise ValueError(f"Simulation not found: {simulation_id}")
            
            engine = self.active_simulations[simulation_id]
            await engine.stop()
            
            # WebSocket 구독 해제
            await self.exchange.unsubscribe_from_klines(simulation_id)
            
            # 결과 업데이트
            self.db.update_simulation_result(simulation_id, {
                'status': 'completed',
                'end_time': datetime.now()
            })
            
            # 활성 시뮬레이션에서 제거
            del self.active_simulations[simulation_id]
            
            logger.info(f"Stopped simulation: {simulation_id}")

        except Exception as e:
            logger.error(f"Failed to stop simulation: {e}")
            raise

    async def _handle_kline_update(self, simulation_id: str, data: Dict):
        """
        K라인 데이터 업데이트 처리

        Args:
            simulation_id: 시뮬레이션 ID
            data: K라인 데이터
        """
        try:
            if simulation_id not in self.active_simulations:
                return
            
            engine = self.active_simulations[simulation_id]
            await engine.process_update(data)

        except Exception as e:
            logger.error(f"Failed to handle kline update: {e}")
            await self.stop_simulation(simulation_id)

    async def _handle_simulation_update(self, result: SimulationResult):
        """
        시뮬레이션 결과 업데이트 처리

        Args:
            result: 시뮬레이션 결과
        """
        try:
            self.db.update_simulation_result(result.id, result.to_dict())
        except Exception as e:
            logger.error(f"Failed to handle simulation update: {e}")

    def get_simulation_result(self, simulation_id: str) -> Optional[SimulationResult]:
        """
        시뮬레이션 결과 조회

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            시뮬레이션 결과
        """
        try:
            result = self.db.get_simulation_result(simulation_id)
            if not result:
                return None
            return SimulationResult(**result)
        except Exception as e:
            logger.error(f"Failed to get simulation result: {e}")
            raise

    def get_simulation_results(self,
                             symbol: Optional[str] = None,
                             strategy: Optional[str] = None,
                             status: Optional[str] = None,
                             limit: int = 100) -> List[SimulationResult]:
        """
        시뮬레이션 결과 목록 조회

        Args:
            symbol: 거래쌍
            strategy: 전략 이름
            status: 상태
            limit: 최대 결과 수

        Returns:
            시뮬레이션 결과 목록
        """
        try:
            results = self.db.get_simulation_results(
                symbol=symbol,
                strategy=strategy,
                status=status,
                limit=limit
            )
            return [SimulationResult(**result) for result in results]
        except Exception as e:
            logger.error(f"Failed to get simulation results: {e}")
            raise

    def delete_simulation_result(self, simulation_id: str):
        """
        시뮬레이션 결과 삭제

        Args:
            simulation_id: 시뮬레이션 ID
        """
        try:
            self.db.delete_simulation_result(simulation_id)
            logger.info(f"Deleted simulation result: {simulation_id}")
        except Exception as e:
            logger.error(f"Failed to delete simulation result: {e}")
            raise 