import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { Layout } from './components/layout/Layout';
import { theme } from './theme';

// 페이지 컴포넌트들
const BacktestPage = React.lazy(() => import('./pages/BacktestPage'));
const SimulationPage = React.lazy(() => import('./pages/SimulationPage'));
const LiveTradingPage = React.lazy(() => import('./pages/LiveTradingPage'));

// 로딩 컴포넌트
import { Loading } from './components/common/Loading';

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <BrowserRouter>
                <Layout>
                    <React.Suspense fallback={<Loading fullScreen />}>
                        <Routes>
                            <Route path="/" element={<Navigate to="/backtest" replace />} />
                            <Route path="/backtest" element={<BacktestPage />} />
                            <Route path="/simulation" element={<SimulationPage />} />
                            <Route path="/live" element={<LiveTradingPage />} />
                        </Routes>
                    </React.Suspense>
                </Layout>
            </BrowserRouter>
        </ThemeProvider>
    );
}

export default App; 