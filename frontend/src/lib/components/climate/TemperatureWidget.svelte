<script lang="ts">
	import type { TemperatureReading } from '$lib/api/temperature';
	import { setThermostatTemperature, adjustTemperature } from '$lib/api/temperature';

	interface Props {
		reading: TemperatureReading;
		size?: 'small' | 'medium' | 'large';
		showControls?: boolean;
	}

	let { reading, size = 'medium', showControls = true }: Props = $props();

	let loading = $state(false);
	let editingSetpoint = $state(false);
	let newSetpoint = $state(reading.heating_setpoint ?? 20);

	// Temperature display formatting
	let displayTemp = $derived(
		reading.temperature !== null ? `${reading.temperature.toFixed(1)}°C` : '--°C'
	);

	let setpointDisplay = $derived(
		reading.heating_setpoint !== null ? `${reading.heating_setpoint.toFixed(1)}°C` : '--'
	);

	// Operating state indicator
	let isHeating = $derived(reading.operating_state === 'heating');
	let isCooling = $derived(reading.operating_state === 'cooling');
	let isIdle = $derived(!isHeating && !isCooling);

	// Size classes
	let sizeClasses = $derived({
		small: {
			container: 'p-3',
			temp: 'text-2xl',
			setpoint: 'text-sm',
			buttons: 'h-8 w-8 text-sm'
		},
		medium: {
			container: 'p-4',
			temp: 'text-4xl',
			setpoint: 'text-base',
			buttons: 'h-10 w-10 text-lg'
		},
		large: {
			container: 'p-6',
			temp: 'text-6xl',
			setpoint: 'text-lg',
			buttons: 'h-12 w-12 text-xl'
		}
	}[size]);

	async function handleAdjust(delta: number) {
		if (loading) return;
		loading = true;
		try {
			await adjustTemperature(reading.device_id, delta);
		} catch (e) {
			console.error('Failed to adjust temperature:', e);
		} finally {
			loading = false;
		}
	}

	async function handleSetpoint() {
		if (loading) return;
		loading = true;
		try {
			await setThermostatTemperature(reading.device_id, newSetpoint);
			editingSetpoint = false;
		} catch (e) {
			console.error('Failed to set temperature:', e);
		} finally {
			loading = false;
		}
	}

	function startEditing() {
		newSetpoint = reading.heating_setpoint ?? 20;
		editingSetpoint = true;
	}
</script>

<div
	class="rounded-xl bg-[var(--color-surface)] shadow-sm transition-all hover:shadow-md {sizeClasses.container}"
	class:opacity-60={loading}
