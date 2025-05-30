export interface User {
  id: number;
  username: string;
  nickname: string;
  email: string;
  score: number;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  nickname: string;
  email: string;
  password: string;
}