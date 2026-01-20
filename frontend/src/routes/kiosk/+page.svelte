<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { websocket } from '$lib/stores/websocket';
	import { devices, favoriteDevices } from '$lib/stores/devices';
	import { getActiveMode, type Mode } from '$lib/api/modes';
	import { getSystemHealth, type SystemHealth } from '$lib/api/health';

	let wsConnected = $derived($websocket.connected);
	let favorites = $derived($favoriteDevices);

	// Clock state
	let currentTime = $state(new Date());
	let clockInterval: ReturnType<typeof setInterval> | undefined;

	// Mode state
	let activeMode = $state<Mode | null>(null);

	// Health state
	let health = $state<SystemHealth | null>(null);

	// Dim state (day/night)
	let isDimmed = $state(false);
	let dimStart = '22:00';
	let dimEnd = '07:00';

	onMount(() => {
		// Connect WebSocket
		websocket.connect();

		// Load devices
		devices.load();

		// Load active mode and health
		loadActiveMode();
		loadHealth();

		// Start clock
		clockInterval = setInterval(() => {
			currentTime = new Date();
			checkDimMode();
		}, 1000);

		// Refresh health every 30 seconds
		const healthInterval = setInterval(loadHealth, 30000);

		// Refresh mode every minute
		const modeInterval = setInterval(loadActiveMode, 60000);

		return () => {
			clearInterval(healthInterval);
			clearInterval(modeInterval);
		};
	});

	onDestroy(() => {
		if (clockInterval) clearInterval(clockInterval);
		websocket.disconnect();
	});

	async function loadActiveMode() {
		try {
			const result = await getActiveMode();
			activeMode = result.data;
		} catch (e) {
			console.error('Failed to load active mode:', e);
		}
	}

	async function loadHealth() {
		try {
			const result = await getSystemHealth();
			health = result.data;
		} catch (e) {
			console.error('Failed to load health:', e);
		}
	}

	function checkDimMode() {
		const now = currentTime;
		const hours = now.getHours();
		const minutes = now.getMinutes();
		const currentMinutes = hours * 60 + minutes;

		const [dimStartH, dimStartM] = dimStart.split(':').map(Number);
		const [dimEndH, dimEndM] = dimEnd.split(':').map(Number);
		const startMinutes = dimStartH * 60 + dimStartM;
		const endMinutes = dimEndH * 60 + dimEndM;

		// Handle overnight dim period
		if (startMinutes > endMinutes) {
			isDimmed = currentMinutes >= startMinutes || currentMinutes < endMinutes;
		} else {
			isDimmed = currentMinutes >= startMinutes && currentMinutes < endMinutes;
		}
	}

	function formatTime(date: Date): string {
		return date.toLocaleTimeString('fr-CA', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatDate(date: Date): string {
		return date.toLocaleDateString('fr-CA', {
			weekday: 'long',
			day: 'numeric',
			month: 'long'
		});
	}

	function getHealthIcon(status: string): string {
		switch (status) {
			case 'healthy':
				return '🟢';
			case 'degraded':
				return '🟡';
			default:
				return '🔴';
		}
	}
</script>

<svelte:head>
	<title>Kiosk - Family Hub</title>
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
</svelte:head>

<div
	class="flex min-h-screen flex-col bg-black text-white transition-opacity duration-1000"
	class:opacity-30={isDimmed}
>
	<!-- Top Bar: Time + Status -->
	<header class="flex items-start justify-between p-6">
		<!-- Clock -->
		<div>
			<div class="text-7xl font-light tracking-tight">{formatTime(currentTime)}</div>
			<div class="mt-1 text-xl capitalize text-gray-400">{formatDate(currentTime)}</div>
		</div>

		<!-- Status indicators -->
		<div class="flex items-center gap-4">
			<!-- Active mode -->
			{#if activeMode}
				<div class="flex items-center gap-2 rounded-lg bg-emerald-900/50 px-3 py-2">
					<span class="text-lg">{activeMode.icon || '🏠'}</span>
					<span class="text-sm font-medium">{activeMode.label}</span>
				</div>
			{/if}

			<!-- WebSocket status -->
			<div
				class="h-3 w-3 rounded-full"
				class:bg-green-500={wsConnected}
				class:bg-red-500={!wsConnected}
				class:animate-pulse={!wsConnected}
				title={wsConnected ? 'Connecté' : 'Déconnecté'}
			></div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="flex flex-1 flex-col gap-6 p-6 pt-0">
		<!-- Quick Stats Row -->
		<div class="grid grid-cols-4 gap-4">
			<!-- Temperature (placeholder) -->
			<div class="rounded-2xl bg-gray-900 p-4">
				<div class="text-sm text-gray-500">Intérieur</div>
				<div class="text-3xl font-light">21°C</div>
			</div>

			<!-- Outside (placeholder) -->
			<div class="rounded-2xl bg-gray-900 p-4">
				<div class="text-sm text-gray-500">Extérieur</div>
				<div class="text-3xl font-light">-5°C</div>
			</div>

			<!-- Devices online -->
			<div class="rounded-2xl bg-gray-900 p-4">
				<div class="text-sm text-gray-500">Appareils</div>
				<div class="text-3xl font-light">{favorites.length}</div>
			</div>

			<!-- System health -->
			<div class="rounded-2xl bg-gray-900 p-4">
				<div class="text-sm text-gray-500">Système</div>
				<div class="text-3xl font-light">{health ? getHealthIcon(health.status) : '⏳'}</div>
			</div>
		</div>

		<!-- Favorite Devices Grid -->
		<section class="flex-1">
			<h2 class="mb-4 text-lg font-medium text-gray-400">Favoris</h2>
			<div class="grid grid-cols-4 gap-4">
				{#each favorites.slice(0, 8) as device}
					<button
						class="flex flex-col items-center justify-center rounded-2xl bg-gray-900 p-6 transition-colors hover:bg-gray-800"
					>
						<span class="text-3xl">{device.type === 'light' ? '💡' : device.type === 'switch' ? '🔌' : '📱'}</span>
						<span class="mt-2 text-sm text-gray-300">{device.label || device.name}</span>
						<span
							class="mt-1 text-xs"
							class:text-green-500={device.state?.switch === 'on'}
							class:text-gray-600={device.state?.switch !== 'on'}
						>
							{device.state?.switch === 'on' ? 'Allumé' : 'Éteint'}
						</span>
					</button>
				{/each}

				{#if favorites.length === 0}
					<div class="col-span-4 rounded-2xl bg-gray-900 p-8 text-center text-gray-500">
						Aucun favori configuré
					</div>
				{/if}
			</div>
		</section>

		<!-- System Status Bar -->
		{#if health}
			<footer class="flex items-center justify-center gap-6 text-sm text-gray-500">
				{#each Object.entries(health.components) as [name, component]}
					<div class="flex items-center gap-1">
						<span
							class="h-2 w-2 rounded-full"
							class:bg-green-500={component.status === 'healthy'}
							class:bg-yellow-500={component.status === 'degraded'}
							class:bg-red-500={component.status !== 'healthy' && component.status !== 'degraded'}
						></span>
						<span class="capitalize">{name.replace('_', ' ')}</span>
					</div>
				{/each}
			</footer>
		{/if}
	</main>
</div>

<style>
	/* Kiosk-specific styles */
	:global(body) {
		overflow: hidden;
		cursor: none;
	}

	/* Show cursor on interaction */
	:global(body:active) {
		cursor: default;
	}
</style>