>
	<!-- Header -->
	<div class="mb-2 flex items-center justify-between">
		<div>
			<h3 class="font-medium text-[var(--color-text)]">
				{reading.device_name}
			</h3>
			{#if reading.room}
				<p class="text-xs text-[var(--color-text-muted)]">{reading.room}</p>
			{/if}
		</div>

		<!-- Operating state indicator -->
		{#if reading.is_thermostat}
			<div class="flex items-center gap-1">
				{#if isHeating}
					<span
						class="flex items-center gap-1 rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"
					>
						<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
							<path
								d="M17.66 11.2C17.43 10.9 17.15 10.64 16.89 10.38C16.22 9.78 15.46 9.35 14.82 8.72C13.33 7.26 13 4.85 13.95 3C13 3.23 12.17 3.75 11.46 4.32C8.87 6.4 7.85 10.07 9.07 13.22C9.11 13.32 9.15 13.42 9.15 13.55C9.15 13.77 9 13.97 8.8 14.05C8.57 14.15 8.33 14.09 8.14 13.93C8.08 13.88 8.04 13.83 8 13.76C6.87 12.33 6.69 10.28 7.45 8.64C5.78 10 4.87 12.3 5 14.47C5.06 14.97 5.12 15.47 5.29 15.97C5.43 16.57 5.7 17.17 6 17.7C7.08 19.43 8.95 20.67 10.96 20.92C13.1 21.19 15.39 20.8 17.03 19.32C18.86 17.66 19.5 15 18.56 12.72L18.43 12.46C18.22 12 17.66 11.2 17.66 11.2Z"
							/>
						</svg>
						Chauffe
					</span>
				{:else if isCooling}
					<span
						class="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
					>
						<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
							<path
								d="M22,11H17.83L21.07,7.76L19.66,6.34L15,11H13V9L17.66,4.34L16.24,2.93L13,6.17V2H11V6.17L7.76,2.93L6.34,4.34L11,9V11H9L4.34,6.34L2.93,7.76L6.17,11H2V13H6.17L2.93,16.24L4.34,17.66L9,13H11V15L6.34,19.66L7.76,21.07L11,17.83V22H13V17.83L16.24,21.07L17.66,19.66L13,15V13H15L19.66,17.66L21.07,16.24L17.83,13H22V11Z"
							/>
						</svg>
						Climatise
					</span>
				{:else}
					<span
						class="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-400"
					>
						Inactif
					</span>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Temperature Display -->
	<div class="flex items-end gap-4">
		<div class="{sizeClasses.temp} font-bold text-[var(--color-text)]">
			{displayTemp}
		</div>

		{#if reading.humidity !== null}
			<div class="mb-1 text-[var(--color-text-muted)] {sizeClasses.setpoint}">
				<span class="text-xs">Humidité</span>
				<span class="ml-1 font-medium">{reading.humidity}%</span>
			</div>
		{/if}
	</div>

	<!-- Thermostat Controls -->
	{#if reading.is_thermostat && showControls}
		<div class="mt-4 border-t border-[var(--color-border)] pt-4">
			{#if editingSetpoint}
				<!-- Editing mode -->
				<div class="flex items-center gap-3">
					<label for="setpoint-edit-{reading.device_id}" class="text-sm text-[var(--color-text-muted)]"
						>Consigne:</label
					>
					<input
						id="setpoint-edit-{reading.device_id}"
						type="number"
						step="0.5"
						min="15"
						max="30"
						bind:value={newSetpoint}
						disabled={loading}
						class="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-center text-[var(--color-text)]"
					/>
					<button
						onclick={handleSetpoint}
						disabled={loading}
						class="rounded-lg bg-[var(--color-primary)] px-3 py-1 text-sm text-white"
					>
						OK
					</button>
					<button
						onclick={() => (editingSetpoint = false)}
						class="rounded-lg bg-[var(--color-bg)] px-3 py-1 text-sm text-[var(--color-text)]"
					>
						Annuler
					</button>
				</div>
			{:else}
				<!-- Normal display with quick adjust -->
				<div class="flex items-center justify-between">
					<button
						onclick={startEditing}
						class="flex items-center gap-2 text-[var(--color-text)] hover:text-[var(--color-primary)]"
					>
						<span class="text-sm text-[var(--color-text-muted)]">Consigne:</span>
						<span class="{sizeClasses.setpoint} font-semibold">{setpointDisplay}</span>
					</button>

					<div class="flex items-center gap-2">
						<button
							onclick={() => handleAdjust(-0.5)}
							disabled={loading}
							class="flex items-center justify-center rounded-full bg-[var(--color-bg)] font-bold text-[var(--color-text)] transition-colors hover:bg-blue-100 dark:hover:bg-blue-900/30 {sizeClasses.buttons}"
							title="Baisser de 0.5°C"
						>
							-
						</button>
						<button
							onclick={() => handleAdjust(0.5)}
							disabled={loading}
							class="flex items-center justify-center rounded-full bg-[var(--color-bg)] font-bold text-[var(--color-text)] transition-colors hover:bg-orange-100 dark:hover:bg-orange-900/30 {sizeClasses.buttons}"
							title="Augmenter de 0.5°C"
						>
							+
						</button>
					</div>
				</div>
			{/if}

			{#if reading.thermostat_mode}
				<div class="mt-2 text-xs text-[var(--color-text-muted)]">
					Mode: {reading.thermostat_mode}
				</div>
			{/if}
		</div>
	{/if}
</div>
