import { setAuthToken } from './auth';
import { Room } from '../types/room';
import { api } from "./index.ts";

// Убедимся, что токен используется для всех запросов
setAuthToken(localStorage.getItem('access_token'));

// Получение списка комнат
export const getRooms = async (): Promise<Room[] | null> => {
    try {
        const response = await api.get<Room[]>('/rooms/');
        console.log('Rooms: ', response.data.length);
        console.log('Room id: ', response.data.map(room => room.id));
        return response.data;
    } catch (error) {
        console.log("Get room error", error);
        return null;
    }
};

// Создание комнаты
export interface CreateRoomData {
    map_name: string;
    max_players: number;
    mode: string;
}

export const createRoom = async (data: CreateRoomData): Promise<Room | null> => {
    try {
        console.log('Create room with data: ', data);
        const response = await api.post<Room>('/rooms/create/', data);
        return response.data;
    } catch (error) {
        console.log("Create room error", error);
        return null
    }
};

// Присоединение к комнате
export const joinRoom = async (roomId: number): Promise<string | null> => {
    try {
        const response = await api.post<{ battle_id: string }>(`/rooms/join/`, { room_id: roomId });
        return response.data.battle_id;
    } catch (error) {
        console.log("Joining room error", error);
        return null;
    }
};


// Покинуть комнату
export const leaveRoom = async (): Promise<void> => {
    try {
        api.post(`/rooms/leave`, {})
    } catch (error){
        console.log("Leave room error", error);
    }
}