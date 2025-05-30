import React, { useState } from 'react';
import './LoginForm.css';
import { login, setAuthToken } from '../../api/auth';
import { LoginCredentials } from '../../types/auth';
import { useNavigate } from 'react-router-dom';

const LoginForm: React.FC = () => {
    const [credentials, setCredentials] = useState<LoginCredentials>({
        username: '',
        password: '',
    });
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setCredentials({ ...credentials, [e.target.name]: e.target.value });
        setError(null);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await login(credentials);
            if (response !== null) {
                localStorage.setItem('access_token', response.access);
                localStorage.setItem('refresh_token', response.refresh);
                localStorage.setItem('user', JSON.stringify(response.user));
                setAuthToken(response.access);
                navigate('/hangar');
            }
        } catch (err) {
            setError((err as Error).message);
        }
    };

    return (
        <form className="login-form" onSubmit={handleSubmit}>
            <h2>Вход</h2>
            {error && <p className="error">{error}</p>}
            <div>
                <label>Имя пользователя</label>
                <input
                    type="text"
                    name="username"
                    value={credentials.username}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label>Пароль</label>
                <input
                    type="password"
                    name="password"
                    value={credentials.password}
                    onChange={handleChange}
                    required
                />
            </div>
            <button type="submit">Войти</button>
        </form>
    );
};

export default LoginForm;