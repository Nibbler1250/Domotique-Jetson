<script lang="ts">
	import type { DeviceWithState } from '$lib/api/devices';
	import DeviceCard from './DeviceCard.svelte';

	interface Props {
		devices: DeviceWithState[];
		title?: string;
		emptyMessage?: string;
	}

	let { devices, title, emptyMessage = 'Aucun appareil' }: Props = $props();
</script>

<div class="space-y-4">
	{#if title}
		<h2 class="text-lg font-semibold text-[var(--color-text)]">{title}</h2>
	{/if}

	{#if devices.length === 0}
		<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
			<p class="text-[var(--color-text-muted)]">{emptyMessage}</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
			{#each devices as device (device.id)}
				<DeviceCard {device} />
			{/each}
		</div>
	{/if}
</div>
