import { Trade, Position } from '../types';

type MessageHandler = (data: any) => void;

class WebSocketService {
    private socket: WebSocket | null = null;
    private messageHandlers: Map<string, MessageHandler> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectTimeout = 1000;
    private isReconnecting = false;

    connect() {
        if (this.socket?.readyState === WebSocket.OPEN || this.isReconnecting) return;

        try {
            this.socket = new WebSocket('ws://localhost:8000/ws');

            this.socket.onopen = this.handleOpen.bind(this);
            this.socket.onmessage = this.handleMessage.bind(this);
            this.socket.onclose = this.handleClose.bind(this);
            this.socket.onerror = this.handleError.bind(this);
        } catch (err) {
            console.error('WebSocket 연결 생성 실패:', err);
            this.handleError(err);
        }
    }

    private handleOpen() {
        console.log('WebSocket 연결됨');
        this.reconnectAttempts = 0;
        this.isReconnecting = false;

        // 연결이 성공하면 모든 채널을 다시 구독
        this.messageHandlers.forEach((_, channel) => {
            this.sendSubscribeMessage(channel);
        });
    }

    private handleMessage(event: MessageEvent) {
        try {
            const message = JSON.parse(event.data);
            const handler = this.messageHandlers.get(message.type);
            if (handler) {
                handler(message.data);
            }
        } catch (err) {
            console.error('WebSocket 메시지 처리 실패:', err);
        }
    }

    private handleClose(event: CloseEvent) {
        console.log('WebSocket 연결 끊김:', event.code, event.reason);
        this.socket = null;

        if (!event.wasClean) {
            this.reconnect();
        }
    }

    private handleError(error: any) {
        console.error('WebSocket 에러:', error);
        
        // 연결이 실패한 경우에만 재연결 시도
        if (this.socket?.readyState === WebSocket.CLOSED) {
            this.reconnect();
        }
    }

    private reconnect() {
        if (this.isReconnecting || this.reconnectAttempts >= this.maxReconnectAttempts) {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('최대 재연결 시도 횟수 초과');
                this.messageHandlers.clear();
            }
            return;
        }

        this.isReconnecting = true;
        this.reconnectAttempts++;

        const timeout = this.reconnectTimeout * Math.pow(2, this.reconnectAttempts - 1);
        console.log(`${timeout}ms 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.isReconnecting = false;
            this.connect();
        }, timeout);
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.messageHandlers.clear();
        this.isReconnecting = false;
        this.reconnectAttempts = 0;
    }

    private sendSubscribeMessage(channel: string) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'subscribe',
                channel
            }));
        }
    }

    private sendUnsubscribeMessage(channel: string) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'unsubscribe',
                channel
            }));
        }
    }

    subscribe(channel: string, handler: MessageHandler) {
        this.messageHandlers.set(channel, handler);
        
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            this.connect();
        } else {
            this.sendSubscribeMessage(channel);
        }
    }

    unsubscribe(channel: string) {
        this.messageHandlers.delete(channel);
        this.sendUnsubscribeMessage(channel);

        // 더 이상 구독 중인 채널이 없으면 연결 종료
        if (this.messageHandlers.size === 0) {
            this.disconnect();
        }
    }

    subscribeToSimulation(simulationId: string, onTrade: (trade: Trade) => void) {
        const channel = `simulation:${simulationId}`;
        this.subscribe(channel, (data) => {
            if (data.type === 'trade') {
                onTrade(data.trade);
            }
        });
    }

    unsubscribeFromSimulation(simulationId: string) {
        this.unsubscribe(`simulation:${simulationId}`);
    }

    subscribeToLiveTrade(tradeId: string, onTrade: (trade: Trade) => void, onPosition: (position: Position) => void) {
        const channel = `trade:${tradeId}`;
        this.subscribe(channel, (data) => {
            if (data.type === 'trade') {
                onTrade(data.trade);
            } else if (data.type === 'position') {
                onPosition(data.position);
            }
        });
    }

    unsubscribeFromLiveTrade(tradeId: string) {
        this.unsubscribe(`trade:${tradeId}`);
    }
}

export const webSocket = new WebSocketService(); 