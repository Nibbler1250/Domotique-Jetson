/**
 * Health API endpoints for system monitoring
 */

import { api, type ApiResponse } from './client';

export interface ComponentHealth {
	status: 'healthy' | 'degraded' | 'unhealthy' | 'disconnected' | 'unavailable' | 'timeout';
	error?: string;
	[key: string]: unknown;
}

export interface SystemHealth {
	status: 'healthy' | 'degraded' | 'unhealthy';
	timestamp: string;
	components: {
		database?: ComponentHealth;
		mqtt?: ComponentHealth & {
			broker?: string;
			devices_tracked?: number;
		};
		hubitat?: ComponentHealth & {
			url?: string;
		};
		mistral_brain?: ComponentHealth & {
			url?: string;
		};
		nodered?: ComponentHealth & {
			url?: string;
		};
	};
}

export interface DevicesHealth {
	total_devices: number;
	online: number;
	offline: number;
	low_battery_count: number;
	low_battery_devices: {
		name: string;
		battery: number;
	}[];
}

export interface ServiceStatus {
	name: string;
	url: string;
	status: 'online' | 'offline' | 'timeout' | 'error';
	latency_ms: number | null;
	http_status?: number;
	error?: string;
}

/**
 * Get comprehensive system health status
 */
export async function getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
	return api.get<SystemHealth>('/api/v1/health/system');
}

/**
 * Get device health overview
 */
export async function getDevicesHealth(): Promise<ApiResponse<DevicesHealth>> {
	return api.get<DevicesHealth>('/api/v1/health/devices');
}

/**
 * Get status of external services
 */
export async function getServicesStatus(): Promise<ApiResponse<ServiceStatus[]>> {
	return api.get<ServiceStatus[]>('/api/v1/health/services');
}
