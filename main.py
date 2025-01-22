import argparse
import yaml
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd
from backtesting import Backtest

from strategies.bollinger_strategy import BollingerStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.ma_crossover_strategy import MACrossoverStrategy
from risk_management.dynamic_risk import DynamicRiskManagement
from data.data_collector import DataCollector
from data.data_loader import DataLoader
from trading.executor import TradingExecutor
from trading.simulator import TradingSimulator
from risk_management.base_risk import BaseRiskManager
from data.websocket_client import BinanceWebSocket
from custom_backtesting.performance import PerformanceAnalyzer

class TradingSystem:
    def __init__(self, config_path: str):
        """
        트레이딩 시스템 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        # 설정 로드
        self.config = self._load_config(config_path)
        
        # 로깅 설정
        self._setup_logging()
        
        # 전략 초기화
        self.strategies = self._initialize_strategies()
        
        # 리스크 관리자 초기화
        self.risk_manager = DynamicRiskManagement(self.config['risk_management'])
        
        # 데이터 로더 초기화
        self.data_loader = DataLoader(self.config['data'])
        
        self.logger = logging.getLogger(__name__)

    def run_live_trading(self):
        """실시간 트레이딩 실행"""
        try:
            self.logger.info("Starting live trading...")
            
            # 트레이딩 실행기 초기화
            executor = TradingExecutor(
                strategies=self.strategies,
                risk_manager=self.risk_manager,
                config=self.config['trading']
            )
            
            # 데이터 수집기 초기화 및 콜백 설정
            collector = DataCollector(
                exchange=self.config['exchange']['name'],
                symbol=self.config['trading']['symbol'],
                interval=self.config['trading']['interval'],
                callback=executor.process_market_data
            )
            
            # 실시간 데이터 수집 시작
            collector.start()
            
        except Exception as e:
            self.logger.error(f"Error in live trading: {str(e)}")
            raise

    def run_backtest(self):
        """백테스팅 실행"""
        try:
            self.logger.info("Starting backtest...")
            
            # 백테스트 기간 설정
            start_date = datetime.strptime(
                self.config['backtest']['start_date'],
                '%Y-%m-%d'
            )
            end_date = datetime.strptime(
                self.config['backtest']['end_date'],
                '%Y-%m-%d'
            )
            
            # 과거 데이터 로드
            self.data_loader.ensure_historical_data(
                symbol=self.config['trading']['symbol'],
                timeframe=self.config['trading']['interval'],
                start_time=start_date,
                end_time=end_date
            )
            
            data = self.data_loader.fetch_historical_data(
                symbol=self.config['trading']['symbol'],
                timeframe=self.config['trading']['interval'],
                start_time=start_date,
                end_time=end_date
            )
            
            # 필요한 컬럼만 선택하고 이름 변경
            data = data[['open', 'high', 'low', 'close', 'volume']]
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # 각 전략에 대해 백테스트 실행
            for strategy in self.strategies:
                self.logger.info(f"Running backtest for {strategy.__name__}")
                
                # Backtest 인스턴스 생성 및 실행
                bt = Backtest(
                    data,
                    strategy,
                    cash=self.config['backtest']['initial_balance'],
                    commission=self.config['backtest']['commission']
                )
                
                # 백테스트 실행
                results = bt.run()
                
                # 결과 출력
                self._print_backtest_results(results)
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {str(e)}")
            raise

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=self.config['logging']['level'],
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['logging']['file']),
                logging.StreamHandler()
            ]
        )

    def _initialize_strategies(self) -> List[Any]:
        """전략 초기화"""
        strategy_map = {
            'ma_crossover': MACrossoverStrategy,
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'bollinger': BollingerStrategy
        }
        
        strategies = []
        for strategy_name, params in self.config['strategies'].items():
            if strategy_name in strategy_map:
                strategy_class = strategy_map[strategy_name]
                # 전략 클래스의 클래스 변수 업데이트
                for param_name, param_value in params.items():
                    setattr(strategy_class, param_name, param_value)
                strategies.append(strategy_class)
            
        return strategies

    def _print_backtest_results(self, results: pd.Series):
        """백테스트 결과 출력"""
        print("\n=== Backtest Results ===")
        print(f"[수익률]")
        print(f"총 수익률: {results['Return [%]']:.2f}%")
        print(f"연간 수익률: {results['Return (Ann.) [%]']:.2f}%")
        print(f"최대 낙폭: {results['Max. Drawdown [%]']:.2f}%")
        print(f"수익 팩터: {results['Profit Factor']:.2f}")
        
        print(f"\n[거래 통계]")
        print(f"총 거래 횟수: {results['# Trades']}")
        print(f"승률: {results['Win Rate [%]']:.2f}%")
        print(f"평균 거래 수익: {results['Avg. Trade [%]']:.2f}%")
        print(f"최대 단일 수익: {results['Best Trade [%]']:.2f}%")
        print(f"최대 단일 손실: {results['Worst Trade [%]']:.2f}%")
        print(f"평균 거래 시간: {results['Avg. Trade Duration']}")
        
        print(f"\n[위험 지표]")
        print(f"샤프 비율: {results['Sharpe Ratio']:.2f}")
        
        print(f"\n[포지션 정보]")
        trades = results._trades
        if len(trades) > 0:
            longs = len(trades[trades['Size'] > 0])
            shorts = len(trades[trades['Size'] < 0])
            total_trades = len(trades)
            
            print(f"롱 포지션 비율: {longs/total_trades*100:.1f}%")
            print(f"숏 포지션 비율: {shorts/total_trades*100:.1f}%")
            
            if longs > 0:
                long_wins = len(trades[(trades['Size'] > 0) & (trades['PnL'] > 0)])
                print(f"롱 승률: {long_wins/longs*100:.1f}%")
            
            if shorts > 0:
                short_wins = len(trades[(trades['Size'] < 0) & (trades['PnL'] > 0)])
                print(f"숏 승률: {short_wins/shorts*100:.1f}%")
        
        print("=====================\n")


def load_config(config_path: str) -> Dict[str, Any]:
    """설정 파일 로드"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_strategy(strategy_name: str, params: dict):
    """전략 객체 생성"""
    strategies = {
        'ma_crossover': MACrossoverStrategy,
        'rsi': RSIStrategy,
        'macd': MACDStrategy,
        'bollinger': BollingerStrategy
    }
    
    if strategy_name not in strategies:
        raise ValueError(f"Unknown strategy: {strategy_name}")
        
    return strategies[strategy_name](params)

