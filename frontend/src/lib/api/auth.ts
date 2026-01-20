/**
 * Auth API endpoints
 */

import { api, type ApiResponse } from './client';
import type { User } from '$types';

export interface LoginRequest {
	username: string;
	password: string;
}

export interface LoginResponse {
	user: User;
	message: string;
}

export async function login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
	return api.post<LoginResponse>('/api/v1/auth/login', credentials);
}

export async function logout(): Promise<ApiResponse<{ message: string }>> {
	return api.post<{ message: string }>('/api/v1/auth/logout');
}

export async function refreshToken(): Promise<ApiResponse<{ message: string }>> {
	return api.post<{ message: string }>('/api/v1/auth/refresh');
}

export async function getCurrentUser(): Promise<ApiResponse<User>> {
	return api.get<User>('/api/v1/auth/me');
}
