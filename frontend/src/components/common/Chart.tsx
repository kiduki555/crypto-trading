import React from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { Box, useTheme } from '@mui/material';

// Chart.js 등록
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface ChartProps {
    data: number[];
    labels?: string[];
    title?: string;
    yAxisLabel?: string;
    height?: number;
}

export const Chart: React.FC<ChartProps> = ({
    data,
    labels,
    title = '',
    yAxisLabel = '',
    height = 400
}) => {
    const theme = useTheme();

    const chartData = {
        labels: labels || data.map((_, i) => i.toString()),
        datasets: [
            {
                label: title,
                data: data,
                borderColor: theme.palette.primary.main,
                backgroundColor: theme.palette.primary.light,
                tension: 0.1
            }
        ]
    };

    const options: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: !!title,
                position: 'top' as const
            },
            title: {
                display: !!title,
                text: title
            }
        },
        scales: {
            y: {
                title: {
                    display: !!yAxisLabel,
                    text: yAxisLabel
                }
            }
        }
    };

    return (
        <Box sx={{ width: '100%', height }}>
            <Line data={chartData} options={options} />
        </Box>
    );
}; 