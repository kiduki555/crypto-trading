import { useState, useCallback, useEffect } from 'react';
import { SimulationParams, SimulationResult } from '../types';
import { startSimulation, stopSimulation, getSimulationResult, getSimulationResults } from '../services/api';
import { wsService } from '../services/websocket';

interface UseSimulationResult {
    loading: boolean;
    error: string | null;
    results: SimulationResult[];
    currentResult: SimulationResult | null;
    startSimulation: (params: SimulationParams) => Promise<string>;
    stopSimulation: (id: string) => Promise<void>;
    fetchResult: (id: string) => Promise<void>;
    fetchResults: (params?: any) => Promise<void>;
}

export function useSimulation(): UseSimulationResult {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<SimulationResult[]>([]);
    const [currentResult, setCurrentResult] = useState<SimulationResult | null>(null);

    // WebSocket 구독 설정
    useEffect(() => {
        const handleUpdate = (data: SimulationResult) => {
            setCurrentResult(prev => {
                if (prev?.id === data.id) {
                    return data;
                }
                return prev;
            });
            
            setResults(prev => {
                const index = prev.findIndex(result => result.id === data.id);
                if (index !== -1) {
                    const newResults = [...prev];
                    newResults[index] = data;
                    return newResults;
                }
                return prev;
            });
        };

        wsService.subscribe('simulation_update', handleUpdate);
        return () => {
            wsService.unsubscribe('simulation_update', handleUpdate);
        };
    }, []);

    const handleStartSimulation = useCallback(async (params: SimulationParams) => {
        setLoading(true);
        setError(null);
        try {
            const response = await startSimulation(params);
            return response.data.simulation_id;
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to start simulation');
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    const handleStopSimulation = useCallback(async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            await stopSimulation(id);
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to stop simulation');
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    const handleFetchResult = useCallback(async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await getSimulationResult(id);
            setCurrentResult(response.data);
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to fetch simulation result');
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    const handleFetchResults = useCallback(async (params?: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await getSimulationResults(params);
            setResults(response.data);
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to fetch simulation results');
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        results,
        currentResult,
        startSimulation: handleStartSimulation,
        stopSimulation: handleStopSimulation,
        fetchResult: handleFetchResult,
        fetchResults: handleFetchResults,
    };
} 