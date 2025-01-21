import { useState, useCallback, useEffect } from 'react';
import { LiveTradingParams, LiveTradingResult, ApiResponse, Trade, Position } from '../types';
import { api } from '../utils/api';
import { webSocket } from '../utils/socket';

export const useLiveTrading = () => {
    const [trades, setTrades] = useState<LiveTradingResult[]>([]);
    const [selectedTrade, setSelectedTrade] = useState<LiveTradingResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // WebSocket 연결 관리
    useEffect(() => {
        webSocket.connect();
        return () => {
            webSocket.disconnect();
        };
    }, []);

    const fetchTrades = useCallback(async (symbol?: string, strategy?: string) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.get<ApiResponse<LiveTradingResult[]>>('/trades', {
                params: { symbol, strategy }
            });
            setTrades(response.data.data);

            // 실행 중인 트레이딩에 대해 WebSocket 구독 설정
            response.data.data.forEach(trade => {
                if (trade.status === 'running') {
                    webSocket.subscribeToLiveTrade(
                        trade.trading_id,
                        (newTrade: Trade) => {
                            setTrades(prev => prev.map(t => 
                                t.trading_id === trade.trading_id
                                    ? { ...t, trades: [...t.trades, newTrade] }
                                    : t
                            ));
                        },
                        (position: Position) => {
                            setTrades(prev => prev.map(t => 
                                t.trading_id === trade.trading_id
                                    ? { 
                                        ...t, 
                                        summary: { 
                                            ...t.summary, 
                                            current_position: position 
                                        } 
                                    }
                                    : t
                            ));
                        }
                    );
                }
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : '트레이딩 목록을 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchTradeDetail = useCallback(async (tradeId: string) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.get<ApiResponse<LiveTradingResult>>(`/trades/${tradeId}`);
            setSelectedTrade(response.data.data);

            // 실행 중인 트레이딩이면 WebSocket 구독 설정
            if (response.data.data.status === 'running') {
                webSocket.subscribeToLiveTrade(
                    tradeId,
                    (trade: Trade) => {
                        setSelectedTrade(prev => 
                            prev && prev.trading_id === tradeId
                                ? { ...prev, trades: [...prev.trades, trade] }
                                : prev
                        );
                    },
                    (position: Position) => {
                        setSelectedTrade(prev => 
                            prev && prev.trading_id === tradeId
                                ? { 
                                    ...prev, 
                                    summary: { 
                                        ...prev.summary, 
                                        current_position: position 
                                    } 
                                }
                                : prev
                        );
                    }
                );
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : '트레이딩 상세 정보를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    }, []);

    const startTrading = useCallback(async (params: LiveTradingParams) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.post<ApiResponse<LiveTradingResult>>('/trades', params);
            const newTrade = response.data.data;
            setTrades(prev => [...prev, newTrade]);

            // 새로 생성된 트레이딩에 대해 WebSocket 구독 설정
            webSocket.subscribeToLiveTrade(
                newTrade.trading_id,
                (trade: Trade) => {
                    setTrades(prev => prev.map(t => 
                        t.trading_id === newTrade.trading_id
                            ? { ...t, trades: [...t.trades, trade] }
                            : t
                    ));
                },
                (position: Position) => {
                    setTrades(prev => prev.map(t => 
                        t.trading_id === newTrade.trading_id
                            ? { 
                                ...t, 
                                summary: { 
                                    ...t.summary, 
                                    current_position: position 
                                } 
                            }
                            : t
                    ));
                }
            );

            return newTrade;
        } catch (err) {
            setError(err instanceof Error ? err.message : '트레이딩 시작에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const stopTrading = useCallback(async (tradeId: string) => {
        try {
            setLoading(true);
            setError(null);
            await api.post<ApiResponse<void>>(`/trades/${tradeId}/stop`);
            setTrades(prev => prev.map(trade => 
                trade.trading_id === tradeId
                    ? { ...trade, status: 'stopped' }
                    : trade
            ));

            // WebSocket 구독 해제
            webSocket.unsubscribeFromLiveTrade(tradeId);
        } catch (err) {
            setError(err instanceof Error ? err.message : '트레이딩 중지에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const clearSelectedTrade = useCallback(() => {
        if (selectedTrade?.trading_id) {
            webSocket.unsubscribeFromLiveTrade(selectedTrade.trading_id);
        }
        setSelectedTrade(null);
    }, [selectedTrade]);

    return {
        trades,
        selectedTrade,
        loading,
        error,
        startTrading,
        stopTrading,
        fetchTrades,
        fetchTradeDetail,
        clearSelectedTrade
    };
}; 