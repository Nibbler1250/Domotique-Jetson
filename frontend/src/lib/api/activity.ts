/**
 * Activity logs API client
 */

import { api, type ApiResponse } from './client';

export interface ActivityLog {
	id: number;
	timestamp: string;
	user_id: number | null;
	username: string | null;
	action: string;
	resource_type: string | null;
	resource_id: string | null;
	resource_name: string | null;
	details: Record<string, unknown> | null;
	ip_address: string | null;
	user_agent: string | null;
}

export interface ActivitySummary {
	period_hours: number;
	total_activities: number;
	unique_users: number;
	by_action: Record<string, number>;
}

export interface ActivityActionTypes {
	auth: string[];
	devices: string[];
	modes: string[];
	automations: string[];
	config: string[];
	users: string[];
	system: string[];
}

export interface GetActivityLogsParams {
	skip?: number;
	limit?: number;
	action?: string;
	user_id?: number;
	resource_type?: string;
}

/**
 * Get activity logs with optional filtering
 */
export async function getActivityLogs(
	params: GetActivityLogsParams = {}
): Promise<ApiResponse<ActivityLog[]>> {
	const searchParams = new URLSearchParams();
	if (params.skip) searchParams.set('skip', params.skip.toString());
	if (params.limit) searchParams.set('limit', params.limit.toString());
	if (params.action) searchParams.set('action', params.action);
	if (params.user_id) searchParams.set('user_id', params.user_id.toString());
	if (params.resource_type) searchParams.set('resource_type', params.resource_type);

	const query = searchParams.toString();
	return api.get<ActivityLog[]>(`/api/v1/activity${query ? `?${query}` : ''}`);
}

/**
 * Get activity summary for a time period
 */
export async function getActivitySummary(hours: number = 24): Promise<ApiResponse<ActivitySummary>> {
	return api.get<ActivitySummary>(`/api/v1/activity/summary?hours=${hours}`);
}

/**
 * Get list of available action types
 */
export async function getActionTypes(): Promise<ApiResponse<ActivityActionTypes>> {
	return api.get<ActivityActionTypes>('/api/v1/activity/actions');
}
