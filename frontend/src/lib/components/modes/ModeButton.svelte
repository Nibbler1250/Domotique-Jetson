<script lang="ts">
	import type { Mode, ModeActivationResult } from '$lib/api/modes';
	import { activateMode } from '$lib/api/modes';

	interface Props {
		mode: Mode;
		size?: 'small' | 'medium' | 'large';
		showDescription?: boolean;
		onActivated?: (result: ModeActivationResult) => void;
		onError?: (error: Error) => void;
	}

	let { mode, size = 'medium', showDescription = false, onActivated, onError }: Props = $props();

	let loading = $state(false);
	let justActivated = $state(false);

	// Icon mapping
	const iconMap: Record<string, string> = {
		moon: '🌙',
		sun: '☀️',
		utensils: '🍽️',
		'door-closed': '🚪',
		snowflake: '❄️',
		fire: '🔥',
		home: '🏠',
		bed: '🛏️',
		tv: '📺',
		music: '🎵',
		star: '⭐',
		heart: '❤️'
	};

	// Color mapping for Tailwind classes
	const colorClasses: Record<string, { bg: string; hover: string; ring: string }> = {
		indigo: {
			bg: 'bg-indigo-600 dark:bg-indigo-700',
			hover: 'hover:bg-indigo-700 dark:hover:bg-indigo-600',
			ring: 'ring-indigo-500'
		},
		amber: {
			bg: 'bg-amber-500 dark:bg-amber-600',
			hover: 'hover:bg-amber-600 dark:hover:bg-amber-500',
			ring: 'ring-amber-500'
		},
		orange: {
			bg: 'bg-orange-500 dark:bg-orange-600',
			hover: 'hover:bg-orange-600 dark:hover:bg-orange-500',
			ring: 'ring-orange-500'
		},
		gray: {
			bg: 'bg-gray-600 dark:bg-gray-700',
			hover: 'hover:bg-gray-700 dark:hover:bg-gray-600',
			ring: 'ring-gray-500'
		},
		blue: {
			bg: 'bg-blue-600 dark:bg-blue-700',
			hover: 'hover:bg-blue-700 dark:hover:bg-blue-600',
			ring: 'ring-blue-500'
		},
		green: {
			bg: 'bg-green-600 dark:bg-green-700',
			hover: 'hover:bg-green-700 dark:hover:bg-green-600',
			ring: 'ring-green-500'
		},
		red: {
			bg: 'bg-red-600 dark:bg-red-700',
			hover: 'hover:bg-red-700 dark:hover:bg-red-600',
			ring: 'ring-red-500'
		}
	};

	let icon = $derived(iconMap[mode.icon ?? ''] ?? '⚡');
	let colors = $derived(colorClasses[mode.color ?? 'gray'] ?? colorClasses.gray);

	let sizeClasses = $derived({
		small: 'px-3 py-2 text-sm',
		medium: 'px-4 py-3 text-base',
		large: 'px-6 py-4 text-lg'
	}[size]);

	async function handleClick() {
		if (loading || !mode.is_enabled) return;

		loading = true;
		try {
			const result = await activateMode(mode.id);
			justActivated = true;
			setTimeout(() => {
				justActivated = false;
			}, 2000);
			onActivated?.(result.data);
		} catch (e) {
			console.error('Failed to activate mode:', e);
			onError?.(e as Error);
		} finally {
			loading = false;
		}
	}
</script>

<button
	onclick={handleClick}
	disabled={loading || !mode.is_enabled}
	class="relative flex items-center gap-3 rounded-xl text-white shadow-md transition-all {colors.bg} {colors.hover} {sizeClasses}
		{mode.is_active ? `ring-2 ${colors.ring} ring-offset-2 ring-offset-[var(--color-bg)]` : ''}
		{!mode.is_enabled ? 'opacity-50 cursor-not-allowed' : ''}
		{loading ? 'cursor-wait' : ''}
		{justActivated ? 'scale-95' : ''}"
	aria-label="Activer {mode.label}"
>
	<!-- Icon -->
	<span class="text-xl" class:animate-pulse={loading}>
		{icon}
	</span>

	<!-- Label and description -->
	<div class="text-left">
		<div class="font-semibold">{mode.label}</div>
		{#if showDescription && mode.description}
			<div class="text-xs opacity-80">{mode.description}</div>
		{/if}
	</div>

	<!-- Active indicator -->
	{#if mode.is_active}
		<span class="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-400 shadow">
			<span class="absolute inset-0 animate-ping rounded-full bg-green-400 opacity-75"></span>
		</span>
	{/if}

	<!-- Loading overlay -->
	{#if loading}
		<span class="absolute inset-0 flex items-center justify-center rounded-xl bg-black/20">
			<svg class="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
				></circle>
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
				></path>
			</svg>
		</span>
	{/if}

	<!-- Success flash -->
	{#if justActivated}
		<span
			class="absolute inset-0 rounded-xl bg-green-500/20 transition-opacity duration-500"
		></span>
	{/if}
</button>
