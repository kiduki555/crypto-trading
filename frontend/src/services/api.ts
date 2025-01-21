import axios, { AxiosInstance } from 'axios';
import { 
    BacktestParams, BacktestResult,
    SimulationParams, SimulationResult,
    LiveTradingParams, LiveTradingResult,
    ApiResponse
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 에러 처리
api.interceptors.response.use(
    response => response,
    error => {
        console.error('API Error:', error);
        return Promise.reject(error);
    }
);

// 요청 인터셉터 설정
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

class ApiService {
    private readonly baseUrl: string;

    constructor() {
        this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
    }

    private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }
        return response.json();
    }

    // 전략 및 리스크 관리자 관련 API
    async getStrategies(): Promise<ApiResponse<{ strategies: Array<{ name: string; description: string; default_params: Record<string, any> }> }>> {
        return this.request('/strategies');
    }

    async getRiskManagers(): Promise<ApiResponse<{ risk_managers: Array<{ name: string; description: string; default_params: Record<string, any> }> }>> {
        return this.request('/risk-managers');
    }

    // 백테스트 관련 API
    async getBacktests(params?: { symbol?: string; interval?: string }): Promise<ApiResponse<BacktestResult[]>> {
        const queryParams = new URLSearchParams(params as Record<string, string>).toString();
        return this.request(`/backtests${queryParams ? `?${queryParams}` : ''}`);
    }

    async createBacktest(params: BacktestParams): Promise<ApiResponse<BacktestResult>> {
        return this.request('/backtests', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }

    async getBacktestDetail(backtestId: string): Promise<ApiResponse<BacktestResult>> {
        return this.request(`/backtests/${backtestId}`);
    }

    // 시뮬레이션 관련 API
    async createSimulation(params: SimulationParams): Promise<ApiResponse<{ simulation_id: string }>> {
        return this.request('/simulations', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }

    async stopSimulation(simulationId: string): Promise<ApiResponse<SimulationResult>> {
        return this.request(`/simulations/${simulationId}/stop`, {
            method: 'POST',
        });
    }

    async getSimulations(params?: { symbol?: string; interval?: string }): Promise<ApiResponse<SimulationResult[]>> {
        const queryParams = new URLSearchParams(params as Record<string, string>).toString();
        return this.request(`/simulations${queryParams ? `?${queryParams}` : ''}`);
    }

    async getSimulationDetail(simulationId: string): Promise<ApiResponse<SimulationResult>> {
        return this.request(`/simulations/${simulationId}`);
    }

    // 라이브 트레이딩 관련 API
    async startLiveTrading(params: LiveTradingParams): Promise<ApiResponse<{ trading_id: string }>> {
        return this.request('/live/start', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }

    async stopLiveTrading(tradingId: string): Promise<ApiResponse<LiveTradingResult>> {
        return this.request(`/live/stop/${tradingId}`, {
            method: 'POST',
        });
    }

    async getLiveTrades(params?: { symbol?: string; strategy?: string }): Promise<ApiResponse<LiveTradingResult[]>> {
        const queryParams = new URLSearchParams(params as Record<string, string>).toString();
        return this.request(`/live/trades${queryParams ? `?${queryParams}` : ''}`);
    }

    async getLiveTradingDetail(tradingId: string): Promise<ApiResponse<LiveTradingResult>> {
        return this.request(`/live/${tradingId}`);
    }
}

export const apiService = new ApiService();

// 전략 관련 API
export const getStrategies = () => api.get('/strategies');

// 리스크 관리 관련 API
export const getRiskManagers = () => api.get('/risk-managers');

// 백테스트 관련 API
export const runBacktest = (params: BacktestParams) => api.post('/backtest', params);
export const getBacktestResult = (id: string) => api.get(`/backtest/${id}`);
export const getBacktestResults = (params?: any) => api.get('/backtests', { params });

// 시뮬레이션 관련 API
export const startSimulation = (params: SimulationParams) => api.post('/simulation', params);
export const stopSimulation = (id: string) => api.delete(`/simulation/${id}`);
export const getSimulationResult = (id: string) => api.get(`/simulation/${id}`);
export const getSimulationResults = (params?: any) => api.get('/simulations', { params });

export default api; 