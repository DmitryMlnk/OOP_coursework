import { LoginCredentials, LoginResponse, RegisterCredentials, User } from '../types/auth';
import { api} from "./index.ts";

// Функция для установки токенов в заголовки
export const setAuthToken = (token: string | null) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete api.defaults.headers.common['Authorization'];
    }
};

export const isAccessTokenExpired = (): boolean => {
    const token = localStorage.getItem('access_token');
    if (!token) return true;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // exp в секундах
        return Date.now() >= exp;
    } catch (e) {
        console.error("Invalid JWT:", e);
        return true;
    }
};


export const refreshToken = async (): Promise<string | null> => {
    const refresh = localStorage.getItem('refresh_token');

    if (!refresh) return null;

    try {
        const response = await api.post<{ access: string }>('/authenticator/token/refresh/', { refresh });
        const newAccessToken = response.data.access;

        // Сохраняем и обновляем заголовки
        localStorage.setItem('access_token', newAccessToken);
        setAuthToken(newAccessToken);

        return newAccessToken;
    } catch (error) {
        console.error("Refresh token error:", error);
        logout();
        return null;
    }
};


// Регистрация
export const register = async (data: RegisterCredentials): Promise<User | null> => {
    try {
        const response = await api.post<User>('/authenticator/register/', data,{
            headers: {
                Authorization: '',
            }
        });
        return response.data;
    } catch (error) {
        console.log("Register error:", error);
        return null;
    }
};

// Вход
export const login = async (data: LoginCredentials): Promise<LoginResponse | null> => {
    try {
        const response = await api.post<LoginResponse>('/authenticator/token/', data);

        setAuthToken(response.data.access);

        return response.data;
    } catch (error) {
        console.log("Login Error:", error);
        return null;
    }
};

export const userInfo = async (): Promise<User | null> => {
    try {
        const response = await api.get<User>('/authenticator/me/');
        localStorage.setItem('user', JSON.stringify(response.data));
        console.log(JSON.stringify(response.data));
        return response.data;
    } catch (error) {
        console.log("UserInfo Error:", error);
        return null;
    }
}

// Выход (удаление токенов)
export const logout = () => {
    setAuthToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
};