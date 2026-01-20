<script lang="ts">
	import type { DeviceWithState } from '$lib/api/devices';
	import {
		turnOn,
		turnOff,
		setLevel,
		lock,
		unlock,
		setHeatingSetpoint,
		toggleFavorite,
		getDevice
	} from '$lib/api/devices';
	import { devices } from '$stores/devices';

	// Refresh device state from API after a short delay (to let Hubitat update)
	async function refreshDeviceAfterCommand() {
		setTimeout(async () => {
			try {
				const response = await getDevice(device.id);
				if (response.data) {
					devices.updateDevice(response.data);
				}
			} catch (e) {
				console.error('Failed to refresh device:', e);
			}
		}, 1500);
	}

	interface Props {
		device: DeviceWithState;
	}

	let { device }: Props = $props();

	// Computed state values - check both device properties and state object
	let level = $derived(
		typeof device.level === 'number' ? device.level :
		typeof device.state?.level === 'number' ? device.state.level : null
	);
	let isOn = $derived(
		device.switch_state === 'on' ||
			device.state?.switch === 'on' ||
			device.state?.switch === true ||
			(level !== null && level > 0)
	);
	let temperature = $derived(
		device.temperature ?? (device.state?.temperature as number | undefined)
	);
	let humidity = $derived(
		device.humidity ?? (device.state?.humidity as number | undefined)
	);
	let motion = $derived(device.state?.motion === 'active');
	let contact = $derived(device.state?.contact as string | undefined);
	let batteryValue = $derived(
		typeof device.battery === 'number' ? device.battery :
		typeof device.state?.battery === 'number' ? device.state.battery : null
	);
	let lockState = $derived(device.state?.lock as string | undefined);
	let heatingSetpoint = $derived(
		device.heating_setpoint ?? (device.state?.heatingSetpoint as number | undefined)
	);
	let thermostatMode = $derived(
		device.thermostat_mode ?? (device.state?.thermostatMode as string | undefined)
	);

	// Device type helpers
	let isSwitch = $derived(
		device.capabilities?.includes('Switch') || device.type?.includes('Switch')
	);
	let isDimmer = $derived(
		device.capabilities?.includes('SwitchLevel') || device.type?.includes('Dimmer')
	);
	let isSensor = $derived(
		device.type?.includes('Sensor') ||
			device.type?.includes('Motion') ||
			device.type?.includes('Temperature')
	);
	let isThermostat = $derived(
		device.type?.includes('Thermostat') || device.capabilities?.includes('Thermostat')
	);
	let isLock = $derived(device.type?.includes('Lock') || device.capabilities?.includes('Lock'));

	let loading = $state(false);

	async function handleToggle() {
		if (loading) return;
		loading = true;
		const newState: 'on' | 'off' = isOn ? 'off' : 'on';
		try {
			if (isOn) {
				await turnOff(device.id);
			} else {
				await turnOn(device.id);
			}
			// Optimistic update after successful command
			devices.setDeviceSwitch(device.id, newState);
			// Refresh from API after delay to get real state
			refreshDeviceAfterCommand();
		} catch (e) {
			console.error('Failed to toggle device:', e);
		} finally {
			loading = false;
		}
	}

	async function handleLevelChange(event: Event) {
		if (loading) return;
		const target = event.target as HTMLInputElement;
		const newLevel = parseInt(target.value, 10);
		loading = true;
		try {
			await setLevel(device.id, newLevel);
			// Optimistic update after successful command
			devices.setDeviceLevel(device.id, newLevel);
			// Refresh from API after delay to get real state
			refreshDeviceAfterCommand();
		} catch (e) {
			console.error('Failed to set level:', e);
		} finally {
			loading = false;
		}
	}

	async function handleLockToggle() {
		if (loading) return;
		loading = true;
		try {
			if (lockState === 'locked') {
				await unlock(device.id);
			} else {
				await lock(device.id);
			}
		} catch (e) {
			console.error('Failed to toggle lock:', e);
		} finally {
			loading = false;
		}
	}

	async function handleSetpointChange(event: Event) {
		if (loading) return;
		const target = event.target as HTMLInputElement;
		const newSetpoint = parseFloat(target.value);
		loading = true;
		try {
			await setHeatingSetpoint(device.id, newSetpoint);
		} catch (e) {
			console.error('Failed to set temperature:', e);
		} finally {
			loading = false;
		}
	}

	async function handleFavoriteToggle() {
		if (loading) return;
		loading = true;
		try {
			const response = await toggleFavorite(device.id, !device.is_favorite);
			if (response.data) {
				// Update the store with new device data
				devices.updateDevice(response.data);
			}
		} catch (e) {
			console.error('Failed to toggle favorite:', e);
		} finally {
			loading = false;
		}
	}
</script>

<div
	class="rounded-xl bg-[var(--color-surface)] p-4 shadow-sm transition-all hover:shadow-md"
	class:opacity-60={loading}
