/**
 * Devices API endpoints
 */

import { api, type ApiResponse } from './client';
import type { Device } from '$types';

export interface DeviceWithState extends Device {
	state: Record<string, unknown>;
}

export interface SyncResult {
	synced: number;
	devices: DeviceWithState[];
}

export interface CommandResult {
	success: boolean;
	device_id: number;
	command: string;
	value?: string;
}

export async function getDevices(options?: {
	room?: string;
	favorites?: boolean;
	includeHidden?: boolean;
}): Promise<ApiResponse<DeviceWithState[]>> {
	const params = new URLSearchParams();
	if (options?.room) params.set('room', options.room);
	if (options?.favorites) params.set('favorites', 'true');
	if (options?.includeHidden) params.set('include_hidden', 'true');

	const query = params.toString();
	return api.get<DeviceWithState[]>(`/api/v1/devices${query ? `?${query}` : ''}`);
}

export async function getDevice(deviceId: number): Promise<ApiResponse<DeviceWithState>> {
	return api.get<DeviceWithState>(`/api/v1/devices/${deviceId}`);
}

export async function getRooms(): Promise<ApiResponse<string[]>> {
	return api.get<string[]>('/api/v1/devices/rooms');
}

export async function syncDevices(): Promise<ApiResponse<SyncResult>> {
	return api.post<SyncResult>('/api/v1/devices/sync');
}

export interface RefreshStatesResult {
	updated: number;
	total: number;
	errors: Array<{ device_id: number; error: string }>;
}

export async function refreshDeviceStates(): Promise<ApiResponse<RefreshStatesResult>> {
	return api.post<RefreshStatesResult>('/api/v1/devices/refresh-states');
}

export async function sendCommand(
	deviceId: number,
	command: string,
	value?: string
): Promise<ApiResponse<CommandResult>> {
	const params = new URLSearchParams();
	params.set('command', command);
	if (value) params.set('value', value);
	return api.post<CommandResult>(`/api/v1/devices/${deviceId}/command?${params}`);
}

export async function turnOn(deviceId: number): Promise<ApiResponse<CommandResult>> {
	return api.post<CommandResult>(`/api/v1/devices/${deviceId}/on`);
}

export async function turnOff(deviceId: number): Promise<ApiResponse<CommandResult>> {
	return api.post<CommandResult>(`/api/v1/devices/${deviceId}/off`);
}

export async function setLevel(
	deviceId: number,
	level: number
): Promise<ApiResponse<CommandResult>> {
	return api.post<CommandResult>(`/api/v1/devices/${deviceId}/level/${level}`);
}

// Lock controls
export async function lock(deviceId: number): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'lock');
}

export async function unlock(deviceId: number): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'unlock');
}

// Thermostat controls
export async function setHeatingSetpoint(
	deviceId: number,
	temperature: number
): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'setHeatingSetpoint', temperature.toString());
}

export async function setCoolingSetpoint(
	deviceId: number,
	temperature: number
): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'setCoolingSetpoint', temperature.toString());
}

export async function setThermostatMode(
	deviceId: number,
	mode: 'heat' | 'cool' | 'auto' | 'off'
): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'setThermostatMode', mode);
}

// Color controls
export async function setColor(
	deviceId: number,
	hue: number,
	saturation: number
): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'setColor', JSON.stringify({ hue, saturation }));
}

export async function setColorTemperature(
	deviceId: number,
	kelvin: number
): Promise<ApiResponse<CommandResult>> {
	return sendCommand(deviceId, 'setColorTemperature', kelvin.toString());
}

// Update device metadata (favorites, room, hidden)
export async function updateDevice(
	deviceId: number,
	update: {
		room?: string;
		is_favorite?: boolean;
		is_hidden?: boolean;
	}
): Promise<ApiResponse<DeviceWithState>> {
	return api.patch<DeviceWithState>(`/api/v1/devices/${deviceId}`, update);
}

export async function toggleFavorite(
	deviceId: number,
	isFavorite: boolean
): Promise<ApiResponse<DeviceWithState>> {
	return updateDevice(deviceId, { is_favorite: isFavorite });
}
