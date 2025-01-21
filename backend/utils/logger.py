import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from config.settings import settings

def setup_logger(name='crypto_trading'):
    """
    애플리케이션 로거 설정

    Args:
        name: 로거 이름

    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 이미 핸들러가 설정되어 있다면 스킵
    if logger.handlers:
        return logger

    formatter = logging.Formatter(settings.LOG_FORMAT)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (로그 파일 디렉토리 생성)
    log_dir = os.path.dirname(settings.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 기본 로거 생성
logger = setup_logger() 