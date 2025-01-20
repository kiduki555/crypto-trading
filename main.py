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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automated Trading System')
    parser.add_argument('--mode', choices=['live', 'backtest'], required=True,
                      help='Trading mode: live or backtest')
    parser.add_argument('--config', default='config/settings.yaml',
                      help='Path to configuration file')
    
    args = parser.parse_args()
    
    # 트레이딩 시스템 초기화 및 실행
    system = TradingSystem(args.config)
    
    if args.mode == 'live':
        system.run_live_trading()
    else:
        system.run_backtest()
