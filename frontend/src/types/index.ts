// 백테스트 관련 타입
export interface BacktestParams {
    symbol: string;
    strategy: string;
    risk_management: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    interval?: string;
    strategy_params?: Record<string, any>;
    risk_params?: Record<string, any>;
}

export interface BacktestResult {
    id: string;
    symbol: string;
    strategy: string;
    risk_management: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    final_capital: number;
    total_pnl: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    max_drawdown: number;
    sharpe_ratio: number;
    trades: Trade[];
    indicators?: Record<string, number[]>;
}

// 시뮬레이션 관련 타입
export interface SimulationParams {
    symbol: string;
    strategy: string;
    risk_management: string;
    initial_capital: number;
    interval?: string;
    strategy_params?: Record<string, any>;
    risk_params?: Record<string, any>;
}

export interface SimulationResult {
    id: string;
    symbol: string;
    strategy: string;
    risk_management: string;
    start_time: string;
    end_time?: string;
    initial_capital: number;
    current_capital: number;
    total_pnl: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    max_drawdown: number;
    trades: Trade[];
    status: 'running' | 'completed' | 'error';
    error_message?: string;
    indicators?: Record<string, number[]>;
}

// 라이브 트레이딩 관련 타입
export interface LiveTradingParams {
    symbol: string;
    strategy: string;
    risk_management: string;
    interval: string;
}

export interface LiveTradingResult {
    trading_id: string;
    symbol: string;
    strategy: string;
    status: 'running' | 'stopped';
    summary: {
        total_trades: number;
        winning_trades: number;
        losing_trades: number;
        win_rate: number;
        profit_loss: number;
        max_drawdown: number;
    };
    trades: Trade[];
}

// 공통 타입
export interface Trade {
    timestamp: string;
    symbol: string;
    position_type: 'long' | 'short';
    entry_price: number;
    exit_price: number;
    position_size: number;
    pnl: number;
    stop_loss: number;
    take_profit: number;
    exit_reason: string;
    holding_period: number;
}

export interface Position {
    timestamp: number;
    type: 'long' | 'short' | 'none';
    entry_price?: number;
    size?: number;
    current_price?: number;
    unrealized_pnl?: number;
}

// API 응답 타입
export interface ApiResponse<T> {
    data: T;
    error?: string;
} 