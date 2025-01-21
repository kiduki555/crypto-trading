# Crypto Trading System

암호화폐 자동 거래 시스템으로, 다중 전략 기반의 백테스팅과 실시간 거래를 지원합니다.

## 프로젝트 구조

```
crypto-trading/
├── frontend/           # React 프론트엔드
│   ├── src/           # 소스 코드
│   ├── public/        # 정적 파일
│   └── package.json   # 의존성 관리
└── backend/           # Flask 백엔드
    ├── app.py         # Flask 애플리케이션
    ├── core/          # 핵심 비즈니스 로직
    │   ├── strategies/    # 거래 전략
    │   └── risk_management/ # 리스크 관리
    ├── services/      # 서비스 레이어
    ├── models/        # 데이터 모델
    ├── utils/         # 유틸리티 함수
    └── config/        # 설정 파일
```

## 기술 스택

### Frontend
- React 18
- TypeScript
- Material-UI (MUI)
- TradingView Lightweight Charts
- WebSocket

### Backend
- Python 3.11
- Flask
- MongoDB
- WebSocket
- Binance API

## 설치 방법

1. Python 3.11 설치:
```bash
# macOS
brew install python@3.11

# Windows
# https://www.python.org/downloads/ 에서 Python 3.11 설치
```

2. Node.js 설치:
```bash
# macOS
brew install node

# Windows
# https://nodejs.org/ 에서 Node.js LTS 버전 설치
```

3. MongoDB 설치:
```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0

# Windows
# https://www.mongodb.com/try/download/community 에서 MongoDB 설치
```

4. 저장소 클론:
```bash
git clone https://github.com/kiduki555/crypto-trading.git
cd crypto-trading
```

5. 백엔드 설정:
```bash
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
.\venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env  # .env 파일 설정
```

6. 프론트엔드 설정:
```bash
cd frontend
npm install
cp .env.example .env  # .env 파일 설정
```

## 실행 방법

1. MongoDB 서비스 실행 확인:
```bash
# macOS
brew services list | grep mongodb
```

2. 백엔드 서버 실행:
```bash
cd backend
flask run --port=5000
```

3. 프론트엔드 개발 서버 실행:
```bash
cd frontend
npm run dev
```

4. 브라우저에서 접속:
```
http://localhost:3000
```

## 주요 기능

- 다중 전략 기반 거래 시스템
  - MA Crossover Strategy
  - RSI Strategy
  - MACD Strategy
  - Bollinger Bands Strategy
- 백테스팅 시스템
  - 과거 데이터 기반 전략 테스트
  - 상세한 성과 분석
- 실시간 시뮬레이션
  - Binance WebSocket 기반 실시간 데이터
  - 더미 계정을 통한 모의 거래
- 리스크 관리
  - 동적 포지션 사이징
  - 스탑로스/익절 자동 설정
