/**
 * Profiles API endpoints for themes and user preferences
 */

import { api, type ApiResponse } from './client';

export interface Profile {
	id: number;
	user_id: number;
	theme: string;
	color_scheme: string | null;
	font_size: string;
	contrast: string;
	dashboard_layout: Record<string, unknown> | null;
	favorite_devices: number[] | null;
	default_room: string | null;
	show_weather: boolean;
	show_clock: boolean;
	reduce_motion: boolean;
	high_contrast: boolean;
	large_touch_targets: boolean;
	kiosk_auto_dim: boolean;
	kiosk_dim_start: string | null;
	kiosk_dim_end: string | null;
	kiosk_dim_brightness: number;
	created_at: string;
	updated_at: string | null;
}

export interface ProfileUpdateInput {
	theme?: string;
	color_scheme?: string;
	font_size?: string;
	contrast?: string;
	dashboard_layout?: Record<string, unknown>;
	favorite_devices?: number[];
	default_room?: string;
	show_weather?: boolean;
	show_clock?: boolean;
	reduce_motion?: boolean;
	high_contrast?: boolean;
	large_touch_targets?: boolean;
	kiosk_auto_dim?: boolean;
	kiosk_dim_start?: string;
	kiosk_dim_end?: string;
	kiosk_dim_brightness?: number;
}

export interface ThemeInfo {
	id: string;
	name: string;
	description: string;
	preview_colors: {
		primary: string;
		bg: string;
		surface: string;
	};
}

/**
 * Get available themes
 */
export async function getThemes(): Promise<ApiResponse<ThemeInfo[]>> {
	return api.get<ThemeInfo[]>('/api/v1/profiles/themes');
}

/**
 * Get current user's profile
 */
export async function getMyProfile(): Promise<ApiResponse<Profile>> {
	return api.get<Profile>('/api/v1/profiles/me');
}

/**
 * Update current user's profile
 */
export async function updateMyProfile(updates: ProfileUpdateInput): Promise<ApiResponse<Profile>> {
	return api.patch<Profile>('/api/v1/profiles/me', updates);
}

/**
 * Get a user's profile (admin only or own)
 */
export async function getUserProfile(userId: number): Promise<ApiResponse<Profile>> {
	return api.get<Profile>(`/api/v1/profiles/${userId}`);
}

/**
 * Update a user's profile (admin only or own)
 */
export async function updateUserProfile(
	userId: number,
	updates: ProfileUpdateInput
): Promise<ApiResponse<Profile>> {
	return api.patch<Profile>(`/api/v1/profiles/${userId}`, updates);
}
