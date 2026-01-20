/**
 * Automations API endpoints for monitoring and management
 */

import { api, type ApiResponse } from './client';

export interface Automation {
	id: number;
	brain_name: string;
	label: string;
	description: string | null;
	trigger_type: string | null;
	trigger_config: Record<string, unknown> | null;
	actions_count: number;
	is_enabled: boolean;
	last_triggered: string | null;
	last_success: boolean | null;
	trigger_count: number;
	success_count: number;
	failure_count: number;
	created_at: string;
	updated_at: string | null;
}

export interface AutomationExecution {
	id: number;
	automation_id: number | null;
	brain_name: string;
	triggered_by: string | null;
	trigger_detail: string | null;
	success: boolean;
	actions_total: number;
	actions_succeeded: number;
	actions_failed: number;
	duration_ms: number | null;
	error_message: string | null;
	error_details: { action: unknown; error: string }[] | null;
	executed_at: string;
}

export interface Alert {
	id: number;
	alert_type: string;
	severity: 'info' | 'warning' | 'error' | 'critical';
	source: string | null;
	message: string;
	details: Record<string, unknown> | null;
	is_acknowledged: boolean;
	acknowledged_by: number | null;
	acknowledged_at: string | null;
	created_at: string;
}

export interface ExecutionStats {
	period_hours: number;
	total_executions: number;
	successful: number;
	failed: number;
	success_rate: number;
}

export interface AlertCounts {
	info: number;
	warning: number;
	error: number;
	critical: number;
	total: number;
}

// ============================================================================
// Automations
// ============================================================================

/**
 * Get all automations
 */
export async function getAutomations(enabledOnly = false): Promise<ApiResponse<Automation[]>> {
	const query = enabledOnly ? '?enabled_only=true' : '';
	return api.get<Automation[]>(`/api/v1/automations${query}`);
}

/**
 * Sync automations from Mistral Brain
 */
export async function syncAutomations(): Promise<
	ApiResponse<{ synced: number; automations: Automation[] }>
> {
	return api.get<{ synced: number; automations: Automation[] }>('/api/v1/automations/sync');
}

/**
 * Get a single automation
 */
export async function getAutomation(automationId: number): Promise<ApiResponse<Automation>> {
	return api.get<Automation>(`/api/v1/automations/${automationId}`);
}

/**
 * Automation action definition
 */
export interface AutomationAction {
	device: string;
	action: string;
	value?: unknown;
}

/**
 * Full automation details including actions
 */
export interface AutomationDetails extends Automation {
	actions: AutomationAction[];
	trigger: Record<string, unknown>;
	conditions: unknown[];
}

/**
 * Get full automation details including actions from Mistral Brain
 */
export async function getAutomationDetails(automationId: number): Promise<ApiResponse<AutomationDetails>> {
	return api.get<AutomationDetails>(`/api/v1/automations/${automationId}/details`);
}

/**
 * Update automation (enable/disable)
 */
export async function updateAutomation(
	automationId: number,
	data: { is_enabled?: boolean }
): Promise<ApiResponse<Automation>> {
	return api.patch<Automation>(`/api/v1/automations/${automationId}`, data);
}

/**
 * Manually trigger an automation
 */
export async function triggerAutomation(
	automationId: number
): Promise<ApiResponse<Record<string, unknown>>> {
	return api.post<Record<string, unknown>>(`/api/v1/automations/${automationId}/trigger`);
}

// ============================================================================
// Executions
// ============================================================================

/**
 * Get all executions
 */
export async function getAllExecutions(
	limit = 50,
	offset = 0,
	successOnly?: boolean
): Promise<ApiResponse<AutomationExecution[]>> {
	const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
	if (successOnly !== undefined) {
		params.set('success_only', String(successOnly));
	}
	return api.get<AutomationExecution[]>(`/api/v1/automations/executions/all?${params}`);
}

/**
 * Get execution stats
 */
export async function getExecutionStats(hours = 24): Promise<ApiResponse<ExecutionStats>> {
	return api.get<ExecutionStats>(`/api/v1/automations/executions/stats?hours=${hours}`);
}

/**
 * Get executions for a specific automation
 */
export async function getAutomationExecutions(
	automationId: number,
	limit = 50
): Promise<ApiResponse<AutomationExecution[]>> {
	return api.get<AutomationExecution[]>(
		`/api/v1/automations/${automationId}/executions?limit=${limit}`
	);
}

/**
 * Get a single execution
 */
export async function getExecution(executionId: number): Promise<ApiResponse<AutomationExecution>> {
	return api.get<AutomationExecution>(`/api/v1/automations/executions/${executionId}`);
}

// ============================================================================
// Alerts
// ============================================================================

/**
 * Get all alerts
 */
export async function getAlerts(
	unacknowledgedOnly = false,
	severity?: string,
	limit = 50
): Promise<ApiResponse<Alert[]>> {
	const params = new URLSearchParams({ limit: String(limit) });
	if (unacknowledgedOnly) {
		params.set('unacknowledged_only', 'true');
	}
	if (severity) {
		params.set('severity', severity);
	}
	return api.get<Alert[]>(`/api/v1/automations/alerts/all?${params}`);
}

/**
 * Get alert counts
 */
export async function getAlertCounts(): Promise<ApiResponse<AlertCounts>> {
	return api.get<AlertCounts>('/api/v1/automations/alerts/counts');
}

/**
 * Acknowledge an alert
 */
export async function acknowledgeAlert(
	alertId: number,
	userId: number
): Promise<ApiResponse<Alert>> {
	return api.post<Alert>(`/api/v1/automations/alerts/${alertId}/acknowledge`, { user_id: userId });
}
