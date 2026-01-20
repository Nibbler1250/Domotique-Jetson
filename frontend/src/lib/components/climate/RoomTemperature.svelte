<script lang="ts">
	import type { RoomTemperature } from '$lib/api/temperature';

	interface Props {
		roomTemp: RoomTemperature;
		showDevices?: boolean;
	}

	let { roomTemp, showDevices = false }: Props = $props();

	let displayTemp = $derived(
		roomTemp.temperature !== null ? `${roomTemp.temperature.toFixed(1)}°C` : '--°C'
	);

	let showingDevices = $state(false);
</script>

<div class="rounded-xl bg-[var(--color-surface)] p-4 shadow-sm">
	<div class="flex items-center justify-between">
		<div>
			<h3 class="font-medium text-[var(--color-text)]">{roomTemp.room}</h3>
			<p class="text-xs text-[var(--color-text-muted)]">
				{roomTemp.devices.length} capteur{roomTemp.devices.length > 1 ? 's' : ''}
			</p>
		</div>

		<div class="flex items-center gap-4">
			<div class="text-right">
				<div class="text-2xl font-bold text-[var(--color-text)]">{displayTemp}</div>
				{#if roomTemp.humidity !== null}
					<div class="text-xs text-[var(--color-text-muted)]">{roomTemp.humidity}% humidité</div>
				{/if}
			</div>

			{#if showDevices && roomTemp.devices.length > 1}
				<button
					onclick={() => (showingDevices = !showingDevices)}
					class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
					aria-label="Afficher ou masquer les détails des capteurs"
				>
					<svg
						class="h-5 w-5 transition-transform"
						class:rotate-180={showingDevices}
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"
						></path>
					</svg>
				</button>
			{/if}
		</div>
	</div>

	{#if showingDevices && showDevices}
		<div class="mt-3 border-t border-[var(--color-border)] pt-3">
			<div class="space-y-2">
				{#each roomTemp.devices as device}
					<div class="flex items-center justify-between text-sm">
						<span class="text-[var(--color-text-muted)]">{device.device_name}</span>
						<span class="text-[var(--color-text)]">
							{device.temperature !== null ? `${device.temperature.toFixed(1)}°C` : '--°C'}
						</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
