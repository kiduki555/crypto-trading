from typing import Dict, Optional
from datetime import datetime
from models.backtest import BacktestResult
from core.engine.backtest_engine import BacktestEngine
from services.exchange import ExchangeService
from services.database import DatabaseService
from utils.logger import logger

class BacktestService:
    def __init__(self,
                 exchange_service: Optional[ExchangeService] = None,
                 database_service: Optional[DatabaseService] = None):
        """
        백테스트 서비스 초기화

        Args:
            exchange_service: 거래소 서비스 (테스트용)
            database_service: 데이터베이스 서비스 (테스트용)
        """
        self.exchange = exchange_service or ExchangeService()
        self.db = database_service or DatabaseService()

    async def run_backtest(self,
                          symbol: str,
                          strategy: str,
                          risk_management: str,
                          start_date: datetime,
                          end_date: datetime,
                          initial_capital: float,
                          strategy_params: Dict,
                          risk_params: Dict,
                          interval: str = '1h') -> str:
        """
        백테스트 실행

        Args:
            symbol: 거래쌍
            strategy: 전략 이름
            risk_management: 리스크 관리 전략 이름
            start_date: 시작 날짜
            end_date: 종료 날짜
            initial_capital: 초기 자본금
            strategy_params: 전략 파라미터
            risk_params: 리스크 관리 파라미터
            interval: 시간간격

        Returns:
            백테스트 ID
        """
        try:
            # 과거 데이터 조회
            data = await self.exchange.get_historical_data(
                symbol=symbol,
                interval=interval,
                start_time=start_date,
                end_time=end_date
            )
            
            if data.empty:
                raise ValueError("No historical data available")
            
            # 백테스트 엔진 초기화
            engine = BacktestEngine(
                symbol=symbol,
                strategy_name=strategy,
                risk_name=risk_management,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                strategy_params=strategy_params,
                risk_params=risk_params
            )
            
            # 백테스트 실행
            result = engine.run(data)
            
            # 결과 저장
            backtest_id = self.db.save_backtest_result(result)
            logger.info(f"Completed backtest: {backtest_id}")
            
            return backtest_id

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            raise

    def get_backtest_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """
        백테스트 결과 조회

        Args:
            backtest_id: 백테스트 ID

        Returns:
            백테스트 결과
        """
        try:
            result = self.db.get_backtest_result(backtest_id)
            if not result:
                return None
            return BacktestResult(**result)
        except Exception as e:
            logger.error(f"Failed to get backtest result: {e}")
            raise

    def get_backtest_results(self,
                           symbol: Optional[str] = None,
                           strategy: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> list[BacktestResult]:
        """
        백테스트 결과 목록 조회

        Args:
            symbol: 거래쌍
            strategy: 전략 이름
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 결과 수

        Returns:
            백테스트 결과 목록
        """
        try:
            results = self.db.get_backtest_results(
                symbol=symbol,
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            return [BacktestResult(**result) for result in results]
        except Exception as e:
            logger.error(f"Failed to get backtest results: {e}")
            raise 