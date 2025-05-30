import React, { useState } from 'react';
import './Auth.css';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const Auth: React.FC = () => {
    const [isLogin, setIsLogin] = useState(true);

    return (
        <div id="auth">
            <div className="buttons">
                <button
                    id="show-login"
                    className={isLogin ? 'active' : ''}
                    onClick={() => setIsLogin(true)}
                >
                    Вход
                </button>
                <button
                    id="show-register"
                    className={!isLogin ? 'active' : ''}
                    onClick={() => setIsLogin(false)}
                >
                    Регистрация
                </button>
            </div>
            {isLogin ? <LoginForm /> : <RegisterForm />}
        </div>
    );
};

export default Auth;