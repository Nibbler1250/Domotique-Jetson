<script lang="ts">
	import type { TemperatureShortcut, TemperatureReading } from '$lib/api/temperature';
	import { applyTemperatureShortcut } from '$lib/api/temperature';

	interface Props {
		shortcuts: TemperatureShortcut[];
		thermostat: TemperatureReading;
		layout?: 'horizontal' | 'vertical' | 'grid';
	}

	let { shortcuts, thermostat, layout = 'horizontal' }: Props = $props();

	let loading = $state<string | null>(null);

	async function handleShortcut(shortcut: TemperatureShortcut) {
		if (loading) return;
		loading = shortcut.name;
		try {
			await applyTemperatureShortcut(thermostat.device_id, shortcut.name);
		} catch (e) {
			console.error('Failed to apply shortcut:', e);
		} finally {
			loading = null;
		}
	}

	// Layout classes
	let containerClass = $derived({
		horizontal: 'flex flex-wrap gap-2',
		vertical: 'flex flex-col gap-2',
		grid: 'grid grid-cols-2 gap-2'
	}[layout]);

	// Shortcut button color based on delta
	function getButtonClasses(delta: number, isLoading: boolean): string {
		const base = 'rounded-lg px-4 py-2 text-sm font-medium transition-all';
		const loading = isLoading ? 'opacity-50 cursor-wait' : '';

		if (delta > 0) {
			return `${base} ${loading} bg-orange-100 text-orange-700 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:hover:bg-orange-900/50`;
		} else {
			return `${base} ${loading} bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50`;
		}
	}

	// Icon based on shortcut type
	function getIcon(name: string, delta: number): string {
		if (name.includes('frette') || delta > 0) {
			return '🔥';
		} else if (name.includes('chaud') || delta < 0) {
			return '❄️';
		} else if (name.includes('economie')) {
			return '💰';
		} else if (name.includes('confort')) {
			return '🛋️';
		}
		return delta > 0 ? '↑' : '↓';
	}
</script>

<div class={containerClass}>
	{#each shortcuts as shortcut}
		<button
			onclick={() => handleShortcut(shortcut)}
			disabled={loading !== null}
			class={getButtonClasses(shortcut.delta, loading === shortcut.name)}
			style="min-height: var(--touch-target);"
		>
			<span class="mr-1">{getIcon(shortcut.name, shortcut.delta)}</span>
			{shortcut.label}
			{#if shortcut.duration_minutes}
				<span class="ml-1 text-xs opacity-70">({shortcut.duration_minutes} min)</span>
			{/if}
		</button>
	{/each}
</div>
