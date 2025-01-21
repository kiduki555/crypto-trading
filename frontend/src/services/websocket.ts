type Callback = (data: any) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private url: string;
    private callbacks: Map<string, Callback[]> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectTimeout = 1000;
    private isReconnecting = false;

    constructor() {
        this.url = import.meta.env.VITE_WS_URL || 'ws://localhost:5000/ws';
    }

    private handleOpen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.isReconnecting = false;
    };

    private handleMessage = (event: MessageEvent) => {
        try {
            const message = JSON.parse(event.data);
            const { type, data } = message;

            if (this.callbacks.has(type)) {
                this.callbacks.get(type)?.forEach(callback => callback(data));
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    };

    private handleClose = () => {
        console.log('WebSocket disconnected');
        this.ws = null;

        if (!this.isReconnecting) {
            this.reconnect();
        }
    };

    private handleError = (error: Event) => {
        console.error('WebSocket error:', error);
        if (this.ws) {
            this.ws.close();
        }
    };

    private async reconnect() {
        if (this.isReconnecting || this.reconnectAttempts >= this.maxReconnectAttempts) {
            return;
        }

        this.isReconnecting = true;
        this.reconnectAttempts++;

        const timeout = this.reconnectTimeout * Math.pow(2, this.reconnectAttempts - 1);
        console.log(`Reconnecting in ${timeout}ms (attempt ${this.reconnectAttempts})`);

        await new Promise(resolve => setTimeout(resolve, timeout));
        this.connect();
    }

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            this.ws = new WebSocket(this.url);
            this.ws.onopen = this.handleOpen;
            this.ws.onmessage = this.handleMessage;
            this.ws.onclose = this.handleClose;
            this.ws.onerror = this.handleError;
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.reconnect();
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.callbacks.clear();
    }

    subscribe(type: string, callback: Callback) {
        if (!this.callbacks.has(type)) {
            this.callbacks.set(type, []);
        }
        this.callbacks.get(type)?.push(callback);

        // 연결이 없는 경우 연결 시도
        if (!this.ws) {
            this.connect();
        }
    }

    unsubscribe(type: string, callback: Callback) {
        if (this.callbacks.has(type)) {
            const callbacks = this.callbacks.get(type) || [];
            const index = callbacks.indexOf(callback);
            if (index !== -1) {
                callbacks.splice(index, 1);
            }
            if (callbacks.length === 0) {
                this.callbacks.delete(type);
            }
        }
    }

    send(type: string, data: any) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        } else {
            console.error('WebSocket is not connected');
        }
    }
}

export const wsService = new WebSocketService();
export default wsService; 