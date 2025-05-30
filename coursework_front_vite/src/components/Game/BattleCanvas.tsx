import React, { useEffect, useRef, useState } from 'react';
import {useParams} from 'react-router-dom';
import player1Src from '../../assets/player_1.png';
import player2Src from '../../assets/player_2.png';
import enemy1Src from '../../assets/enemy_1.png';
import enemy2Src from '../../assets/enemy_2.png';
import bulletSrc from '../../assets/bullet_8x8.png';
import wallSrc from '../../assets/wall_16x16.png';
import blockSrc from '../../assets/brick_16x16.png';
import shoot1 from '../../assets/shoot_1.png';
import shoot2 from '../../assets/shoot_2.png';
import shoot3 from '../../assets/shoot_3.png';
import explosion1 from '../../assets/explosion_1.png';
import explosion2 from '../../assets/explosion_2.png';
import { isAccessTokenExpired, refreshToken } from '../../api/auth.ts';

type Tank = {
  player_id: number;
  x: number;
  y: number;
  direction: 'up' | 'down' | 'left' | 'right';
  is_alive: boolean;
};

type Bullet = {
  id: string;
  shooter_id: number;
  x: number;
  y: number;
  direction: 'up' | 'down' | 'left' | 'right';
};

type GameMap = {
  name: string;
  width: number;
  height: number;
  obstacles: string;
};

type GameState = {
  tanks: Tank[];
  bullets: Bullet[];
  map?: GameMap;
  battle_id: string;
  time_left: number | null;
};

const loadImage = (src: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
    img.src = src;
  });
};

const BattleCanvas: React.FC = () => {
    const {battleId} = useParams<{ battleId: string }>();
    const ws = useRef<WebSocket | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const item = localStorage.getItem('user');
    let currentUserId = 0
    if (item !== null) {
        currentUserId = JSON.parse(item).id;
    }

    const [images, setImages] = useState<{
        player1: HTMLImageElement;
        player2: HTMLImageElement;
        enemy1: HTMLImageElement;
        enemy2: HTMLImageElement;
        bullet: HTMLImageElement;
        wall: HTMLImageElement;
        block: HTMLImageElement;
    } | null>(null);

    const [shootFrames, setShootFrames] = useState<HTMLImageElement[]>([]);
    const [explosionFrames, setExplosionFrames] = useState<HTMLImageElement[]>([]);

    const gameStateRef = useRef<GameState | null>(null);
    const mapRef = useRef<GameMap | null>(null);
    const prevBullets = useRef<Bullet[]>([]);
    const prevTanksState = useRef<Record<number, { is_alive: boolean }>>({});
    const shouldRender = useRef<boolean>(true);
    const [frame, setFrame] = useState(0);
    const shootEffects = useRef<{ x: number; y: number; frame: number; direction: string }[]>([]);
    const explosions = useRef<{ x: number; y: number; frame: number }[]>([]);
    const [isMoving, setIsMoving] = useState(false); // для управления анимацией танк
    const moveTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);


    const isDev = true;

    // Загрузка изображений
    useEffect(() => {
        Promise.all([
            loadImage(player1Src),
            loadImage(player2Src),
            loadImage(enemy1Src),
            loadImage(enemy2Src),
            loadImage(bulletSrc),
            loadImage(wallSrc),
            loadImage(blockSrc),
            loadImage(shoot1),
            loadImage(shoot2),
            loadImage(shoot3),
            loadImage(explosion1),
            loadImage(explosion2),
        ])
            .then(([player1, player2, enemy1, enemy2, bullet, wall, block, s1, s2, s3, e1, e2]) => {
                setImages({player1, player2, enemy1, enemy2, bullet, wall, block});
                setShootFrames([s1, s2, s3]);
                setExplosionFrames([e1, e2]);
            })
            .catch((err) => console.error('Failed to load images:', err));
    }, []);

    // WebSocket
    useEffect(() => {
        if (!battleId) return;

        const connectWebSocket = async () => {
            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            let token = localStorage.getItem('access_token');

            if (!token || isAccessTokenExpired()) {
                token = await refreshToken();
                if (!token) {
                    console.error('Failed to refresh token');
                    return;
                }
            }

            const wsUrl = `${protocol}://192.168.0.104:8000/ws/battle/${battleId}/?token=${token}`;

            ws.current = new WebSocket(wsUrl);

            ws.current.onopen = () => {
                if (isDev) console.log('WebSocket connected');
            };
            ws.current.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'state') {
                    const newState = msg.data as GameState;

                    // Обновляем карту, если она пришла
                    if (newState.map) {
                        console.log('received map');
                        mapRef.current = newState.map;
                        shouldRender.current = true;
                    }

                    // Проверяем новые пули для эффектов выстрелов
                    const newBullets = newState.bullets.filter(
                        (bullet) => !prevBullets.current.find((pb) => pb.id === bullet.id)
                    );

                    newBullets.forEach((bullet) => {
                        const tank = newState.tanks.find((t) => t.player_id === bullet.shooter_id);
                        if (tank && tank.is_alive) {
                            shootEffects.current.push({
                                x: bullet.x,
                                y: bullet.y,
                                frame: 0,
                                direction: bullet.direction,
                            });
                            if (isDev) console.log(`Shoot effect at ${bullet.x},${bullet.y}`);
                        }
                    });

                    // Проверяем взрывы при уничтожении танков
                    newState.tanks.forEach((tank) => {
                        const prevTank = prevTanksState.current[tank.player_id];
                        if (prevTank && prevTank.is_alive && !tank.is_alive) {
                            explosions.current.push({
                                x: tank.x,
                                y: tank.y,
                                frame: 0,
                            });
                            if (isDev) console.log(`Explosion at ${tank.x},${tank.y}`);
                        }
                    });

                    prevBullets.current = [...newState.bullets];
                    prevTanksState.current = newState.tanks.reduce(
                        (acc, tank) => ({...acc, [tank.player_id]: {is_alive: tank.is_alive}}),
                        {}
                    );
                    // Проверяем исчезнувшие пули для взрывов
                    const removedBullets = prevBullets.current.filter(
                        (oldBullet) => !newState.bullets.find((b) => b.id === oldBullet.id)
                    );

                    removedBullets.forEach((bullet) => {
                        explosions.current.push({
                            x: bullet.x,
                            y: bullet.y,
                            frame: 0,
                        });
                        if (isDev) console.log(`Bullet exploded at ${bullet.x},${bullet.y}`);
                    });


                    gameStateRef.current = newState;
                    shouldRender.current = true;
                } else if (msg.type === 'event') {
                    if (msg.data.event === 'game_over') {
                        alert(`Game Over: ${msg.data.reason}`);
                    } else if (msg.type === 'error') {
                        console.error(msg.data.message);
                        alert(`Error: ${msg.data.message}`);
                    }
                }
            };

            ws.current.onerror = (err) => console.error('WebSocket error:', err);
            ws.current.onclose = (event) => console.log('WebSocket closed:', event);
        };

        connectWebSocket().catch((err) => console.error('WebSocket failed:', err));
        return () => {
            if (ws.current?.readyState !== WebSocket.CLOSED) {
                ws.current?.close();
            }
        };
    }, [battleId]);

