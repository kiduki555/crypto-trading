from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Any, Tuple
from core.strategies import get_strategy
from core.risk_management import get_risk_manager
from services.database import DatabaseService
from models.backtest import BacktestResult
from models.simulation import SimulationResult
from utils.logger import logger
from config.settings import settings
from services.backtest import BacktestService
from services.simulation import SimulationService

app = Flask(__name__)
CORS(app)
db = DatabaseService()

backtest_service = BacktestService()
simulation_service = SimulationService()

def validate_request_data(data: Dict[str, Any], required_fields: list) -> Tuple[bool, str]:
    """
    요청 데이터 유효성 검사

    Args:
        data: 요청 데이터
        required_fields: 필수 필드 목록

    Returns:
        (유효성 여부, 에러 메시지)
    """
    if not data:
        return False, "No data provided"
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""

@app.route('/api/strategies', methods=['GET'])
def get_available_strategies():
    """사용 가능한 전략 목록 반환"""
    try:
        strategies = [
            {
                'name': name,
                'description': strategy.description,
                'default_params': strategy.default_params
            }
            for name, strategy in get_strategy.AVAILABLE_STRATEGIES.items()
        ]
        return jsonify({'strategies': strategies})
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/risk-managers', methods=['GET'])
def get_available_risk_managers():
    """사용 가능한 리스크 관리 전략 목록 반환"""
    try:
        risk_managers = [
            {
                'name': name,
                'description': manager.description,
                'default_params': manager.default_params
            }
            for name, manager in get_risk_manager.AVAILABLE_RISK_MANAGERS.items()
        ]
        return jsonify({'risk_managers': risk_managers})
    except Exception as e:
        logger.error(f"Failed to get risk managers: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/backtest', methods=['POST'])
async def run_backtest():
    """백테스트 실행"""
    try:
        data = request.json
        required_fields = ['symbol', 'strategy', 'risk_management', 'start_date', 
                         'end_date', 'initial_capital', 'strategy_params', 'risk_params']
        validate_request_data(data, required_fields)
        
        # 날짜 문자열을 datetime으로 변환
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        backtest_id = await backtest_service.run_backtest(
            symbol=data['symbol'],
            strategy=data['strategy'],
            risk_management=data['risk_management'],
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(data['initial_capital']),
            strategy_params=data['strategy_params'],
            risk_params=data['risk_params'],
            interval=data.get('interval', '1h')
        )
        
        return jsonify({'backtest_id': backtest_id}), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/backtest/<backtest_id>', methods=['GET'])
def get_backtest_result(backtest_id):
    """백테스트 결과 조회"""
    try:
        result = backtest_service.get_backtest_result(backtest_id)
        if not result:
            return jsonify({'error': 'Backtest not found'}), 404
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to get backtest result: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/backtests', methods=['GET'])
def get_backtest_results():
    """백테스트 결과 목록 조회"""
    try:
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        results = backtest_service.get_backtest_results(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return jsonify([result.to_dict() for result in results])
        
    except Exception as e:
        logger.error(f"Failed to get backtest results: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/simulation', methods=['POST'])
async def start_simulation():
    """시뮬레이션 시작"""
    try:
        data = request.json
        required_fields = ['symbol', 'strategy', 'risk_management', 
                         'initial_capital', 'strategy_params', 'risk_params']
        validate_request_data(data, required_fields)
        
        simulation_id = await simulation_service.start_simulation(
            symbol=data['symbol'],
            strategy=data['strategy'],
            risk_management=data['risk_management'],
            initial_capital=float(data['initial_capital']),
            strategy_params=data['strategy_params'],
            risk_params=data['risk_params'],
            interval=data.get('interval', '1m')
        )
        
        return jsonify({'simulation_id': simulation_id}), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/simulation/<simulation_id>', methods=['DELETE'])
async def stop_simulation(simulation_id):
    """시뮬레이션 중지"""
    try:
        await simulation_service.stop_simulation(simulation_id)
        return '', 204
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Failed to stop simulation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/simulation/<simulation_id>', methods=['GET'])
def get_simulation_result(simulation_id):
    """시뮬레이션 결과 조회"""
    try:
        result = simulation_service.get_simulation_result(simulation_id)
        if not result:
            return jsonify({'error': 'Simulation not found'}), 404
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to get simulation result: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/simulations', methods=['GET'])
def get_simulation_results():
    """시뮬레이션 결과 목록 조회"""
    try:
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        results = simulation_service.get_simulation_results(
            symbol=symbol,
            strategy=strategy,
            status=status,
            limit=limit
        )
        
        return jsonify([result.to_dict() for result in results])
        
    except Exception as e:
        logger.error(f"Failed to get simulation results: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/live-trading/start', methods=['POST'])
def start_live_trading():
    """실시간 거래 시작"""
    # TODO: 실시간 거래 시작 로직 구현
    return jsonify({'status': 'success'})

@app.route('/api/live-trading/stop', methods=['POST'])
def stop_live_trading():
    """실시간 거래 중지"""
    # TODO: 실시간 거래 중지 로직 구현
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(
        debug=settings.FLASK_DEBUG,
        port=settings.WS_PORT
    ) 