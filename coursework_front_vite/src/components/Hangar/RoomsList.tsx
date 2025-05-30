import React from 'react';
import { Room } from '../../types/room';
import './RoomsList.css';

interface RoomsListProps {
  rooms: Room[];
  onJoin: (roomId: number) => void;
}

const RoomsList: React.FC<RoomsListProps> = ({ rooms, onJoin }) => {
  return (
      <div className="rooms-list">
        <h3>Доступные комнаты</h3>
        {rooms.length === 0 ? (
            <p>Нет доступных комнат</p>
        ) : (
            <ul>
              {rooms.map((room) => (
                  <li key={room.id} className="room-item">
                    <div className="room-info">
                      <p><strong>Комната номер:</strong> {room.id}</p>
                      <p><strong>Карта:</strong> {room.map_name}</p>
                      <p><strong>Создатель:</strong> {room.creator.nickname}</p>
                      <p><strong>Игроки:</strong> {room.current_player_count}/{room.max_players}</p>
                      <p><strong>Режим:</strong> {room.mode === 'DM' ? 'Deathmatch' : 'Team Battle'}</p>
                      <p><strong>Создана:</strong> {new Date(room.created_at).toLocaleString()}</p>
                    </div>
                    <button
                        className="start-button"
                        onClick={() => onJoin(room.id)}
                        disabled={room.current_player_count >= room.max_players}
                    >
                      Присоединиться
                    </button>
                  </li>
              ))}
            </ul>
        )}
      </div>
  );
};

export default RoomsList;
