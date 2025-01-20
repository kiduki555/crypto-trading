from typing import Dict, Optional, List
import sqlite3
from datetime import datetime
import uuid
from data.schema import SCHEMA_QUERIES

class DummyAccount:
    def __init__(self, db_path: str, account_id: Optional[str] = None):
        """
        더미 계정 관리 클래스
        
        Args:
            db_path: 데이터베이스 경로
            account_id: 계정 ID (None인 경우 새로 생성)
        """
        self.db_path = db_path
        self.account_id = account_id or f"dummy_{uuid.uuid4().hex[:8]}"
        self._ensure_tables()
        
    def _ensure_tables(self):
        """필요한 테이블이 없으면 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for query in SCHEMA_QUERIES:
            cursor.execute(query)
            
        conn.commit()
        conn.close()
        
    def create_account(self, initial_balance: float) -> bool:
        """새로운 더미 계정 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO dummy_accounts (account_id, initial_balance, current_balance)
                VALUES (?, ?, ?)
            """, (self.account_id, initial_balance, initial_balance))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
            
    def get_balance(self) -> float:
        """현재 계정 잔고 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT current_balance FROM dummy_accounts
            WHERE account_id = ?
        """, (self.account_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0.0
        
    def update_balance(self, new_balance: float) -> bool:
        """계정 잔고 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE dummy_accounts
                SET current_balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE account_id = ?
            """, (new_balance, self.account_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
            
    def get_positions(self) -> List[Dict]:
        """현재 보유 포지션 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, position_size, entry_price, current_price,
                   unrealized_pnl, direction
            FROM dummy_positions
            WHERE account_id = ?
        """, (self.account_id,))
        
        columns = ['symbol', 'position_size', 'entry_price', 'current_price',
                  'unrealized_pnl', 'direction']
        positions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return positions
        
    def update_position(self, symbol: str, position_size: float,
                       entry_price: float, current_price: float,
                       direction: str) -> bool:
        """포지션 업데이트 또는 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        unrealized_pnl = (current_price - entry_price) * position_size
        if direction == 'short':
            unrealized_pnl *= -1
            
        try:
            # 기존 포지션이 있는지 확인
            cursor.execute("""
                SELECT id FROM dummy_positions
                WHERE account_id = ? AND symbol = ?
            """, (self.account_id, symbol))
            
            if cursor.fetchone():
                # 포지션 업데이트
                cursor.execute("""
                    UPDATE dummy_positions
                    SET position_size = ?, entry_price = ?, current_price = ?,
                        unrealized_pnl = ?, direction = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE account_id = ? AND symbol = ?
                """, (position_size, entry_price, current_price, unrealized_pnl,
                     direction, self.account_id, symbol))
            else:
                # 새 포지션 생성
                cursor.execute("""
                    INSERT INTO dummy_positions
                    (account_id, symbol, position_size, entry_price, current_price,
                     unrealized_pnl, direction)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.account_id, symbol, position_size, entry_price,
                     current_price, unrealized_pnl, direction))
            
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
            
    def record_trade(self, symbol: str, direction: str, quantity: float,
                    price: float, realized_pnl: Optional[float],
                    commission: float, strategy: str) -> bool:
        """거래 내역 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO dummy_trades
                (account_id, symbol, direction, quantity, price,
                 realized_pnl, commission, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.account_id, symbol, direction, quantity, price,
                 realized_pnl, commission, strategy))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
            
    def get_trade_history(self) -> List[Dict]:
        """거래 내역 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, direction, quantity, price, realized_pnl,
                   commission, strategy, created_at
            FROM dummy_trades
            WHERE account_id = ?
            ORDER BY created_at DESC
        """, (self.account_id,))
        
        columns = ['symbol', 'direction', 'quantity', 'price', 'realized_pnl',
                  'commission', 'strategy', 'created_at']
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return trades 