import React, { useState } from 'react';
import './RegisterForm.css';
import { register } from '../../api/auth';
import { RegisterCredentials } from '../../types/auth';
import { useNavigate } from 'react-router-dom';

const RegisterForm: React.FC = () => {
    const [credentials, setCredentials] = useState<RegisterCredentials>({
        username: '',
        nickname: '',
        email: '',
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
            const user = await register(credentials);
            localStorage.setItem('user', JSON.stringify(user));
            navigate('/login');
        } catch (err) {
            setError((err as Error).message);
        }
    };

    return (
        <form className="register-form" onSubmit={handleSubmit}>
            <h2>Регистрация</h2>
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
                <label>Никнейм</label>
                <input
                    type="text"
                    name="nickname"
                    value={credentials.nickname}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label>Email</label>
                <input
                    type="email"
                    name="email"
                    value={credentials.email}
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
            <button type="submit">Зарегистрироваться</button>
        </form>
    );
};

export default RegisterForm;