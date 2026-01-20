/**
 * Integrations API client - Check status of external services
 */

import { api, type ApiResponse } from './client';

export interface IntegrationStatus {
	name: string;
	status: 'connected' | 'disconnected' | 'error' | 'timeout' | 'unavailable' | 'not_configured';
	message: string;
	url?: string;
	broker?: string;
	port?: number;
	devices_count?: number;
	automations_count?: number;
}

export interface IntegrationsOverview {
	timestamp: string;
	overall_status: 'healthy' | 'degraded';
	connected: number;
	total: number;
	integrations: IntegrationStatus[];
}

/**
 * Get status of all integrations
 */
export async function getIntegrationsStatus(): Promise<ApiResponse<IntegrationsOverview>> {
	return api.get<IntegrationsOverview>('/api/v1/integrations');
}

/**
 * Get detailed Hubitat status
 */
export async function getHubitatStatus(): Promise<ApiResponse<IntegrationStatus>> {
	return api.get<IntegrationStatus>('/api/v1/integrations/hubitat');
}

/**
 * Get detailed MQTT status
 */
export async function getMqttStatus(): Promise<ApiResponse<IntegrationStatus>> {
	return api.get<IntegrationStatus>('/api/v1/integrations/mqtt');
}

/**
 * Get detailed Mistral Brain status
 */
export async function getBrainStatus(): Promise<ApiResponse<IntegrationStatus>> {
	return api.get<IntegrationStatus>('/api/v1/integrations/brain');
}