// Обработка ввода
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (!ws.current || ws.current?.readyState !== WebSocket.OPEN) return;

            const key = event.key.toLowerCase();
            console.log('key', key);
            if (['arrowup', 'w', 'arrowdown', 's', 'arrowleft', 'a', 'arrowright', 'd'].includes(key)) {
                let direction: string;
                switch (key) {
                    case 'arrowup':
                    case 'w':
                        direction = 'up';
                        break;
                    case 'arrowdown':
                    case 's':
                        direction = 'down';
                        break;
                    case 'arrowleft':
                    case 'a':
                        direction = 'left';
                        break;
                    case 'arrowright':
                    case 'd':
                        direction = 'right';
                        break;
                    default:
                        return;
                }

                ws.current.send(JSON.stringify({action: 'move', direction}));
                shouldRender.current = true;

                setIsMoving(true);
                if (moveTimeout.current) clearTimeout(moveTimeout.current);
                moveTimeout.current = setTimeout(() => setIsMoving(false), 150);
            } else if (key === ' ') {
                ws.current.send(JSON.stringify({action: 'shoot'}));
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);


// Анимация танков
    useEffect(() => {
        const interval = setInterval(() => {
            if (isMoving) {
                setFrame((prev) => (prev + 1) % 2);
                shouldRender.current = true;
            }
        }, 100);

        return () => clearInterval(interval);
    }, [isMoving]);


// Эффекты
    useEffect(() => {
        const maxEffects = 50;
        const effectFrameInterval = 200;
        const updateEffects = setInterval(() => {
            shootEffects.current = shootEffects.current
                .filter((eff) => eff.frame < shootFrames.length)
                .slice(0, maxEffects);
            shootEffects.current.forEach((eff) => eff.frame += 1);

            explosions.current = explosions.current
                .filter((expl) => expl.frame < explosionFrames.length)
                .slice(0, maxEffects);
            explosions.current.forEach((expl) => expl.frame += 1);

            shouldRender.current = true;
        }, effectFrameInterval);
        return () => clearInterval(updateEffects);
    }, [shootFrames, explosionFrames]);

