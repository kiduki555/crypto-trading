# Crypto Trading System

암호화폐 자동 거래 시스템으로, 다중 전략 기반의 백테스팅과 실시간 거래를 지원합니다.

## 주요 기능

- 다중 전략 기반 거래 시스템
  - MA Crossover Strategy
  - RSI Strategy
  - MACD Strategy
- 백테스팅 시스템
  - 과거 데이터 기반 전략 테스트
  - 상세한 성과 분석 (수익률, 승률, 샤프 비율 등)
  - 자본금 변화 및 드로다운 시각화
- 리스크 관리
  - 동적 포지션 사이징
  - 스탑로스/익절 자동 설정
  - ATR 기반 변동성 고려
- 데이터 관리
  - SQLite 기반 시장 데이터 저장
  - 자동 데이터 업데이트
  - 캐시 시스템

## 시스템 구조

```
crypto-trading/
├── backtesting/          # 백테스팅 관련 모듈
│   ├── backtester.py     # 백테스팅 엔진
│   └── performance.py    # 성과 분석
├── config/               # 설정 파일
│   └── settings.yaml     # 시스템 설정
├── data/                 # 데이터 관리
│   ├── data_collector.py # 데이터 수집
│   └── data_loader.py    # 데이터 로딩
├── risk_management/      # 리스크 관리
│   ├── base_risk.py     # 기본 리스크 관리
│   ├── dynamic_risk.py  # 동적 리스크 관리
│   └── fixed_stoploss.py# 고정 스탑로스
├── strategies/          # 거래 전략
│   ├── base_strategy.py # 기본 전략 클래스
│   ├── ma_crossover_strategy.py  # 이동평균 크로스오버
│   ├── macd_strategy.py # MACD 전략
│   └── rsi_strategy.py  # RSI 전략
├── trading/            # 실시간 거래
│   ├── executor.py    # 주문 실행
│   └── position_manager.py # 포지션 관리
├── main.py            # 메인 실행 파일
└── requirements.txt   # 의존성 패키지
```

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/kiduki555/crypto-trading.git
cd crypto-trading
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

## 설정

1. `config/settings.yaml` 파일에서 다음 설정을 수정:
   - 거래소 API 키/시크릿
   - 거래 심볼 및 시간 간격
   - 전략 파라미터
   - 리스크 관리 설정
   - 백테스팅 기간

## 사용 방법

### 데이터베이스 초기화
시스템 최초 실행 시 `data/market_data.db` 파일이 자동으로 생성되며, 필요한 테이블들이 자동으로 설정됩니다. 수동으로 데이터베이스를 초기화하려면:
```bash
python main.py --mode init-db
```

### 백테스팅 실행
```bash
# 기본 설정으로 백테스팅 실행
python main.py --mode backtest --config config/settings.yaml

# 특정 기간 백테스팅 실행
python main.py --mode backtest --config config/settings.yaml --start-date 2023-01-01 --end-date 2023-12-31

# 특정 전략으로 백테스팅 실행
python main.py --mode backtest --config config/settings.yaml --strategy ma_crossover
```

### 실시간 거래 실행
```bash
# 기본 설정으로 실시간 거래 실행
python main.py --mode live --config config/settings.yaml

# 특정 전략으로 실시간 거래 실행
python main.py --mode live --config config/settings.yaml --strategy rsi

# 백그라운드에서 실행
nohup python main.py --mode live --config config/settings.yaml > trading.log 2>&1 &
```

### 결과 확인
- 백테스팅 결과는 `results/` 디렉토리에 저장됩니다
- 거래 로그는 `logs/` 디렉토리에서 확인할 수 있습니다
- 실시간 거래 상태는 웹 대시보드(http://localhost:8501)에서 모니터링할 수 있습니다

### 프로그램 종료
```bash
# 실시간 거래 종료
pkill -f "python main.py"
```

## 전략 추가 방법

1. `strategies` 디렉토리에 새로운 전략 파일 생성
2. `BaseStrategy` 클래스를 상속받아 구현
3. `calculate_signals` 메서드 구현
4. `config/settings.yaml`에 전략 설정 추가

예시:
```python
from .base_strategy import BaseStrategy

class NewStrategy(BaseStrategy):
    def __init__(self, params):
        super().__init__(params)
        # 전략 파라미터 초기화

    def calculate_signals(self, data):
        # 매매 신호 계산 로직 구현
        return {
            'direction': 'long/short/None',
            'strength': 0.0
        }
```

## 리스크 관리

- `risk_per_trade`: 거래당 리스크 비율 (기본값: 1%)
- `max_leverage`: 최대 레버리지
- `stop_loss_atr_multiplier`: ATR 기반 스탑로스 설정
- `take_profit_atr_multiplier`: ATR 기반 익절 설정
- `trailing_stop_start`: 트레일링 스탑 시작 조건

## 성과 분석

백테스팅 결과는 다음 지표들을 포함합니다:
- 총 수익률
- 승률
- 수익 팩터
- 샤프 비율
- 최대 드로다운
- 평균 거래 기간

또한 다음 시각화를 제공합니다:
- 자본금 변화 곡선
- 드로다운 차트
- 월별 수익률 히트맵