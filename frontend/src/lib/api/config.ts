/**
 * Config API client - Export/Import configuration
 */

import { api, type ApiResponse } from './client';

export interface ConfigStats {
	modes_imported: number;
	modes_updated: number;
	automations_imported: number;
	devices_updated: number;
}

export interface ImportResult {
	success: boolean;
	message: string;
	stats: ConfigStats;
}

export interface ConfigSummary {
	version: string;
	exported_at: string;
	modes: Array<{
		name: string;
		label: string;
		actions_count: number;
		is_enabled: boolean;
	}>;
	automations_count: number;
	automations_enabled: number;
	devices_count: number;
	devices_favorite: number;
}

/**
 * Export configuration as YAML file (triggers download)
 */
export async function exportConfigYaml(): Promise<void> {
	const response = await fetch('/api/v1/config/export', {
		credentials: 'include'
	});

	if (!response.ok) {
		throw new Error('Failed to export configuration');
	}

	// Get filename from Content-Disposition header
	const disposition = response.headers.get('Content-Disposition');
	const filenameMatch = disposition?.match(/filename="(.+)"/);
	const filename = filenameMatch ? filenameMatch[1] : 'family-hub-config.yaml';

	// Download the file
	const blob = await response.blob();
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	window.URL.revokeObjectURL(url);
	document.body.removeChild(a);
}

/**
 * Import configuration from YAML file
 */
export async function importConfigYaml(file: File): Promise<ImportResult> {
	const formData = new FormData();
	formData.append('file', file);

	const response = await fetch('/api/v1/config/import', {
		method: 'POST',
		credentials: 'include',
		body: formData
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to import configuration');
	}

	const result = await response.json();
	return result.data;
}

/**
 * Get configuration summary (JSON format)
 */
export async function getConfigSummary(): Promise<ApiResponse<ConfigSummary>> {
	return api.get<ConfigSummary>('/api/v1/config/export/json');
}