// Рендеринг
    useEffect(() => {
        const ctx = canvasRef.current?.getContext('2d');
        if (!ctx || !images) return;

        const tileSize = 64;
        let lastRenderTime = 0;
        const frameInterval = 20;

        const mapCanvas = document.createElement('canvas');
        mapCanvas.width = 768;
        mapCanvas.height = 576;
        const mapCtx = mapCanvas.getContext('2d')!;

        const drawMap = () => {
            if (!mapRef.current) return;
            mapCtx.clearRect(0, 0, mapCanvas.width, mapCanvas.height);
            mapCtx.fillStyle = 'black';
            mapCtx.fillRect(0, 0, mapCanvas.width, mapCanvas.height);

            const obstacles = mapRef.current.obstacles;
            const rowCount = mapRef.current.height / tileSize;
            const colCount = mapRef.current.width / tileSize;

            for (let row = 0; row < rowCount; row++) {
                for (let col = 0; col < colCount; col++) {
                    const idx = row * colCount + col;
                    const symbol = obstacles[idx];
                    const x = col * tileSize;
                    const y = row * tileSize;
                    if (symbol === 'W') {
                        mapCtx.drawImage(images.wall, x, y, tileSize, tileSize);
                    } else if (symbol === 'B') {
                        mapCtx.drawImage(images.block, x, y, tileSize, tileSize);
                    } else if (symbol === 'S') {
                        mapCtx.strokeStyle = 'yellow';
                        mapCtx.strokeRect(x, y, tileSize, tileSize);
                    }
                }
            }
        };


        const render = (timestamp: number) => {
            if (timestamp - lastRenderTime < frameInterval) {
                requestAnimationFrame(render);
                return;
            }
            lastRenderTime = timestamp;

            if (!gameStateRef.current || !mapRef.current || !shouldRender.current) {
                requestAnimationFrame(render);
                return;
            }

            drawMap();
            ctx.clearRect(0, 0, mapRef.current.width, mapRef.current.height);
            ctx.drawImage(mapCanvas, 0, 0);

            // Рендеринг танков
            gameStateRef.current.tanks.forEach((tank) => {
                if (!tank.is_alive) return;

                const isCurrent = tank.player_id === currentUserId;
                console.log('current user id', currentUserId)
                const img = isCurrent
                    ? frame === 0
                        ? images.player1
                        : images.player2
                    : frame === 0
                        ? images.enemy1
                        : images.enemy2;

                ctx.save();
                ctx.translate(tank.x, tank.y);
                const angleMap: Record<string, number> = {
                    up: 0,
                    right: Math.PI / 2,
                    down: Math.PI,
                    left: -Math.PI / 2,
                };
                ctx.rotate(angleMap[tank.direction] || 0);
                ctx.drawImage(img, -tileSize / 2, -tileSize / 2, tileSize, tileSize);
                ctx.restore();
            });

            // Рендеринг пуль
            gameStateRef.current.bullets.forEach((bullet) => {
                ctx.save();
                ctx.translate(bullet.x, bullet.y);
                const angleMap: Record<string, number> = {
                    up: 0,
                    right: Math.PI / 2,
                    down: Math.PI,
                    left: -Math.PI / 2,
                };
                ctx.rotate(angleMap[bullet.direction] || 0);
                ctx.drawImage(images.bullet, -16, -16, 32, 32);
                ctx.restore();
            });

            // ✅ Рендеринг эффектов стрельбы с проверкой
            shootEffects.current.forEach((eff) => {
                const frameImg = shootFrames[eff.frame];
                if (!frameImg) return;

                ctx.save();
                ctx.translate(eff.x, eff.y);
                const angleMap: Record<string, number> = {
                    up: 0,
                    right: Math.PI / 2,
                    down: Math.PI,
                    left: -Math.PI / 2,
                };
                ctx.rotate(angleMap[eff.direction] || 0);
                ctx.drawImage(frameImg, -tileSize / 2, -tileSize / 2, tileSize, tileSize);
                ctx.restore();

            });

            // ✅ Рендеринг взрывов с проверкой
            explosions.current.forEach((expl) => {
                const img = explosionFrames[expl.frame];
                if (!img) return;

                ctx.drawImage(img, expl.x - 48, expl.y - 48, 96, 96);

            });

            shouldRender.current = false;
            requestAnimationFrame(render);
        };

        requestAnimationFrame(render);
        return () => {

        };
    }, [images, frame, shootFrames, explosionFrames, currentUserId]);

    return (
        <canvas
            ref={canvasRef}
            width={768}
            height={576}
            style={{background: 'black'}}
        >
        </canvas>
    );
};

export default BattleCanvas;