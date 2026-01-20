import { writable } from 'svelte/store';
import { login as apiLogin, logout as apiLogout, getCurrentUser, type LoginRequest } from '$lib/api';
import type { User } from '$types';

export interface AuthState {
	data: User | null;
	loading: boolean;
	error: string | null;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>({
		data: null,
		loading: true,
		error: null
	});

	return {
		subscribe,

		/**
		 * Initialize auth state by checking if user is logged in
		 */
		async init() {
			update((state) => ({ ...state, loading: true }));
			try {
				const response = await getCurrentUser();
				update((state) => ({ ...state, data: response.data, loading: false, error: null }));
				return response.data;
			} catch {
				set({ data: null, loading: false, error: null });
				return null;
			}
		},

		/**
		 * Login with username and password
		 */
		async login(credentials: LoginRequest) {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const response = await apiLogin(credentials);
				update((state) => ({ ...state, data: response.data.user, loading: false }));
				return response.data.user;
			} catch (err: unknown) {
				const error = err as { detail?: string };
				const message = error?.detail || 'Login failed';
				update((state) => ({ ...state, loading: false, error: message }));
				throw err;
			}
		},

		/**
		 * Logout the current user
		 */
		async logout() {
			try {
				await apiLogout();
			} finally {
				set({ data: null, loading: false, error: null });
			}
		},

		/**
		 * Set error message
		 */
		setError: (error: string | null) => update((state) => ({ ...state, error, loading: false })),

		/**
		 * Clear error
		 */
		clearError: () => update((state) => ({ ...state, error: null })),

		/**
		 * Reset store
		 */
		reset: () => set({ data: null, loading: false, error: null })
	};
}

export const auth = createAuthStore();
