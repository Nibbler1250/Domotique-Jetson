/**
 * API client for Family Hub backend
 */

// Using proxy in dev, direct URL in prod
const API_BASE = import.meta.env.VITE_API_URL || '';

export interface ApiResponse<T> {
	data: T;
	meta: {
		timestamp: string;
		[key: string]: unknown;
	};
}

export interface ApiError {
	type: string;
	title: string;
	status: number;
	detail: string;
	instance?: string;
}

class ApiClient {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE) {
		this.baseUrl = baseUrl;
	}

	private async request<T>(
		endpoint: string,
		options: RequestInit = {}
	): Promise<ApiResponse<T>> {
		const url = `${this.baseUrl}${endpoint}`;

		const response = await fetch(url, {
			...options,
			credentials: 'include', // Include cookies
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			}
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({
				type: 'about:blank',
				title: 'Unknown Error',
				status: response.status,
				detail: response.statusText
			}));
			throw error as ApiError;
		}

		return response.json();
	}

	async get<T>(endpoint: string): Promise<ApiResponse<T>> {
		return this.request<T>(endpoint, { method: 'GET' });
	}

	async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
		return this.request<T>(endpoint, {
			method: 'POST',
			body: body ? JSON.stringify(body) : undefined
		});
	}

	async patch<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
		return this.request<T>(endpoint, {
			method: 'PATCH',
			body: JSON.stringify(body)
		});
	}

	async delete(endpoint: string): Promise<void> {
		await this.request(endpoint, { method: 'DELETE' });
	}
}

export const api = new ApiClient();
