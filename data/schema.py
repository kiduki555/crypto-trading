SCHEMA_QUERIES = [
    # 더미 계정 테이블
    """
    CREATE TABLE IF NOT EXISTS dummy_accounts (
        account_id TEXT PRIMARY KEY,
        initial_balance REAL NOT NULL,
        current_balance REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # 포지션 테이블
    """
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        position_size REAL NOT NULL,
        entry_price REAL NOT NULL,
        current_price REAL NOT NULL,
        direction TEXT NOT NULL,
        strategy TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES dummy_accounts(account_id)
    )
    """,
    
    # 거래 기록 테이블
    """
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL,
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        realized_pnl REAL,
        commission REAL NOT NULL,
        strategy TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES dummy_accounts(account_id)
    )
    """
]