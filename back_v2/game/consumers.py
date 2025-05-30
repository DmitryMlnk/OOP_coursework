import asyncio
import json
import random
import time
from urllib.parse import parse_qs
import redis.asyncio as redis
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.backends import TokenBackend

from back_v2 import settings
from rooms.models import Room, GameMap

User = get_user_model()
logger = logging.getLogger(__name__)

class BattleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.battle_id = self.scope['url_route']['kwargs']['battle_id']
            self.room_group_name = f'battle_{self.battle_id}'
            self.redis = redis.Redis(host='192.168.0.104', port=6379)

            self.user = await self.authenticate_user()
            if not self.user or not self.user.is_authenticated:
                logger.warning(f"Auth failed for battle {self.battle_id}")
                await self.close()
                return

            self.room = await self.get_room()
            if not self.room or not self.room.is_active:
                logger.warning(f"Room {self.battle_id} not found or inactive")
                await self.close()
                return

            await self.load_map_to_redis()
            await self.create_tank()
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            self.running = True
            self.map_changed = True  # Флаг для отправки карты
            self.game_loop_task = asyncio.create_task(self.game_loop())
            logger.info(f"Connected to battle {self.battle_id} for user {self.user.id}")
        except Exception as e:
            print('Error in connect:', e)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.remove_tank()
        self.running = False
        if hasattr(self, 'game_loop_task'):
            self.game_loop_task.cancel()
        if hasattr(self, 'redis'):
            await self.redis.close()
        logger.info(f"Disconnected from battle {self.battle_id}, code: {close_code}, user:{self.user.id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.debug(f"Receive: {data}")
        action = data.get('action')
        if not self.room or not self.room.is_active:
            return

        if action == 'move':
            await self.handle_move(data.get('direction'))
        elif action == 'shoot':
            await self.handle_shoot()

    async def game_loop(self):
        while self.running:
            if not self.room or not self.room.is_active:
                break

            if self.room.end_time and timezone.now() >= self.room.end_time:
                await self.set_room_inactive()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'game_event', 'data': {'event': 'game_over', 'reason': 'time_up'}}
                )
                await self.clear_room_state()
                break
            start_time = time.time()
            await self.update_bullets()
            await self.send_game_state()
            elapsed = time.time() - start_time
            if elapsed > 0.1:
                logger.warning(f"Slow loop in battle {self.battle_id}: {elapsed:.3f}s")
            await asyncio.sleep(0.01)

    async def send_game_state(self):
        if not self.room or not self.room.is_active:
            return

        tanks = await self.get_tanks()
        bullets = await self.get_bullets()
        map_data = None
        if self.map_changed:
            map_data = await self.get_map()
            self.map_changed = False
        game_state = {
            'tanks': tanks,
            'bullets': bullets,
            'battle_id': str(self.battle_id),
            'time_left': ((self.room.end_time - timezone.now()).seconds if self.room.end_time > timezone.now() else None)
        }
        if map_data:
            game_state['map'] = map_data
        try:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_state', 'data': game_state}
            )
        except Exception as e:
            logger.warning(f"Error in sending game state: {e}")

    async def game_state(self, event):
        await self.send(text_data=json.dumps({'type': 'state', 'data': event['data']}))

    async def game_event(self, event):
        await self.send(text_data=json.dumps({'type': 'event', 'data': event['data']}))

    async def authenticate_user(self):
        try:
            query_string = self.scope["query_string"].decode()
            token = parse_qs(query_string).get("token", [None])[0]
            if not token:
                return None
            UntypedToken(token)
            decoded = TokenBackend(
                algorithm='HS256',
                signing_key=settings.SECRET_KEY
            ).decode(token, verify=True)
            user_id = decoded['user_id']
            return await database_sync_to_async(User.objects.get)(id=user_id)
        except Exception as e:
            logger.error(f"Auth failed: {e}")
            return None

    @database_sync_to_async
    def get_room(self):
        try:
            return Room.objects.select_related("map_name").get(battle_id=self.battle_id, is_active=True)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def set_room_inactive(self):
        self.room.is_active = False
        self.room.save()

    @database_sync_to_async
    def get_map_data(self):
        game_map = self.room.map_name
        return {
            'name': game_map.name,
            'width': game_map.width,
            'height': game_map.height,
            'obstacles': game_map.obstacles
        }

    async def load_map_to_redis(self):
        map_data = await self.get_map_data()
        await self.redis.set(f"battle:{self.battle_id}:map", json.dumps(map_data))
        logger.info(f"Map loaded for battle {self.battle_id}")

    async def get_map(self):
        raw = await self.redis.get(f"battle:{self.battle_id}:map")
        if raw:
            return json.loads(raw)
        map_data = await self.get_map_data()
        await self.redis.set(f"battle:{self.battle_id}:map", json.dumps(map_data))
        return map_data

    async def create_tank(self):
        key = f"battle:{self.battle_id}:tanks"
        map_data = await self.get_map()
        if not map_data:
            logger.error(f"Map data not found for battle {self.battle_id}")
            raise ValueError("Map data not found")

        sprite_size = 64
        width_in_tiles = map_data['width'] // sprite_size
        height_in_tiles = map_data['height'] // sprite_size
        obstacles = map_data['obstacles']

        spawn_points = []
        for row in range(height_in_tiles):
            for col in range(width_in_tiles):
                idx = row * width_in_tiles + col
                if idx < len(obstacles) and obstacles[idx] == 'S':
                    spawn_points.append({
                        'x': col * sprite_size + sprite_size // 2,
                        'y': row * sprite_size + sprite_size // 2
                    })

        if not spawn_points:
            logger.error(f"No spawn points for battle {self.battle_id}")
            raise ValueError("No spawn points ('S') found")

        existing_tanks = await self.get_tanks()
        occupied_positions = {(tank['x'], tank['y']) for tank in existing_tanks}
        available_spawns = [
            point for point in spawn_points
            if (point['x'], point['y']) not in occupied_positions
        ]

        if not available_spawns:
            logger.error(f"No free spawn points for battle {self.battle_id}")
            raise ValueError("No free spawn points available")

        spawn_point = random.choice(available_spawns)
        tank_data = {
            'player_id': self.user.id,
            'x': spawn_point['x'],
            'y': spawn_point['y'],
            'direction': random.choice(['up', 'down', 'left', 'right']),
            'is_alive': True
        }

        async with self.redis.pipeline() as pipe:
            await pipe.hset(key, str(self.user.id), json.dumps(tank_data))
            await pipe.execute()
        logger.info(f"Tank created for user {self.user.id} at x={spawn_point['x']}, y={spawn_point['y']}")

    async def get_tanks(self):
        key = f"battle:{self.battle_id}:tanks"
        tanks = await self.redis.hgetall(key)
        return [json.loads(v) for v in tanks.values()]

    async def get_bullets(self):
        key = f"battle:{self.battle_id}:bullets"
        bullets = await self.redis.hgetall(key)
        return [json.loads(v) for v in bullets.values()]

    def is_blocked(self, tank_rect, map_data):
        sprite_size = 64
        obstacles = map_data['obstacles']
        width = map_data['width'] // sprite_size
        height = map_data['height'] // sprite_size

        for row in range(height):
            for col in range(width):
                idx = row * width + col
                cell = obstacles[idx]
                if cell not in {'W', 'B'}:
                    continue

                obstacle_rect = {
                    'x': col * sprite_size,
                    'y': row * sprite_size,
                    'w': sprite_size,
                    'h': sprite_size
                }

                if self.aabb_collision(tank_rect, obstacle_rect):
                    return True
        return False

    @staticmethod
    def aabb_collision(rect1, rect2):
        return (
            rect1['x'] < rect2['x'] + rect2['w'] and
            rect1['x'] + rect1['w'] > rect2['x'] and
            rect1['y'] < rect2['y'] + rect2['h'] and
            rect1['y'] + rect1['h'] > rect2['y']
        )

    async def handle_move(self, direction):
        tank_key = f"battle:{self.battle_id}:tanks"
        tank_raw = await self.redis.hget(tank_key, str(self.user.id))
        if not tank_raw:
            return
        tank = json.loads(tank_raw)
        map_data = await self.get_map()

        dx, dy = 0, 0
        speed = 5
        if direction == 'up':
            dy = -speed
        elif direction == 'down':
            dy = speed
        elif direction == 'left':
            dx = -speed
        elif direction == 'right':
            dx = speed

        new_x = tank['x'] + dx
        new_y = tank['y'] + dy

        tank_rect = {
            'x': new_x - 30,
            'y': new_y - 30,
            'w': 60,
            'h': 60
        }

        if not self.is_blocked(tank_rect, map_data):
            tank['x'] = max(0, min(map_data['width'], new_x))
            tank['y'] = max(0, min(map_data['height'], new_y))

        tank['direction'] = direction
        async with self.redis.pipeline() as pipe:
            await pipe.hset(tank_key, str(self.user.id), json.dumps(tank))
            await pipe.execute()

    async def handle_shoot(self):
        tank_key = f"battle:{self.battle_id}:tanks"
        bullet_key = f"battle:{self.battle_id}:bullets"
        tank_raw = await self.redis.hget(tank_key, str(self.user.id))
        if not tank_raw:
            return
        tank = json.loads(tank_raw)
        #if tank['is_alive'] == False:
        #    return
        direction = tank['direction']
        correct_x = tank['x']
        correct_y = tank['y']
        if direction == 'up':
            correct_y = tank['y'] - 32
        elif direction == 'down':
            correct_y = tank['y'] + 32
        elif direction == 'left':
            correct_x = tank['x'] - 32
        elif direction == 'right':
            correct_x = tank['x'] + 32

        bullet_id = f"{self.user.id}:{int(time.time() * 1000)}"
        bullet = {
            'id': bullet_id,
            'shooter_id': self.user.id,
            'x': correct_x,
            'y': correct_y,
            'direction': direction
        }
        async with self.redis.pipeline() as pipe:
            await pipe.hset(bullet_key, bullet_id, json.dumps(bullet))
            await pipe.expire(bullet_key, 10)  # Пули живут 10 секунд
            await pipe.execute()

    async def update_bullets(self):
        bullet_key = f"battle:{self.battle_id}:bullets"
        tank_key = f"battle:{self.battle_id}:tanks"
        map_data = await self.get_map()
        max_width, max_height = map_data['width'], map_data['height']
        sprite_size = 64

        # Кэшируем танки
        tanks = await self.redis.hgetall(tank_key)
        tanks = {k: json.loads(v) for k, v in tanks.items()}
        bullets = await self.redis.hgetall(bullet_key)
        bullets = {k: json.loads(v) for k, v in bullets.items()}
        new_bullets = {}
        bullets_to_remove = []
        map_updated = False

        async with self.redis.pipeline() as pipe:
            for bullet_id, bullet in bullets.items():
                speed = 10
                if bullet['direction'] == 'up':
                    bullet['y'] -= speed
                elif bullet['direction'] == 'down':
                    bullet['y'] += speed
                elif bullet['direction'] == 'left':
                    bullet['x'] -= speed
                elif bullet['direction'] == 'right':
                    bullet['x'] += speed

                hit = False
                for tank_id, t in tanks.items():
                    # Проверка на воскрешение
                    if not t['is_alive']:
                        if 'death_time' in t:
                            elapsed = time.time() - t['death_time']
                            if elapsed >= 2.0:
                                # Попытка респавна
                                spawn_points = await self.get_spawn_points(map_data)
                                occupied_positions = {(tank['x'], tank['y']) for tank in tanks.values() if
                                                      tank['is_alive']}
                                available_spawns = [
                                    point for point in spawn_points
                                    if (point['x'], point['y']) not in occupied_positions
                                ]
                                if available_spawns:
                                    new_spawn = random.choice(available_spawns)
                                    t['x'] = new_spawn['x']
                                    t['y'] = new_spawn['y']
                                    t['is_alive'] = True
                                    t.pop('death_time', None)
                                    await pipe.hset(tank_key, tank_id, json.dumps(t))
                        continue  # Необрабатываем как цель

                    if abs(t['x'] - bullet['x']) < 20 and abs(t['y'] - bullet['y']) < 20:
                        t['is_alive'] = False
                        t['death_time'] = time.time()
                        await pipe.hset(tank_key, tank_id, json.dumps(t))
                        hit = True
                        break

                if hit:
                    bullets_to_remove.append(bullet_id)
                    continue

                col = int(bullet['x'] // sprite_size)
                row = int(bullet['y'] // sprite_size)
                width_in_tiles = map_data['width'] // sprite_size
                index = row * width_in_tiles + col

                if not (0 <= bullet['x'] <= max_width and 0 <= bullet['y'] <= max_height):
                    bullets_to_remove.append(bullet_id)
                    continue

                try:
                    tile = map_data['obstacles'][index]
                    if tile == 'W':
                        bullets_to_remove.append(bullet_id)
                        continue
                    elif tile == 'B':
                        new_obstacles = list(map_data['obstacles'])
                        new_obstacles[index] = ' '
                        map_data['obstacles'] = ''.join(new_obstacles)
                        await pipe.set(f"battle:{self.battle_id}:map", json.dumps(map_data))
                        map_updated = True
                        bullets_to_remove.append(bullet_id)
                        continue
                    else:
                        new_bullets[bullet_id] = bullet
                except IndexError:
                    bullets_to_remove.append(bullet_id)
                    continue

            # Обновляем пули
            for bullet_id in bullets_to_remove:
                await pipe.hdel(bullet_key, bullet_id)
            for bullet_id, bullet in new_bullets.items():
                await pipe.hset(bullet_key, bullet_id, json.dumps(bullet))
            await pipe.execute()

        if map_updated:
            self.map_changed = True

    async def remove_tank(self):
        async with self.redis.pipeline() as pipe:
            await pipe.hdel(f"battle:{self.battle_id}:tanks", str(self.user.id))
            await pipe.execute()

    async def clear_room_state(self):
        async with self.redis.pipeline() as pipe:
            await pipe.delete(
                f"battle:{self.battle_id}:tanks",
                f"battle:{self.battle_id}:bullets",
                f"battle:{self.battle_id}:map"
            )
            await pipe.execute()

    async def get_spawn_points(self, map_data):
        sprite_size = 64
        width_in_tiles = map_data['width'] // sprite_size
        height_in_tiles = map_data['height'] // sprite_size
        spawn_points = []

        for row in range(height_in_tiles):
            for col in range(width_in_tiles):
                idx = row * width_in_tiles + col
                if idx < len(map_data['obstacles']) and map_data['obstacles'][idx] == 'S':
                    spawn_points.append({
                        'x': col * sprite_size + sprite_size // 2,
                        'y': row * sprite_size + sprite_size // 2
                    })
        return spawn_points