>
	<!-- Header -->
	<div class="flex items-start justify-between">
		<div class="min-w-0 flex-1">
			<h3 class="truncate font-medium text-[var(--color-text)]">
				{device.label || device.name}
			</h3>
			{#if device.room}
				<p class="text-xs text-[var(--color-text-muted)]">{device.room}</p>
			{/if}
		</div>

		<button
			onclick={handleFavoriteToggle}
			disabled={loading}
			class="ml-2 text-lg transition-colors hover:scale-110"
			class:text-[var(--color-accent)]={device.is_favorite}
			class:text-gray-400={!device.is_favorite}
			title={device.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
		>
			{device.is_favorite ? '★' : '☆'}
		</button>
	</div>

	<!-- State Display -->
	<div class="mt-3">
		{#if isLock}
			<!-- Lock controls -->
			<button
				onclick={handleLockToggle}
				disabled={loading}
				class="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
				class:bg-green-600={lockState === 'locked'}
				class:text-white={lockState === 'locked'}
				class:bg-red-100={lockState !== 'locked'}
				class:text-red-700={lockState !== 'locked'}
				style="min-height: var(--touch-target);"
			>
				<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					{#if lockState === 'locked'}
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
						></path>
					{:else}
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"
						></path>
					{/if}
				</svg>
				{lockState === 'locked' ? 'Verrouillé' : 'Déverrouillé'}
			</button>
		{:else if isThermostat}
			<!-- Thermostat controls -->
			<div class="space-y-3">
				{#if temperature !== undefined}
					<div class="flex items-center gap-2">
						<span class="text-2xl font-semibold text-[var(--color-text)]">{temperature}°C</span>
						<span class="text-sm text-[var(--color-text-muted)]">actuel</span>
					</div>
				{/if}
				{#if heatingSetpoint !== undefined}
					<div class="flex items-center gap-3">
						<label for="setpoint-{device.id}" class="text-sm text-[var(--color-text-muted)]"
							>Consigne:</label
						>
						<input
							id="setpoint-{device.id}"
							type="number"
							step="0.5"
							min="15"
							max="30"
							value={heatingSetpoint}
							onchange={handleSetpointChange}
							disabled={loading}
							class="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-center text-[var(--color-text)]"
						/>
						<span class="text-sm text-[var(--color-text)]">°C</span>
					</div>
				{/if}
				{#if thermostatMode}
					<div class="text-xs text-[var(--color-text-muted)]">
						Mode: {thermostatMode}
					</div>
				{/if}
			</div>
		{:else if isSensor}
			<!-- Sensor display -->
			<div class="flex flex-wrap gap-3 text-sm">
				{#if temperature !== undefined}
					<div class="flex items-center gap-1">
						<span class="text-[var(--color-text-muted)]">Temp:</span>
						<span class="font-medium text-[var(--color-text)]">{temperature}°C</span>
					</div>
				{/if}
				{#if humidity !== undefined}
					<div class="flex items-center gap-1">
						<span class="text-[var(--color-text-muted)]">Hum:</span>
						<span class="font-medium text-[var(--color-text)]">{humidity}%</span>
					</div>
				{/if}
				{#if motion !== undefined}
					<div class="flex items-center gap-1">
						<span
							class="h-2 w-2 rounded-full"
							class:bg-green-500={motion}
							class:bg-gray-400={!motion}
						></span>
						<span class="text-[var(--color-text)]">{motion ? 'Mouvement' : 'Inactif'}</span>
					</div>
				{/if}
				{#if contact !== undefined}
					<div class="flex items-center gap-1">
						<span class="text-[var(--color-text)]">{contact === 'open' ? 'Ouvert' : 'Fermé'}</span>
					</div>
				{/if}
			</div>
		{:else if isSwitch || isDimmer}
			<!-- Switch/Dimmer controls -->
			<div class="space-y-3">
				<button
					onclick={handleToggle}
					disabled={loading}
					class="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
					class:bg-[var(--color-primary)]={isOn}
					class:text-white={isOn}
					class:bg-[var(--color-bg)]={!isOn}
					class:text-[var(--color-text)]={!isOn}
					style="min-height: var(--touch-target);"
				>
					<span
						class="h-2 w-2 rounded-full"
						class:bg-green-400={isOn}
						class:bg-gray-400={!isOn}
					></span>
					{isOn ? 'Allumé' : 'Éteint'}
				</button>

				{#if isDimmer && level !== null}
					<div class="flex items-center gap-3">
						<input
							type="range"
							min="0"
							max="100"
							value={level}
							onchange={handleLevelChange}
							disabled={loading}
							class="h-2 flex-1 cursor-pointer appearance-none rounded-lg bg-[var(--color-bg)] accent-[var(--color-primary)]"
						/>
						<span class="w-10 text-right text-sm text-[var(--color-text)]">{level}%</span>
					</div>
				{/if}
			</div>
		{:else}
			<!-- Generic device state -->
			<div class="text-sm text-[var(--color-text-muted)]">
				{device.type}
			</div>
		{/if}
	</div>

	<!-- Battery indicator -->
	{#if batteryValue !== null}
		<div class="mt-3 flex items-center gap-1 text-xs">
			<span class="text-[var(--color-text-muted)]">Batterie:</span>
			<span
				class="font-medium"
				class:text-green-500={batteryValue > 50}
				class:text-yellow-500={batteryValue > 20 && batteryValue <= 50}
				class:text-red-500={batteryValue <= 20}
			>
				{batteryValue}%
			</span>
		</div>
	{/if}
</div>
