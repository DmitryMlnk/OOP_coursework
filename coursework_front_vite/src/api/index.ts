import axios from 'axios';

export const api = axios.create({
    baseURL: 'http://192.168.0.104:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});
