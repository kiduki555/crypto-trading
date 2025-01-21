import React, { useState, useEffect } from 'react';
import {
    Box,
    Button,
    Grid,
    Paper,
    Typography,
    TextField,
    MenuItem,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton
} from '@mui/material';
import { Add as AddIcon, Stop as StopIcon } from '@mui/icons-material';
import { Modal } from '../components/common/Modal';
import { Loading } from '../components/common/Loading';
import { ErrorDisplay } from '../components/common/ErrorDisplay';
import { Chart } from '../components/common/Chart';
import { useLiveTrading } from '../hooks/useLiveTrading';
import { LiveTradingParams } from '../types';

const INTERVALS = [
    { value: '5m', label: '5분' },
    { value: '15m', label: '15분' },
    { value: '30m', label: '30분' },
    { value: '1h', label: '1시간' },
    { value: '4h', label: '4시간' }
];

const STRATEGIES = [
    { value: 'bollinger', label: '볼린저 밴드' }
];

const RISK_METHODS = [
    { value: 'base', label: '기본 리스크 관리' }
];

const LiveTradingPage: React.FC = () => {
    const {
        trades,
        selectedTrade,
        loading,
        error,
        startTrading,
        stopTrading,
        fetchTrades,
        fetchTradeDetail,
        clearSelectedTrade
    } = useLiveTrading();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState<LiveTradingParams>({
        api_key: '',
        api_secret: '',
        symbol: 'BTCUSDT',
        strategy: 'bollinger',
        risk_management_method: 'base',
        interval: '1h'
    });

    useEffect(() => {
        fetchTrades();
    }, [fetchTrades]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await startTrading(formData);
            setIsModalOpen(false);
        } catch (err) {
            console.error('트레이딩 생성 실패:', err);
        }
    };

    const handleStop = async (tradeId: string) => {
        try {
            await stopTrading(tradeId);
        } catch (err) {
            console.error('트레이딩 중지 실패:', err);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    if (loading && !trades.length) {
        return <Loading />;
    }

    if (error && !trades.length) {
        return <ErrorDisplay error={error} onRetry={fetchTrades} />;
    }

    return (
        <Box>
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h5" component="h1">
                    실시간 트레이딩
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setIsModalOpen(true)}
                >
                    새 트레이딩
                </Button>
            </Box>

            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>심볼</TableCell>
                                    <TableCell>전략</TableCell>
                                    <TableCell>상태</TableCell>
                                    <TableCell>총 거래</TableCell>
                                    <TableCell>승률</TableCell>
                                    <TableCell>수익률</TableCell>
                                    <TableCell>최대 낙폭</TableCell>
                                    <TableCell>현재 포지션</TableCell>
                                    <TableCell>작업</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {trades.map((trade) => (
                                    <TableRow
                                        key={trade.trading_id}
                                        hover
                                        onClick={() => fetchTradeDetail(trade.trading_id)}
                                        sx={{ cursor: 'pointer' }}
                                    >
                                        <TableCell>{trade.symbol}</TableCell>
                                        <TableCell>{trade.strategy}</TableCell>
                                        <TableCell>{trade.status}</TableCell>
                                        <TableCell>{trade.summary?.total_trades || '-'}</TableCell>
                                        <TableCell>
                                            {trade.summary
                                                ? `${(trade.summary.win_rate * 100).toFixed(2)}%`
                                                : '-'}
                                        </TableCell>
                                        <TableCell>
                                            {trade.summary
                                                ? `${(trade.summary.profit_loss * 100).toFixed(2)}%`
                                                : '-'}
                                        </TableCell>
                                        <TableCell>
                                            {trade.summary
                                                ? `${(trade.summary.max_drawdown * 100).toFixed(2)}%`
                                                : '-'}
                                        </TableCell>
                                        <TableCell>
                                            {trade.summary?.current_position.type || '-'}
                                        </TableCell>
                                        <TableCell>
                                            {trade.status === 'running' && (
                                                <IconButton
                                                    color="error"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleStop(trade.trading_id);
                                                    }}
                                                >
                                                    <StopIcon />
                                                </IconButton>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Grid>

                {selectedTrade && (
                    <Grid item xs={12}>
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" sx={{ mb: 2 }}>
                                트레이딩 상세 결과
                            </Typography>
                            <Chart
                                data={selectedTrade.equity_curve}
                                title="자본금 변화"
                                yAxisLabel="자본금"
                            />
                        </Paper>
                    </Grid>
                )}
            </Grid>

            <Modal
                open={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="새 트레이딩"
                actions={
                    <>
                        <Button onClick={() => setIsModalOpen(false)}>
                            취소
                        </Button>
                        <Button variant="contained" onClick={handleSubmit}>
                            시작
                        </Button>
                    </>
                }
            >
                <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                        name="api_key"
                        label="API Key"
                        type="password"
                        value={formData.api_key}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    />
                    <TextField
                        name="api_secret"
                        label="API Secret"
                        type="password"
                        value={formData.api_secret}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    />
                    <TextField
                        name="symbol"
                        label="거래 심볼"
                        value={formData.symbol}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    />
                    <TextField
                        name="strategy"
                        label="전략"
                        select
                        value={formData.strategy}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    >
                        {STRATEGIES.map(option => (
                            <MenuItem key={option.value} value={option.value}>
                                {option.label}
                            </MenuItem>
                        ))}
                    </TextField>
                    <TextField
                        name="risk_management_method"
                        label="리스크 관리 방법"
                        select
                        value={formData.risk_management_method}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    >
                        {RISK_METHODS.map(option => (
                            <MenuItem key={option.value} value={option.value}>
                                {option.label}
                            </MenuItem>
                        ))}
                    </TextField>
                    <TextField
                        name="interval"
                        label="간격"
                        select
                        value={formData.interval}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    >
                        {INTERVALS.map(option => (
                            <MenuItem key={option.value} value={option.value}>
                                {option.label}
                            </MenuItem>
                        ))}
                    </TextField>
                </Box>
            </Modal>
        </Box>
    );
};

export default LiveTradingPage; 