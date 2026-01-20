/**
 * Modes API endpoints for automation sequences
 */

import { api, type ApiResponse } from './client';

export interface ModeAction {
	type: string; // device, temperature, delay
	command?: string;
	value?: unknown;
	device_id?: number;
	device_type?: string;
	rooms?: string[];
	seconds?: number; // For delay actions
}

export interface Mode {
	id: number;
	name: string;
	label: string;
	description: string | null;
	icon: string | null;
	color: string | null;
	actions: ModeAction[];
	is_active: boolean;
	is_enabled: boolean;
	display_order: number | null;
	created_at: string;
	updated_at: string | null;
	last_activated: string | null;
}

export interface ModeExecution {
	id: number;
	mode_id: number;
	mode_name: string;
	triggered_by: string;
	user_id: number | null;
	success: boolean;
	actions_total: number;
	actions_succeeded: number;
	actions_failed: number;
	error_details: { action: ModeAction; error: string }[] | null;
	executed_at: string;
}

export interface ModeActivationResult {
	mode_id: number;
	mode_name: string;
	mode_label: string;
	success: boolean;
	actions_total: number;
	actions_succeeded: number;
	actions_failed: number;
	errors: { action: ModeAction; error: string }[] | null;
}

export interface ModeCreateInput {
	name: string;
	label: string;
	description?: string;
	icon?: string;
	color?: string;
	actions: ModeAction[];
}

export interface ModeUpdateInput {
	label?: string;
	description?: string;
	icon?: string;
	color?: string;
	actions?: ModeAction[];
	is_enabled?: boolean;
	display_order?: number;
}

/**
 * Get all modes
 */
export async function getModes(enabledOnly = false): Promise<ApiResponse<Mode[]>> {
	const query = enabledOnly ? '?enabled_only=true' : '';
	return api.get<Mode[]>(`/api/v1/modes${query}`);
}

/**
 * Get the currently active mode
 */
export async function getActiveMode(): Promise<ApiResponse<Mode | null>> {
	return api.get<Mode | null>('/api/v1/modes/active');
}

/**
 * Get a mode by ID
 */
export async function getModeById(modeId: number): Promise<ApiResponse<Mode>> {
	return api.get<Mode>(`/api/v1/modes/${modeId}`);
}

/**
 * Create a new mode
 */
export async function createMode(mode: ModeCreateInput): Promise<ApiResponse<Mode>> {
	return api.post<Mode>('/api/v1/modes', mode);
}

/**
 * Update a mode
 */
export async function updateMode(
	modeId: number,
	updates: ModeUpdateInput
): Promise<ApiResponse<Mode>> {
	return api.patch<Mode>(`/api/v1/modes/${modeId}`, updates);
}

/**
 * Delete a mode
 */
export async function deleteMode(modeId: number): Promise<void> {
	return api.delete(`/api/v1/modes/${modeId}`);
}

/**
 * Activate a mode (execute all its actions)
 */
export async function activateMode(
	modeId: number,
	triggeredBy = 'user',
	useMistralBrain = false
): Promise<ApiResponse<ModeActivationResult>> {
	const params = new URLSearchParams({
		triggered_by: triggeredBy,
		use_mistral_brain: String(useMistralBrain)
	});
	return api.post<ModeActivationResult>(`/api/v1/modes/${modeId}/activate?${params}`);
}

/**
 * Deactivate all modes
 */
export async function deactivateAllModes(): Promise<ApiResponse<{ message: string }>> {
	return api.post<{ message: string }>('/api/v1/modes/deactivate');
}

/**
 * Get execution history for a mode
 */
export async function getModeExecutions(
	modeId: number,
	limit = 50
): Promise<ApiResponse<ModeExecution[]>> {
	return api.get<ModeExecution[]>(`/api/v1/modes/${modeId}/executions?limit=${limit}`);
}

/**
 * Get all mode execution history
 */
export async function getAllModeExecutions(limit = 50): Promise<ApiResponse<ModeExecution[]>> {
	return api.get<ModeExecution[]>(`/api/v1/modes/executions/all?limit=${limit}`);
}
