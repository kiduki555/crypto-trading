import { io, Socket } from 'socket.io-client';
import { Trade } from '../types';

class WebSocketService {
    private socket: Socket | null = null;
    private simulationHandlers: Map<string, (trade: Trade) => void> = new Map();
    private liveTradeHandlers: Map<string, (trade: Trade) => void> = new Map();

    constructor() {
        this.socket = io(process.env.REACT_APP_WS_URL || 'http://localhost:5000', {
            autoConnect: false
        });

        this.setupEventListeners();
    }

    private setupEventListeners() {
        if (!this.socket) return;

        this.socket.on('simulation_update', (data: { simulation_id: string; trade: Trade }) => {
            const handler = this.simulationHandlers.get(data.simulation_id);
            if (handler) {
                handler(data.trade);
            }
        });

        this.socket.on('live_trade_update', (data: { trading_id: string; trade: Trade }) => {
            const handler = this.liveTradeHandlers.get(data.trading_id);
            if (handler) {
                handler(data.trade);
            }
        });

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });

        this.socket.on('error', (error: Error) => {
            console.error('WebSocket error:', error);
        });
    }

    connect() {
        if (this.socket) {
            this.socket.connect();
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    subscribeToSimulation(simulationId: string, handler: (trade: Trade) => void) {
        this.simulationHandlers.set(simulationId, handler);
    }

    unsubscribeFromSimulation(simulationId: string) {
        this.simulationHandlers.delete(simulationId);
    }

    subscribeToLiveTrade(tradingId: string, handler: (trade: Trade) => void) {
        this.liveTradeHandlers.set(tradingId, handler);
    }

    unsubscribeFromLiveTrade(tradingId: string) {
        this.liveTradeHandlers.delete(tradingId);
    }
}

export const webSocketService = new WebSocketService(); 