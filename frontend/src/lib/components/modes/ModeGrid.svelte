<script lang="ts">
	import type { Mode, ModeActivationResult } from '$lib/api/modes';
	import ModeButton from './ModeButton.svelte';

	interface Props {
		modes: Mode[];
		columns?: 1 | 2 | 3 | 4;
		size?: 'small' | 'medium' | 'large';
		showDescriptions?: boolean;
		onModeActivated?: (mode: Mode, result: ModeActivationResult) => void;
		onError?: (mode: Mode, error: Error) => void;
	}

	let {
		modes,
		columns = 2,
		size = 'medium',
		showDescriptions = false,
		onModeActivated,
		onError
	}: Props = $props();

	let gridClass = $derived({
		1: 'grid-cols-1',
		2: 'grid-cols-2',
		3: 'grid-cols-3',
		4: 'grid-cols-4'
	}[columns]);

	// Sort modes by display_order, then by label
	let sortedModes = $derived(
		[...modes].sort((a, b) => {
			const orderA = a.display_order ?? 999;
			const orderB = b.display_order ?? 999;
			if (orderA !== orderB) return orderA - orderB;
			return a.label.localeCompare(b.label);
		})
	);

	function handleActivated(mode: Mode, result: ModeActivationResult) {
		onModeActivated?.(mode, result);
	}

	function handleError(mode: Mode, error: Error) {
		onError?.(mode, error);
	}
</script>

<div class="grid gap-3 {gridClass}">
	{#each sortedModes as mode (mode.id)}
		<ModeButton
			{mode}
			{size}
			showDescription={showDescriptions}
			onActivated={(result) => handleActivated(mode, result)}
			onError={(error) => handleError(mode, error)}
		/>
	{/each}
</div>

{#if modes.length === 0}
	<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
		<p class="text-[var(--color-text-muted)]">Aucun mode disponible</p>
	</div>
{/if}
