import React, { useState, useEffect } from 'react';
import './Hangar.css';
import { logout, userInfo} from '../../api/auth';
import {getRooms, createRoom, joinRoom, CreateRoomData} from '../../api/rooms';
import { Room } from '../../types/room';
import { User } from '../../types/auth';
import { useNavigate } from 'react-router-dom';
import RoomsList from "./RoomsList.tsx";

const Hangar: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRoom, setNewRoom] = useState<CreateRoomData>({
    map_name: 'Default',
    max_players: 2,
    mode: 'DM',
  });
  const navigate = useNavigate();

  // Загружаем данные пользователя и список комнат при монтировании
  useEffect(() => {
    const fetchData = async () => {
      try {
        const user = await userInfo();
        if (user) {
          setUser(user);
        } else {
          navigate('/login');
        }
      } catch (err) {
        console.error('Ошибка при получении пользователя:', err);
        navigate('/login');
      }

      try {
        const roomsData = await getRooms();
        setRooms(roomsData || []);
      } catch (err) {
        setError((err as Error).message);
      }
    };

    fetchData();
    const interval = setInterval(() => {
      getRooms().then((roomsData) => {
        setRooms(roomsData || []);
      }).catch((err) => {
        setError((err as Error).message);
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [navigate]);



  // Обработчик выхода
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Обработчик создания комнаты
  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const createdRoom = await createRoom(newRoom);
      if (createdRoom) {
        setRooms([...rooms, createdRoom]);
        setIsModalOpen(false);
        setNewRoom({map_name: 'Default', max_players: 2, mode: 'DM'});
        navigate(`/battle/${createdRoom.battle_id}`);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  // Обработчик присоединения к комнате
  const handleJoinRoom = async (roomId: number) => {
    try {
      const battleId = await joinRoom(roomId);
      if (battleId) {
        navigate(`/battle/${battleId}`);
      } else {
        setError("Ошибка при присоединении к комнате");
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };


  if (!user) return null;

  return (
      <div className="hangar">
        <div className="hangar-container">
          {/* Кнопка выхода */}
          <button className="logout-button" onClick={handleLogout}>
            Выйти
          </button>

          {/* Информация о пользователе */}
          <div className="user-info">
            <p className="nickname">{user.nickname}</p>
            <p className="balance">Очки: {user.score}</p>
          </div>

          {/* Кнопка создания комнаты */}
          <div className="controls">
            <button className="control-button" onClick={() => setIsModalOpen(true)}>
              Создать комнату
            </button>
          </div>

          {/* Список комнат */}
          <div className="rooms-list">
            {error && <p className="error">{error}</p>}
            <RoomsList rooms={rooms} onJoin={handleJoinRoom} />
          </div>

          {/* Модальное окно для создания комнаты */}
          {isModalOpen && (
              <div className="modal-overlay">
                <div className="modal-content">
                  <button className="modal-close" onClick={() => setIsModalOpen(false)}>
                    ×
                  </button>
                  <h2>Создать комнату</h2>
                  <form onSubmit={handleCreateRoom}>
                    <div>
                      <label>Карта</label>
                      <input
                          type="text"
                          value={newRoom.map_name}
                          onChange={(e) =>
                              setNewRoom({ ...newRoom, map_name: e.target.value })
                          }
                          required
                      />
                    </div>
                    <div>
                      <label>Макс. игроков</label>
                      <input
                          type="number"
                          value={newRoom.max_players}
                          onChange={(e) =>
                              setNewRoom({ ...newRoom, max_players: parseInt(e.target.value) })
                          }
                          min="2"
                          max="8"
                          required
                      />
                    </div>
                    <div>
                      <label>Режим</label>
                      <select
                          value={newRoom.mode}
                          onChange={(e) =>
                              setNewRoom({ ...newRoom, mode: e.target.value })
                          }
                      >
                        <option value="DM">Deathmatch</option>
                        <option value="TB">Team Battle</option>
                      </select>
                    </div>
                    <button type="submit" className="control-button">
                      Создать
                    </button>
                  </form>
                </div>
              </div>
          )}
        </div>
      </div>
  );
};

export default Hangar;