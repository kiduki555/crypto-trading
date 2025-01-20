import argparse
import yaml
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from strategies.bollinger_strategy import BollingerStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.ma_crossover_strategy import MACrossoverStrategy
from risk_management.dynamic_risk import DynamicRiskManagement
from data.data_collector import DataCollector
from data.data_loader import DataLoader
from trading.executor import TradingExecutor
from backtesting.backtester import Backtester
from backtesting.performance import PerformanceAnalyzer
from trading.simulator import TradingSimulator
from risk_management.base_risk import BaseRiskManager
from data.websocket_client import BinanceWebSocket

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
            
            # 백테스터 초기화 및 실행
            backtester = Backtester(
                strategies=self.strategies,
                risk_manager=self.risk_manager,
                initial_balance=self.config['backtest']['initial_balance'],
                commission=self.config['backtest']['commission']
            )
            
            results = backtester.run(data)
            
            # 성과 분석
            analyzer = PerformanceAnalyzer(results)
            metrics = analyzer.calculate_metrics()
            
            # 결과 출력
            self._print_backtest_results(metrics)
            
            # 차트 생성
            analyzer.plot_equity_curve()
            analyzer.plot_drawdown()
            analyzer.plot_monthly_returns()
            
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
            'RSI': RSIStrategy,
            'MACD': MACDStrategy,
            'MA_Crossover': MACrossoverStrategy,
            'bollinger': BollingerStrategy
        }
        
        strategies = []
        for strategy_config in self.config['strategies']:
            strategy_class = strategy_map[strategy_config['name']]
            strategies.append(strategy_class(strategy_config['params']))
            
        return strategies

    def _print_backtest_results(self, metrics: Dict[str, Any]):
        """백테스트 결과 출력"""
        print("\n=== Backtest Results ===")
        print(f"Total Return: {metrics['total_return_pct']:.2f}%")
        print(f"Win Rate: {metrics['win_rate']:.2f}%")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"Average Trade Duration: {metrics['avg_trade_duration']}")
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
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    config = load_config(args.config)
    
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
        # TODO: Implement backtest mode
        pass
        
    elif args.mode == 'live':
        # 실시간 거래 모드
        # TODO: Implement live trading mode
        pass

if __name__ == '__main__':
    main()
