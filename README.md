# Crypto Trading System

암호화폐 자동 거래 시스템으로, 다중 전략 기반의 백테스팅과 실시간 거래를 지원합니다.

## 주요 기능

- 다중 전략 기반 거래 시스템
  - MA Crossover Strategy
  - RSI Strategy
  - MACD Strategy
  - Bollinger Bands Strategy
- 백테스팅 시스템
  - 과거 데이터 기반 전략 테스트
  - 상세한 성과 분석 (수익률, 승률, 샤프 비율 등)
  - 자본금 변화 및 드로다운 시각화
- 실시간 시뮬레이션
  - Binance WebSocket 기반 실시간 데이터
  - 더미 계정을 통한 모의 거래
  - 실시간 손익 및 포지션 추적
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

### 백테스팅 실행
```bash
# 기본 설정으로 백테스팅 실행
python main.py --mode backtest --config config/settings.yaml

# 특정 기간 백테스팅 실행
python main.py --mode backtest --config config/settings.yaml --start-date 2023-01-01 --end-date 2023-12-31

# 특정 전략으로 백테스팅 실행
python main.py --mode backtest --config config/settings.yaml --strategy ma_crossover

# 여러 전략 동시 실행
python main.py --mode backtest --config config/settings.yaml --strategy "bollinger,rsi,ma_crossover"
```

백테스팅에서 여러 전략을 사용할 경우, 시뮬레이션과 동일하게 과반수 기준으로 매매 결정이 이루어집니다.
백테스팅 결과는 `results/` 디렉토리에 저장되며, 다음과 같은 정보를 포함합니다:
- 전체 거래 내역
- 수익률 분석
- 포지션별 성과
- 월별 수익률
- 드로다운 분석

### 실시간 시뮬레이션 실행
```bash
# 기본 설정으로 시뮬레이션 실행 (BTC/USDT, 1분봉)
python main.py --mode simulation --config config/settings.yaml --strategy bollinger

# 다른 심볼과 시간 간격으로 실행
python main.py --mode simulation --config config/settings.yaml --strategy rsi --symbol ethusdt --interval 5m

# 여러 전략 동시 실행 (쉼표로 구분)
python main.py --mode simulation --config config/settings.yaml --strategy "bollinger,rsi,ma_crossover"

# 기존 계정으로 시뮬레이션 재시작
python main.py --mode simulation --config config/settings.yaml --account-id dummy_12345678
```

시뮬레이션 실행 시 필요한 데이터베이스 테이블이 자동으로 생성됩니다.
여러 전략을 동시에 사용할 경우, 각 전략의 신호를 종합하여 하나의 매매 결정을 내립니다:
- 과반수의 전략이 매수 신호를 보내면 매수
- 과반수의 전략이 매도 신호를 보내면 매도
- 하나 이상의 전략이 청산 신호를 보내면 청산
- 그 외의 경우 포지션 유지

예를 들어, 3개의 전략을 사용할 경우:
- 2개 이상의 전략이 매수 신호를 보내면 매수 포지션 진입
- 2개 이상의 전략이 매도 신호를 보내면 매도 포지션 진입
- 1개 이상의 전략이 청산 신호를 보내면 현재 포지션 청산

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

예시 (볼린저 밴드 전략):
```python
from .base_strategy import BaseStrategy

class BollingerStrategy(BaseStrategy):
    def __init__(self, params):
        super().__init__(params)
        self.window = params.get('window', 20)
        self.std_dev = params.get('std_dev', 2.0)
        
    def calculate_signals(self, data):
        # 볼린저 밴드 계산
        bb = ta.volatility.BollingerBands(
            close=data['close'],
            window=self.window,
            window_dev=self.std_dev
        )
        
        # 매매 신호 생성
        if price < lower_band:
            return {'direction': 'long', 'strength': 0.8}
        elif price > upper_band:
            return {'direction': 'short', 'strength': 0.8}
        
        return {'direction': None, 'strength': 0}
```

설정 예시:
```yaml
strategies:
  bollinger:
    window: 20
    std_dev: 2.0
    entry_threshold: 1.0
    exit_threshold: 0.5
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

## 데이터베이스 구조

### dummy_accounts
- 시뮬레이션용 더미 계정 정보
- 초기 자본금 및 현재 잔고 관리

### dummy_positions
- 현재 보유 중인 포지션 정보
- 진입가, 현재가, 미실현 손익 등

### dummy_trades
- 거래 내역
- 실현 손익, 수수료, 사용된 전략 등

## 전략 설정

`config/settings.yaml` 파일에서 각 전략의 파라미터를 설정할 수 있습니다:

```yaml
strategies:
  ma_crossover:
    short_window: 10
    long_window: 20
    
  rsi:
    period: 14
    oversold: 30
    overbought: 70
    
  macd:
    fast_period: 12
    slow_period: 26
    signal_period: 9
    
  bollinger:
    window: 20
    std_dev: 2.0
    entry_threshold: 1.0
    exit_threshold: 0.5
```

각 전략의 주요 파라미터:

### MA Crossover Strategy
- `short_window`: 단기 이동평균 기간
- `long_window`: 장기 이동평균 기간

### RSI Strategy
- `period`: RSI 계산 기간
- `oversold`: 과매도 기준값
- `overbought`: 과매수 기준값

### MACD Strategy
- `fast_period`: 단기 EMA 기간
- `slow_period`: 장기 EMA 기간
- `signal_period`: 시그널 라인 기간

### Bollinger Bands Strategy
- `window`: 이동평균 기간
- `std_dev`: 표준편차 승수
- `entry_threshold`: 진입 임계값
- `exit_threshold`: 청산 임계값