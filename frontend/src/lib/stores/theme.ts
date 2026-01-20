/**
 * Theme store for managing user theme preferences
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { getMyProfile, updateMyProfile, type Profile } from '$lib/api/profiles';

export type ThemeId = 'system' | 'light' | 'dark' | 'simon' | 'caroline' | 'kids' | 'kiosk';
export type FontSize = 'small' | 'medium' | 'large' | 'xlarge';
export type Contrast = 'normal' | 'high' | 'highest';

export interface ThemeConfig {
	id: ThemeId;
	name: string;
	colors: {
		primary: string;
		primaryHover: string;
		bg: string;
		surface: string;
		surfaceHover: string;
		border: string;
		text: string;
		textMuted: string;
		success: string;
		warning: string;
		error: string;
	};
}

// Theme definitions
export const themes: Record<ThemeId, ThemeConfig> = {
	system: {
		id: 'system',
		name: 'Système',
		colors: {
			primary: '#3b82f6',
			primaryHover: '#2563eb',
			bg: '#ffffff',
			surface: '#f3f4f6',
			surfaceHover: '#e5e7eb',
			border: '#e5e7eb',
			text: '#111827',
			textMuted: '#6b7280',
			success: '#10b981',
			warning: '#f59e0b',
			error: '#ef4444'
		}
	},
	light: {
		id: 'light',
		name: 'Clair',
		colors: {
			primary: '#3b82f6',
			primaryHover: '#2563eb',
			bg: '#ffffff',
			surface: '#f3f4f6',
			surfaceHover: '#e5e7eb',
			border: '#e5e7eb',
			text: '#111827',
			textMuted: '#6b7280',
			success: '#10b981',
			warning: '#f59e0b',
			error: '#ef4444'
		}
	},
	dark: {
		id: 'dark',
		name: 'Sombre',
		colors: {
			primary: '#60a5fa',
			primaryHover: '#3b82f6',
			bg: '#0f172a',
			surface: '#1e293b',
			surfaceHover: '#334155',
			border: '#334155',
			text: '#f1f5f9',
			textMuted: '#94a3b8',
			success: '#34d399',
			warning: '#fbbf24',
			error: '#f87171'
		}
	},
	simon: {
		id: 'simon',
		name: 'Simon',
		colors: {
			primary: '#0ea5e9',
			primaryHover: '#0284c7',
			bg: '#0c1929',
			surface: '#1a2e44',
			surfaceHover: '#264059',
			border: '#264059',
			text: '#e0f2fe',
			textMuted: '#7dd3fc',
			success: '#22d3ee',
			warning: '#fbbf24',
			error: '#f87171'
		}
	},
	caroline: {
		id: 'caroline',
		name: 'Caroline',
		colors: {
			primary: '#f472b6',
			primaryHover: '#ec4899',
			bg: '#fdf2f8',
			surface: '#fce7f3',
			surfaceHover: '#fbcfe8',
			border: '#fbcfe8',
			text: '#831843',
			textMuted: '#be185d',
			success: '#34d399',
			warning: '#fbbf24',
			error: '#f87171'
		}
	},
	kids: {
		id: 'kids',
		name: 'Enfants',
		colors: {
			primary: '#a855f7',
			primaryHover: '#9333ea',
			bg: '#faf5ff',
			surface: '#f3e8ff',
			surfaceHover: '#e9d5ff',
			border: '#e9d5ff',
			text: '#581c87',
			textMuted: '#7e22ce',
			success: '#22c55e',
			warning: '#fbbf24',
			error: '#f87171'
		}
	},
	kiosk: {
		id: 'kiosk',
		name: 'Kiosk',
		colors: {
			primary: '#10b981',
			primaryHover: '#059669',
			bg: '#000000',
			surface: '#111827',
			surfaceHover: '#1f2937',
			border: '#1f2937',
			text: '#f9fafb',
			textMuted: '#9ca3af',
			success: '#34d399',
			warning: '#fbbf24',
			error: '#f87171'
		}
	}
};

// Font size values
export const fontSizes: Record<FontSize, { base: string; scale: number }> = {
	small: { base: '14px', scale: 0.875 },
	medium: { base: '16px', scale: 1 },
	large: { base: '18px', scale: 1.125 },
	xlarge: { base: '20px', scale: 1.25 }
};

// Theme state
function createThemeStore() {
	const { subscribe, set, update } = writable<{
		theme: ThemeId;
		fontSize: FontSize;
		contrast: Contrast;
		reduceMotion: boolean;
		highContrast: boolean;
		largeTouchTargets: boolean;
		resolvedTheme: 'light' | 'dark';
		loading: boolean;
	}>({
		theme: 'system',
		fontSize: 'medium',
		contrast: 'normal',
		reduceMotion: false,
		highContrast: false,
		largeTouchTargets: false,
		resolvedTheme: 'light',
		loading: true
	});

	// Detect system preference
	function getSystemTheme(): 'light' | 'dark' {
		if (browser && window.matchMedia) {
			return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}
		return 'light';
	}

	// Resolve theme (handle 'system')
	function resolveTheme(themeId: ThemeId): 'light' | 'dark' {
		if (themeId === 'system') {
			return getSystemTheme();
		}
		// Map custom themes to their base
		const darkThemes: ThemeId[] = ['dark', 'simon', 'kiosk'];
		return darkThemes.includes(themeId) ? 'dark' : 'light';
	}

	// Apply theme to DOM
	function applyTheme(themeId: ThemeId) {
		if (!browser) return;

		const resolved = resolveTheme(themeId);
		const config = themes[themeId === 'system' ? resolved : themeId];

		// Set CSS variables
		const root = document.documentElement;
		root.style.setProperty('--color-primary', config.colors.primary);
		root.style.setProperty('--color-primary-hover', config.colors.primaryHover);
		root.style.setProperty('--color-bg', config.colors.bg);
		root.style.setProperty('--color-surface', config.colors.surface);
		root.style.setProperty('--color-surface-hover', config.colors.surfaceHover);
		root.style.setProperty('--color-border', config.colors.border);
		root.style.setProperty('--color-text', config.colors.text);
		root.style.setProperty('--color-text-muted', config.colors.textMuted);
		root.style.setProperty('--color-success', config.colors.success);
		root.style.setProperty('--color-warning', config.colors.warning);
		root.style.setProperty('--color-error', config.colors.error);

		// Set dark mode class
		root.classList.toggle('dark', resolved === 'dark');

		update((s) => ({ ...s, resolvedTheme: resolved }));
	}

	// Apply font size
	function applyFontSize(size: FontSize) {
		if (!browser) return;
		const config = fontSizes[size];
		document.documentElement.style.setProperty('--font-base', config.base);
		document.documentElement.style.setProperty('--font-scale', String(config.scale));
	}

	// Apply accessibility settings
	function applyAccessibility(reduceMotion: boolean, highContrast: boolean, largeTouchTargets: boolean) {
		if (!browser) return;
		const root = document.documentElement;
		root.classList.toggle('reduce-motion', reduceMotion);
		root.classList.toggle('high-contrast', highContrast);
		root.classList.toggle('large-touch-targets', largeTouchTargets);
	}

	return {
		subscribe,

		// Load profile from API
		async load() {
			try {
				const result = await getMyProfile();
				const profile = result.data;

				const themeId = (profile.theme || 'system') as ThemeId;
				const fontSize = (profile.font_size || 'medium') as FontSize;
				const contrast = (profile.contrast || 'normal') as Contrast;

				set({
					theme: themeId,
					fontSize,
					contrast,
					reduceMotion: profile.reduce_motion,
					highContrast: profile.high_contrast,
					largeTouchTargets: profile.large_touch_targets,
					resolvedTheme: resolveTheme(themeId),
					loading: false
				});

				applyTheme(themeId);
				applyFontSize(fontSize);
				applyAccessibility(profile.reduce_motion, profile.high_contrast, profile.large_touch_targets);
			} catch {
				// Use defaults on error
				set({
					theme: 'system',
					fontSize: 'medium',
					contrast: 'normal',
					reduceMotion: false,
					highContrast: false,
					largeTouchTargets: false,
					resolvedTheme: getSystemTheme(),
					loading: false
				});
				applyTheme('system');
			}
		},

		// Set theme
		async setTheme(themeId: ThemeId) {
			update((s) => ({ ...s, theme: themeId, resolvedTheme: resolveTheme(themeId) }));
			applyTheme(themeId);

			try {
				await updateMyProfile({ theme: themeId });
			} catch (e) {
				console.error('Failed to save theme:', e);
			}
		},

		// Set font size
		async setFontSize(size: FontSize) {
			update((s) => ({ ...s, fontSize: size }));
			applyFontSize(size);

			try {
				await updateMyProfile({ font_size: size });
			} catch (e) {
				console.error('Failed to save font size:', e);
			}
		},

		// Set accessibility options
		async setAccessibility(options: {
			reduceMotion?: boolean;
			highContrast?: boolean;
			largeTouchTargets?: boolean;
		}) {
			update((s) => ({
				...s,
				...(options.reduceMotion !== undefined && { reduceMotion: options.reduceMotion }),
				...(options.highContrast !== undefined && { highContrast: options.highContrast }),
				...(options.largeTouchTargets !== undefined && { largeTouchTargets: options.largeTouchTargets })
			}));

			const current = get({ subscribe });
			applyAccessibility(
				options.reduceMotion ?? current.reduceMotion,
				options.highContrast ?? current.highContrast,
				options.largeTouchTargets ?? current.largeTouchTargets
			);

			try {
				await updateMyProfile({
					reduce_motion: options.reduceMotion,
					high_contrast: options.highContrast,
					large_touch_targets: options.largeTouchTargets
				});
			} catch (e) {
				console.error('Failed to save accessibility:', e);
			}
		},

		// Initialize system theme listener
		initSystemListener() {
			if (!browser) return;

			const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
			const handler = () => {
				const current = get({ subscribe });
				if (current.theme === 'system') {
					update((s) => ({ ...s, resolvedTheme: getSystemTheme() }));
					applyTheme('system');
				}
			};

			mediaQuery.addEventListener('change', handler);
			return () => mediaQuery.removeEventListener('change', handler);
		}
	};
}

export const theme = createThemeStore();

// Derived store for current theme config
export const currentThemeConfig = derived(theme, ($theme) => {
	if ($theme.theme === 'system') {
		return themes[$theme.resolvedTheme];
	}
	return themes[$theme.theme];
});
