import { useState, useCallback } from 'react';
import { runBacktest, getBacktestResult, getBacktestResults } from '../services/api';
import { BacktestResult } from '../types';

interface UseBacktestResult {
    loading: boolean;
    error: string | null;
    results: BacktestResult[];
    currentResult: BacktestResult | null;
    runBacktest: (params: any) => Promise<string>;
    fetchResult: (id: string) => Promise<void>;
    fetchResults: (params?: any) => Promise<void>;
}

export function useBacktest(): UseBacktestResult {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<BacktestResult[]>([]);
    const [currentResult, setCurrentResult] = useState<BacktestResult | null>(null);

    const handleBacktest = useCallback(async (params: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await runBacktest(params);
            return response.data.backtest_id;
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to run backtest');
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    const handleFetchResult = useCallback(async (id: string) => {
        setLoading(true);
        setError(null);
        try {
            const response = await getBacktestResult(id);
            setCurrentResult(response.data);
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to fetch backtest result');
            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    const handleFetchResults = useCallback(async (params?: any) => {
        setLoading(true);
        setError(null);
        try {
            const response = await getBacktestResults(params);
            setResults(response.data);
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to fetch backtest results');
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
        runBacktest: handleBacktest,
        fetchResult: handleFetchResult,
        fetchResults: handleFetchResults,
    };
} 