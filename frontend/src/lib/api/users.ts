/**
 * Users API endpoints for user management
 */

import { api, type ApiResponse } from './client';

export interface User {
	id: number;
	username: string;
	display_name: string;
	role: 'admin' | 'family_adult' | 'family_child' | 'kiosk';
	is_active: boolean;
	created_at: string;
	last_login: string | null;
}

export interface UserCreateInput {
	username: string;
	password: string;
	display_name: string;
	role: 'admin' | 'family_adult' | 'family_child' | 'kiosk';
}

export interface UserUpdateInput {
	display_name?: string;
	password?: string;
	role?: 'admin' | 'family_adult' | 'family_child' | 'kiosk';
	is_active?: boolean;
}

/**
 * Get all users
 */
export async function getUsers(skip = 0, limit = 100): Promise<ApiResponse<User[]>> {
	return api.get<User[]>(`/api/v1/users?skip=${skip}&limit=${limit}`);
}

/**
 * Get a user by ID
 */
export async function getUserById(userId: number): Promise<ApiResponse<User>> {
	return api.get<User>(`/api/v1/users/${userId}`);
}

/**
 * Create a new user
 */
export async function createUser(user: UserCreateInput): Promise<ApiResponse<User>> {
	return api.post<User>('/api/v1/users', user);
}

/**
 * Update a user
 */
export async function updateUser(userId: number, updates: UserUpdateInput): Promise<ApiResponse<User>> {
	return api.patch<User>(`/api/v1/users/${userId}`, updates);
}

/**
 * Delete a user
 */
export async function deleteUser(userId: number): Promise<void> {
	return api.delete(`/api/v1/users/${userId}`);
}
