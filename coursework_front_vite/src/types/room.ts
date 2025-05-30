import { User } from "./auth.ts";

export interface Room {
    id: number;
    battle_id: string;
    creator: User;
    map_name: string;
    mode: 'DM' | 'TB';
    max_players: number;
    current_player_count: number;
    current_players: User[];
    is_active: boolean;
    created_at: string;
    end_time: string | null;
}