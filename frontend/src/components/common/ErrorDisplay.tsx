import React from 'react';
import { Alert, AlertTitle, Box, Button } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface ErrorDisplayProps {
    error: string;
    onRetry?: () => void;
    fullScreen?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
    error,
    onRetry,
    fullScreen = false
}) => {
    const content = (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                p: 2,
                maxWidth: '100%',
                width: fullScreen ? 'auto' : '400px'
            }}
        >
            <Alert
                severity="error"
                action={
                    onRetry && (
                        <Button
                            color="inherit"
                            size="small"
                            startIcon={<RefreshIcon />}
                            onClick={onRetry}
                        >
                            다시 시도
                        </Button>
                    )
                }
            >
                <AlertTitle>오류가 발생했습니다</AlertTitle>
                {error}
            </Alert>
        </Box>
    );

    if (fullScreen) {
        return (
            <Box
                sx={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    bgcolor: 'background.paper',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}
            >
                {content}
            </Box>
        );
    }

    return content;
}; 