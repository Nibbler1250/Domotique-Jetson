/**
 * Temperature API endpoints for climate control
 */

import { api, type ApiResponse } from './client';

export interface TemperatureReading {
	device_id: number;
	device_name: string;
	room: string | null;
	temperature: number | null;
	humidity: number | null;
	is_thermostat: boolean;
	heating_setpoint: number | null;
	cooling_setpoint: number | null;
	thermostat_mode: string | null;
	operating_state: string | null;
}

export interface TemperatureOverview {
	readings: TemperatureReading[];
	by_room: Record<string, TemperatureReading[]>;
	thermostats: TemperatureReading[];
	sensors: TemperatureReading[];
}

export interface RoomTemperature {
	room: string;
	temperature: number | null;
	humidity: number | null;
	devices: {
		device_id: number;
		device_name: string;
		temperature: number | null;
	}[];
}

export interface TemperatureShortcut {
	name: string;
	label: string;
	delta: number;
	duration_minutes: number | null;
}

export interface SetpointResult {
	success: boolean;
	device_id: number;
	setpoint?: number;
	previous_setpoint?: number;
	new_setpoint?: number;
	delta?: number;
	mode?: string;
}

export interface ShortcutResult {
	success: boolean;
	device_id: number;
	shortcut: string;
	previous_setpoint: number;
	new_setpoint: number;
	duration_minutes: number | null;
}

/**
 * Get temperature overview with all sensors and thermostats
 */
export async function getTemperatureOverview(): Promise<ApiResponse<TemperatureOverview>> {
	return api.get<TemperatureOverview>('/api/v1/temperature');
}

/**
 * Get temperature readings grouped by room
 */
export async function getTemperatureByRoom(): Promise<ApiResponse<RoomTemperature[]>> {
	return api.get<RoomTemperature[]>('/api/v1/temperature/rooms');
}

/**
 * Get all thermostats
 */
export async function getThermostats(): Promise<ApiResponse<TemperatureReading[]>> {
	return api.get<TemperatureReading[]>('/api/v1/temperature/thermostats');
}

/**
 * Set thermostat temperature
 */
export async function setThermostatTemperature(
	deviceId: number,
	setpoint: number,
	mode?: string
): Promise<ApiResponse<SetpointResult>> {
	return api.post<SetpointResult>(`/api/v1/temperature/${deviceId}/setpoint`, {
		setpoint,
		mode
	});
}

/**
 * Adjust thermostat temperature by delta
 */
export async function adjustTemperature(
	deviceId: number,
	delta: number
): Promise<ApiResponse<SetpointResult>> {
	return api.post<SetpointResult>(`/api/v1/temperature/${deviceId}/adjust?delta=${delta}`);
}

/**
 * Get available temperature shortcuts
 */
export async function getTemperatureShortcuts(): Promise<ApiResponse<TemperatureShortcut[]>> {
	return api.get<TemperatureShortcut[]>('/api/v1/temperature/shortcuts');
}

/**
 * Apply a temperature shortcut
 */
export async function applyTemperatureShortcut(
	deviceId: number,
	shortcutName: string
): Promise<ApiResponse<ShortcutResult>> {
	return api.post<ShortcutResult>(`/api/v1/temperature/${deviceId}/shortcut/${shortcutName}`);
}
