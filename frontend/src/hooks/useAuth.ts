import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, ApiResponse } from '../types';
import { api } from '../utils/api';

interface LoginParams {
    email: string;
    password: string;
}

interface RegisterParams {
    username: string;
    email: string;
    password: string;
}

export const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    // 초기 사용자 정보 로드
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            fetchUser();
        }
    }, []);

    const fetchUser = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.get<ApiResponse<User>>('/auth/me');
            setUser(response.data.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : '사용자 정보를 불러오는데 실패했습니다.');
            localStorage.removeItem('token');
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const login = useCallback(async (params: LoginParams) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.post<ApiResponse<{ token: string }>>('/auth/login', params);
            localStorage.setItem('token', response.data.data.token);
            await fetchUser();
            navigate('/');
        } catch (err) {
            setError(err instanceof Error ? err.message : '로그인에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [navigate, fetchUser]);

    const register = useCallback(async (params: RegisterParams) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.post<ApiResponse<{ token: string }>>('/auth/register', params);
            localStorage.setItem('token', response.data.data.token);
            await fetchUser();
            navigate('/');
        } catch (err) {
            setError(err instanceof Error ? err.message : '회원가입에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [navigate, fetchUser]);

    const logout = useCallback(() => {
        localStorage.removeItem('token');
        setUser(null);
        navigate('/login');
    }, [navigate]);

    const updateProfile = useCallback(async (params: Partial<User>) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.put<ApiResponse<User>>('/auth/profile', params);
            setUser(response.data.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : '프로필 업데이트에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const addApiKey = useCallback(async (apiKey: string, apiSecret: string) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.post<ApiResponse<User>>('/auth/api-keys', {
                api_key: apiKey,
                api_secret: apiSecret
            });
            setUser(response.data.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'API 키 추가에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const removeApiKey = useCallback(async (apiKey: string) => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.delete<ApiResponse<User>>(`/auth/api-keys/${apiKey}`);
            setUser(response.data.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'API 키 삭제에 실패했습니다.');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        user,
        loading,
        error,
        login,
        register,
        logout,
        updateProfile,
        addApiKey,
        removeApiKey
    };
}; 