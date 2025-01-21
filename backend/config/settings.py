from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # MongoDB 설정
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'crypto_trading')
    
    # Binance API 설정
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    # Flask 설정
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # WebSocket 설정
    WS_PORT = int(os.getenv('WS_PORT', '8765'))
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/crypto_trading.log'

    # 거래 설정
    DEFAULT_COMMISSION_RATE = float(os.getenv('DEFAULT_COMMISSION_RATE', '0.001'))  # 0.1%
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '20'))
    
    # 백테스트 설정
    MIN_BACKTEST_PERIOD = int(os.getenv('MIN_BACKTEST_PERIOD', '7'))  # 최소 7일
    MAX_BACKTEST_PERIOD = int(os.getenv('MAX_BACKTEST_PERIOD', '365'))  # 최대 1년

settings = Settings() 