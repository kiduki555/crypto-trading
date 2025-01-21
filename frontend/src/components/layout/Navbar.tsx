import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
    AppBar,
    Box,
    Button,
    IconButton,
    Link,
    Toolbar,
    Typography,
    useTheme
} from '@mui/material';
import { AccountCircle } from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';

export const Navbar: React.FC = () => {
    const theme = useTheme();
    const location = useLocation();
    const { user, logout } = useAuth();

    const isActive = (path: string) => location.pathname === path;

    const navItems = [
        { path: '/backtest', label: '백테스트' },
        { path: '/simulation', label: '시뮬레이션' },
        { path: '/live', label: '라이브' }
    ];

    return (
        <AppBar position="static" color="default" elevation={1}>
            <Toolbar>
                <Typography
                    variant="h6"
                    component={RouterLink}
                    to="/"
                    sx={{
                        textDecoration: 'none',
                        color: 'inherit',
                        flexGrow: 0,
                        mr: 4
                    }}
                >
                    Crypto Trading
                </Typography>

                <Box sx={{ flexGrow: 1, display: 'flex', gap: 2 }}>
                    {navItems.map(({ path, label }) => (
                        <Link
                            key={path}
                            component={RouterLink}
                            to={path}
                            sx={{
                                textDecoration: 'none',
                                color: isActive(path)
                                    ? theme.palette.primary.main
                                    : theme.palette.text.primary,
                                fontWeight: isActive(path) ? 600 : 400
                            }}
                        >
                            {label}
                        </Link>
                    ))}
                </Box>

                <Box sx={{ flexGrow: 0 }}>
                    {user ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <IconButton
                                component={RouterLink}
                                to="/profile"
                                size="large"
                                color="inherit"
                            >
                                <AccountCircle />
                            </IconButton>
                            <Button
                                variant="outlined"
                                color="inherit"
                                onClick={logout}
                            >
                                로그아웃
                            </Button>
                        </Box>
                    ) : (
                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <Button
                                component={RouterLink}
                                to="/login"
                                variant="outlined"
                                color="inherit"
                            >
                                로그인
                            </Button>
                            <Button
                                component={RouterLink}
                                to="/register"
                                variant="contained"
                                color="primary"
                            >
                                회원가입
                            </Button>
                        </Box>
                    )}
                </Box>
            </Toolbar>
        </AppBar>
    );
}; 