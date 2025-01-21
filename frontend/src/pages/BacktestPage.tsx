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
    FormControl,
    InputLabel,
    Select,
    SelectChangeEvent
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { Modal } from '../components/common/Modal';
import { Loading } from '../components/common/Loading';
import { ErrorDisplay } from '../components/common/ErrorDisplay';
import { Chart } from '../components/common/Chart';
import { BacktestParams, BacktestResult } from '../types';
import { apiService } from '../services/api';

const INTERVALS = [
    { value: '5m', label: '5분' },
    { value: '15m', label: '15분' },
    { value: '30m', label: '30분' },
    { value: '1h', label: '1시간' },
    { value: '4h', label: '4시간' }
];

interface Strategy {
    name: string;
    description: string;
    default_params: Record<string, any>;
}

interface RiskManager {
    name: string;
    description: string;
    default_params: Record<string, any>;
}

const BacktestPage: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState<BacktestParams>({
        symbol: 'BTCUSDT',
        strategy: '',
        risk_management: '',
        start_date: '',
        end_date: '',
        initial_capital: 10000,
        interval: '1h'
    });

    // 데이터 상태
    const [strategies, setStrategies] = useState<Strategy[]>([]);
    const [riskManagers, setRiskManagers] = useState<RiskManager[]>([]);
    const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([]);
    const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null);

    // UI 상태
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 데이터 로드
    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                setError(null);
                const [strategiesRes, riskManagersRes, backtestsRes] = await Promise.all([
                    apiService.getStrategies(),
                    apiService.getRiskManagers(),
                    apiService.getBacktests()
                ]);
                setStrategies(strategiesRes.data.strategies || []);
                setRiskManagers(riskManagersRes.data.risk_managers || []);
                setBacktestResults(backtestsRes.data || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : '데이터 로드 실패');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSelectChange = (e: SelectChangeEvent) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            setError(null);
            const response = await apiService.createBacktest(formData);
            setBacktestResults(prev => [response.data, ...prev]);
            setIsModalOpen(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : '백테스트 실행 실패');
        } finally {
            setLoading(false);
        }
    };

    if (loading && backtestResults.length === 0) {
        return <Loading />;
    }

    if (error && backtestResults.length === 0) {
        return <ErrorDisplay error={error} />;
    }

    return (
        <Box>
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h5" component="h1">
                    백테스트
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setIsModalOpen(true)}
                >
                    새 백테스트
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
                                    <TableCell>기간</TableCell>
                                    <TableCell>총 거래</TableCell>
                                    <TableCell>승률</TableCell>
                                    <TableCell>수익률</TableCell>
                                    <TableCell>최대 낙폭</TableCell>
                                    <TableCell>샤프 비율</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {backtestResults.map((result) => (
                                    <TableRow
                                        key={result.id}
                                        hover
                                        onClick={() => setSelectedResult(result)}
                                        sx={{ cursor: 'pointer' }}
                                    >
                                        <TableCell>{result.symbol}</TableCell>
                                        <TableCell>{result.strategy}</TableCell>
                                        <TableCell>
                                            {new Date(result.start_date).toLocaleDateString()} ~{' '}
                                            {new Date(result.end_date).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell>{result.total_trades}</TableCell>
                                        <TableCell>{(result.win_rate * 100).toFixed(2)}%</TableCell>
                                        <TableCell>
                                            {((result.total_pnl / result.initial_capital) * 100).toFixed(2)}%
                                        </TableCell>
                                        <TableCell>{(result.max_drawdown * 100).toFixed(2)}%</TableCell>
                                        <TableCell>{result.sharpe_ratio.toFixed(2)}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Grid>

                {selectedResult && (
                    <Grid item xs={12}>
                        <Paper sx={{ p: 2 }}>
                            <Typography variant="h6" gutterBottom>
                                상세 결과
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={6}>
                                    <Typography variant="body1">
                                        초기 자본금: ${selectedResult.initial_capital}
                                    </Typography>
                                    <Typography variant="body1">
                                        최종 자본금: ${selectedResult.final_capital}
                                    </Typography>
                                    <Typography variant="body1">
                                        총 수익: ${selectedResult.total_pnl}
                                    </Typography>
                                    <Typography variant="body1">
                                        총 거래 횟수: {selectedResult.total_trades}
                                    </Typography>
                                    <Typography variant="body1">
                                        승률: {(selectedResult.win_rate * 100).toFixed(2)}%
                                    </Typography>
                                    <Typography variant="body1">
                                        최대 손실폭: {(selectedResult.max_drawdown * 100).toFixed(2)}%
                                    </Typography>
                                    <Typography variant="body1">
                                        샤프 비율: {selectedResult.sharpe_ratio.toFixed(2)}
                                    </Typography>
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    {selectedResult.trades && selectedResult.trades.length > 0 && (
                                        <Chart
                                            data={selectedResult.trades.map(trade => trade.pnl)}
                                            title="거래별 손익"
                                            yAxisLabel="손익($)"
                                        />
                                    )}
                                </Grid>
                            </Grid>
                        </Paper>
                    </Grid>
                )}
            </Grid>

            <Modal
                open={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="새 백테스트"
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
                        name="symbol"
                        label="거래 심볼"
                        value={formData.symbol}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    />
                    <FormControl fullWidth>
                        <InputLabel>전략</InputLabel>
                        <Select
                            name="strategy"
                            value={formData.strategy}
                            onChange={handleSelectChange}
                        >
                            {strategies.map(strategy => (
                                <MenuItem key={strategy.name} value={strategy.name}>
                                    {strategy.name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <FormControl fullWidth>
                        <InputLabel>리스크 관리</InputLabel>
                        <Select
                            name="risk_management"
                            value={formData.risk_management}
                            onChange={handleSelectChange}
                        >
                            {riskManagers.map(manager => (
                                <MenuItem key={manager.name} value={manager.name}>
                                    {manager.name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <TextField
                        name="start_date"
                        label="시작일"
                        type="datetime-local"
                        value={formData.start_date}
                        onChange={handleInputChange}
                        fullWidth
                        required
                        InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                        name="end_date"
                        label="종료일"
                        type="datetime-local"
                        value={formData.end_date}
                        onChange={handleInputChange}
                        fullWidth
                        required
                        InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                        name="initial_capital"
                        label="초기 자본금"
                        type="number"
                        value={formData.initial_capital}
                        onChange={handleInputChange}
                        fullWidth
                        required
                    />
                    <FormControl fullWidth>
                        <InputLabel>간격</InputLabel>
                        <Select
                            name="interval"
                            value={formData.interval}
                            onChange={handleSelectChange}
                        >
                            {INTERVALS.map(option => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Box>
            </Modal>
        </Box>
    );
};

export default BacktestPage; 