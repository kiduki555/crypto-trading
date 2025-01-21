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
import { useSimulation } from '../hooks/useSimulation';
import { SimulationParams } from '../types';

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

const SimulationPage: React.FC = () => {
    const {
        simulations,
        selectedSimulation,
        loading,
        error,
        createSimulation,
        stopSimulation,
        fetchSimulations,
        fetchSimulationDetail,
        clearSelectedSimulation
    } = useSimulation();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [formData, setFormData] = useState<SimulationParams>({
        balance: 10000,
        symbol: 'BTCUSDT',
        strategy: 'bollinger',
        risk_management_method: 'base',
        interval: '1h'
    });

    useEffect(() => {
        fetchSimulations();
    }, [fetchSimulations]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createSimulation(formData);
            setIsModalOpen(false);
        } catch (err) {
            console.error('시뮬레이션 생성 실패:', err);
        }
    };

    const handleStop = async (simulationId: string) => {
        try {
            await stopSimulation(simulationId);
        } catch (err) {
            console.error('시뮬레이션 중지 실패:', err);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    if (loading && !simulations.length) {
        return <Loading />;
    }

    if (error && !simulations.length) {
        return <ErrorDisplay error={error} onRetry={fetchSimulations} />;
    }

    return (
        <Box>
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h5" component="h1">
                    시뮬레이션
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setIsModalOpen(true)}
                >
                    새 시뮬레이션
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
                                    <TableCell>작업</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {simulations.map((simulation) => (
                                    <TableRow
                                        key={simulation.simulation_id}
                                        hover
                                        onClick={() => fetchSimulationDetail(simulation.simulation_id)}
                                        sx={{ cursor: 'pointer' }}
                                    >
                                        <TableCell>{simulation.params.symbol}</TableCell>
                                        <TableCell>{simulation.params.strategy}</TableCell>
                                        <TableCell>{simulation.summary ? '완료' : '실행 중'}</TableCell>
                                        <TableCell>{simulation.summary?.total_trades || '-'}</TableCell>
                                        <TableCell>
                                            {simulation.summary
                                                ? `${(simulation.summary.win_rate * 100).toFixed(2)}%`
                                                : '-'}
                                        </TableCell>
                                        <TableCell>
                                            {simulation.summary
                                                ? `${(simulation.summary.profit_loss * 100).toFixed(2)}%`
                                                : '-'}
                                        </TableCell>
                                        <TableCell>
                                            {simulation.summary
                                                ? `${(simulation.summary.max_drawdown * 100).toFixed(2)}%`
                                                : '-'}
                                        </TableCell>
                                        <TableCell>
                                            {!simulation.summary && (
                                                <IconButton
                                                    color="error"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleStop(simulation.simulation_id);
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

                {selectedSimulation && (
                    <Grid item xs={12}>
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" sx={{ mb: 2 }}>
                                시뮬레이션 상세 결과
                            </Typography>
                            <Chart
                                data={selectedSimulation.equity_curve}
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
                title="새 시뮬레이션"
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
                        name="balance"
                        label="초기 자본금"
                        type="number"
                        value={formData.balance}
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

export default SimulationPage; 