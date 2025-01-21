from typing import List, Optional, Dict
from datetime import datetime
from pymongo.database import Database
from models.backtest import BacktestResult
from models.simulation import SimulationResult
from utils.db import MongoDB
from utils.logger import logger

class DatabaseService:
    def __init__(self, db: Optional[Database] = None):
        """
        데이터베이스 서비스 초기화

        Args:
            db: MongoDB 데이터베이스 인스턴스 (테스트용)
        """
        self.db = db or MongoDB.get_instance().db
        self._ensure_indexes()

    def _ensure_indexes(self):
        """인덱스 생성"""
        try:
            # 백테스트 컬렉션 인덱스
            self.db.backtest_results.create_index([
                ("symbol", 1),
                ("strategy", 1),
                ("created_at", -1)
            ])

            # 시뮬레이션 컬렉션 인덱스
            self.db.simulation_results.create_index([
                ("symbol", 1),
                ("strategy", 1),
                ("status", 1),
                ("created_at", -1)
            ])
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            raise

    # 백테스트 관련 메서드
    def save_backtest_result(self, result: BacktestResult) -> str:
        """
        백테스트 결과 저장

        Args:
            result: 백테스트 결과 객체

        Returns:
            저장된 문서의 ID
        """
        try:
            data = result.to_dict()
            self.db.backtest_results.insert_one(data)
            logger.info(f"Saved backtest result: {result.id}")
            return result.id
        except Exception as e:
            logger.error(f"Failed to save backtest result: {e}")
            raise

    def get_backtest_result(self, backtest_id: str) -> Optional[Dict]:
        """
        백테스트 결과 조회

        Args:
            backtest_id: 백테스트 ID

        Returns:
            백테스트 결과 또는 None
        """
        try:
            return self.db.backtest_results.find_one({"id": backtest_id})
        except Exception as e:
            logger.error(f"Failed to get backtest result: {e}")
            raise

    def get_backtest_results(self,
                           symbol: Optional[str] = None,
                           strategy: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> List[Dict]:
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
            query = {}
            if symbol:
                query["symbol"] = symbol
            if strategy:
                query["strategy"] = strategy
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["created_at"] = date_query

            return list(self.db.backtest_results.find(
                query,
                sort=[("created_at", -1)],
                limit=limit
            ))
        except Exception as e:
            logger.error(f"Failed to get backtest results: {e}")
            raise

    # 시뮬레이션 관련 메서드
    def save_simulation_result(self, result: SimulationResult) -> str:
        """
        시뮬레이션 결과 저장

        Args:
            result: 시뮬레이션 결과 객체

        Returns:
            저장된 문서의 ID
        """
        try:
            data = result.to_dict()
            self.db.simulation_results.insert_one(data)
            logger.info(f"Saved simulation result: {result.id}")
            return result.id
        except Exception as e:
            logger.error(f"Failed to save simulation result: {e}")
            raise

    def update_simulation_result(self, simulation_id: str, updates: Dict):
        """
        시뮬레이션 결과 업데이트

        Args:
            simulation_id: 시뮬레이션 ID
            updates: 업데이트할 필드와 값
        """
        try:
            self.db.simulation_results.update_one(
                {"id": simulation_id},
                {"$set": updates}
            )
            logger.info(f"Updated simulation result: {simulation_id}")
        except Exception as e:
            logger.error(f"Failed to update simulation result: {e}")
            raise

    def get_simulation_result(self, simulation_id: str) -> Optional[Dict]:
        """
        시뮬레이션 결과 조회

        Args:
            simulation_id: 시뮬레이션 ID

        Returns:
            시뮬레이션 결과 또는 None
        """
        try:
            return self.db.simulation_results.find_one({"id": simulation_id})
        except Exception as e:
            logger.error(f"Failed to get simulation result: {e}")
            raise

    def get_simulation_results(self,
                             symbol: Optional[str] = None,
                             strategy: Optional[str] = None,
                             status: Optional[str] = None,
                             limit: int = 100) -> List[Dict]:
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
            query = {}
            if symbol:
                query["symbol"] = symbol
            if strategy:
                query["strategy"] = strategy
            if status:
                query["status"] = status

            return list(self.db.simulation_results.find(
                query,
                sort=[("created_at", -1)],
                limit=limit
            ))
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
            self.db.simulation_results.delete_one({"id": simulation_id})
            logger.info(f"Deleted simulation result: {simulation_id}")
        except Exception as e:
            logger.error(f"Failed to delete simulation result: {e}")
            raise 