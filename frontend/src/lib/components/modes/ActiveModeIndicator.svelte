<script lang="ts">
	import type { Mode } from '$lib/api/modes';

	interface Props {
		mode: Mode | null;
		compact?: boolean;
	}

	let { mode, compact = false }: Props = $props();

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

	let icon = $derived(mode ? iconMap[mode.icon ?? ''] ?? '⚡' : null);
</script>

{#if mode}
	{#if compact}
		<!-- Compact version for header -->
		<div
			class="flex items-center gap-1.5 rounded-full bg-green-100 px-2 py-1 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400"
		>
			<span class="relative flex h-2 w-2">
				<span
					class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
				></span>
				<span class="relative inline-flex h-2 w-2 rounded-full bg-green-500"></span>
			</span>
			<span>{icon}</span>
			<span class="font-medium">{mode.label}</span>
		</div>
	{:else}
		<!-- Full version for dashboard -->
		<a
			href="/modes"
			class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)] p-4 ring-2 ring-green-500/50 transition-colors hover:bg-[var(--color-bg)]"
		>
			<span class="relative flex h-3 w-3">
				<span
					class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
				></span>
				<span class="relative inline-flex h-3 w-3 rounded-full bg-green-500"></span>
			</span>
			<div class="flex items-center gap-2">
				<span class="text-xl">{icon}</span>
				<div>
					<p class="text-xs text-[var(--color-text-muted)]">Mode actif</p>
					<p class="font-semibold text-[var(--color-text)]">{mode.label}</p>
				</div>
			</div>
		</a>
	{/if}
{:else}
	{#if !compact}
		<!-- No active mode -->
		<a
			href="/modes"
			class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)] p-4 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-bg)]"
		>
			<span class="text-xl">⚡</span>
			<div>
				<p class="text-xs">Aucun mode actif</p>
				<p class="font-medium text-[var(--color-text)]">Choisir un mode</p>
			</div>
		</a>
	{/if}
{/if}