def main():
    parser = argparse.ArgumentParser(description='Crypto Trading System')
    parser.add_argument('--mode', required=True,
                      choices=['backtest', 'live', 'simulation'],
                      help='실행 모드')
    parser.add_argument('--config', required=True,
                      help='설정 파일 경로')
    parser.add_argument('--strategy', default='ma_crossover',
                      help='사용할 전략 (쉼표로 구분하여 여러 개 지정 가능)')
    parser.add_argument('--account-id',
                      help='시뮬레이션용 계정 ID')
    parser.add_argument('--symbol', default='btcusdt',
                      help='거래 심볼 (예: btcusdt)')
    parser.add_argument('--interval', default='1m',
                      help='캔들스틱 간격 (예: 1m, 5m, 15m, 1h)')
    parser.add_argument('--start-date',
                      help='백테스트 시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('--end-date',
                      help='백테스트 종료 날짜 (YYYY-MM-DD)')
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    config = load_config(args.config)
    
    # 백테스트 날짜 설정이 있으면 config에 추가
    if args.start_date:
        if 'backtest' not in config:
            config['backtest'] = {}
        config['backtest']['start_date'] = args.start_date
    if args.end_date:
        if 'backtest' not in config:
            config['backtest'] = {}
        config['backtest']['end_date'] = args.end_date
    
    # 전략 및 리스크 관리자 생성
    risk_manager = BaseRiskManager(config['risk_management'])
    
    if args.mode == 'simulation':
        # 전략 목록 생성
        strategies = []
        strategy_names = args.strategy.split(',')
        for strategy_name in strategy_names:
            strategy_name = strategy_name.strip()
            if strategy_name in config['strategies']:
                strategy = get_strategy(strategy_name, config['strategies'][strategy_name])
                strategies.append(strategy)
            else:
                logger.warning(f"Strategy '{strategy_name}' not found in config, skipping...")
        
        if not strategies:
            logger.error("No valid strategies found")
            return
            
        # 시뮬레이션 모드
        simulator = TradingSimulator(
            db_path='data/market_data.db',
            strategies=strategies,
            risk_manager=risk_manager,
            account_id=args.account_id
        )
        
        # 계정 초기화
        initial_balance = config['simulation']['initial_balance']
        if simulator.initialize_account(initial_balance):
            logger.info(f"Simulation account created with {initial_balance} USDT")
        else:
            logger.info("Using existing simulation account")
            
        # WebSocket 클라이언트 시작
        ws_client = BinanceWebSocket(
            symbol=args.symbol,
            interval=args.interval,
            callback=simulator.process_market_data
        )
        
        try:
            strategy_names_str = ', '.join(s.__class__.__name__ for s in strategies)
            logger.info(f"Starting simulation for {args.symbol} with strategies: {strategy_names_str}")
            ws_client.start()
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        except Exception as e:
            logger.error(f"Simulation error: {str(e)}")
            
    elif args.mode == 'backtest':
        # 백테스팅 모드
        trading_system = TradingSystem(args.config)
        trading_system.run_backtest()
    elif args.mode == 'live':
        # 실시간 거래 모드
        trading_system = TradingSystem(args.config)
        trading_system.run_live_trading()

if __name__ == '__main__':
    main()
