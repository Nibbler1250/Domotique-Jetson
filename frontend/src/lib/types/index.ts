// API Response wrapper - ALWAYS use this format
export interface ApiResponse<T> {
	data: T;
	meta: {
		timestamp: string;
	};
}

// RFC 7807 Problem Details error format
export interface ApiError {
	type: string;
	title: string;
	status: number;
	detail: string;
	instance?: string;
}

// Store state pattern - ALWAYS use this shape
export interface StoreState<T> {
	data: T | null;
	loading: boolean;
	error: string | null;
}

// WebSocket message format
export interface WsMessage<T = unknown> {
	type: string;
	payload: T;
	timestamp: string;
}

// User roles
export type UserRole = 'admin' | 'family_adult' | 'family_child' | 'kiosk';

// User type
export interface User {
	id: number;
	username: string;
	email: string | null;
	display_name: string;
	role: UserRole;
	is_active: boolean;
	theme: string | null;
	created_at: string;
	last_login: string | null;
}

// Device types
export interface Device {
	id: number;
	hubitat_id: number;
	name: string;
	label: string | null;
	type: string;
	room: string | null;
	is_favorite: boolean;
	is_hidden: boolean;
	display_order: number | null;
	icon: string | null;
	capabilities: string[] | null;
	created_at: string;
}

// Theme types
export type Theme = 'simon' | 'caroline' | 'kids' | 'kiosk' | 'light' | 'dark';
