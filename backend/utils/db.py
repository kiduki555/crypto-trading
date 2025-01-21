import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config.settings import settings
from utils.logger import logger

class MongoDB:
    """MongoDB 연결 관리자"""
    _instance: Optional['MongoDB'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            self._connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _connect(self):
        """MongoDB 연결 수립"""
        try:
            self._client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000  # 5초 타임아웃
            )
            # 연결 테스트
            self._client.server_info()
            self._db = self._client[settings.MONGODB_DB_NAME]
            logger.info("Connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB server selection timeout: {e}")
            raise

    def _ensure_connection(self):
        """연결이 살아있는지 확인하고 필요시 재연결"""
        try:
            if self._client:
                self._client.server_info()
            else:
                self._connect()
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.warning("Lost MongoDB connection, attempting to reconnect...")
            self._connect()

    @property
    def db(self) -> Database:
        """데이터베이스 인스턴스 반환"""
        self._ensure_connection()
        return self._db

    @property
    def client(self) -> MongoClient:
        """클라이언트 인스턴스 반환"""
        self._ensure_connection()
        return self._client

    def close(self):
        """MongoDB 연결 종료"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Closed MongoDB connection") 