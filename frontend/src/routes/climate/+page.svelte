<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$stores/auth';
	import { websocket } from '$stores/websocket';
	import {
		getTemperatureOverview,
		getTemperatureShortcuts,
		type TemperatureOverview,
		type TemperatureShortcut
	} from '$lib/api/temperature';
	import { refreshDeviceStates } from '$lib/api/devices';
	import { TemperatureWidget, TemperatureShortcuts, RoomTemperature } from '$components/climate';

	let user = $derived($auth.data);
	let wsConnected = $derived($websocket.connected);

	let loading = $state(true);
	let error = $state<string | null>(null);
	let overview = $state<TemperatureOverview | null>(null);
	let shortcuts = $state<TemperatureShortcut[]>([]);
	let activeTab = $state<'thermostats' | 'rooms' | 'all'>('thermostats');

	onMount(async () => {
		// Connect WebSocket for real-time updates
		websocket.connect();

		await loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			// First, refresh device states from Hubitat
			await refreshDeviceStates();

			// Then load the temperature data
			const [overviewRes, shortcutsRes] = await Promise.all([
				getTemperatureOverview(),
				getTemperatureShortcuts()
			]);
			overview = overviewRes.data;
			shortcuts = shortcutsRes.data;
		} catch (e) {
			console.error('Failed to load temperature data:', e);
			error = 'Impossible de charger les données de température';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Climat - Family Hub</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
			<div class="flex items-center gap-3">
				<a
					href="/dashboard"
					class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
					aria-label="Retour au tableau de bord"
				>
					<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 19l-7-7 7-7"
						></path>
					</svg>
				</a>
				<h1 class="text-lg font-semibold text-[var(--color-text)]">Température</h1>

				<!-- WebSocket status -->
				<span
					class="h-2 w-2 rounded-full"
					class:bg-green-500={wsConnected}
					class:bg-red-500={!wsConnected}
					title={wsConnected ? 'Connecté' : 'Déconnecté'}
				></span>
			</div>

			<button
				onclick={loadData}
				disabled={loading}
				class="flex items-center gap-2 rounded-lg bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-bg)] disabled:opacity-50"
			>
				<svg
					class="h-4 w-4"
					class:animate-spin={loading}
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
					></path>
				</svg>
				Actualiser
			</button>
		</div>
	</header>

	<main class="mx-auto max-w-7xl px-4 py-6">
		<!-- Error -->
		{#if error}
			<div
				class="mb-6 rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900/30 dark:text-red-400"
			>
				{error}
				<button onclick={() => (error = null)} class="ml-2 underline">Fermer</button>
			</div>
		{/if}

		<!-- Loading -->
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<svg class="h-8 w-8 animate-spin text-[var(--color-primary)]" viewBox="0 0 24 24">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
						fill="none"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
					></path>
				</svg>
			</div>
		{:else if overview}
			<!-- Quick Shortcuts Section -->
			{#if overview.thermostats.length > 0 && shortcuts.length > 0}
				<section class="mb-8">
					<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Raccourcis</h2>
					<div class="rounded-xl bg-[var(--color-surface)] p-4">
						<p class="mb-3 text-sm text-[var(--color-text-muted)]">
							Appliquer à: {overview.thermostats[0].device_name}
						</p>
						<TemperatureShortcuts {shortcuts} thermostat={overview.thermostats[0]} layout="grid" />
					</div>
				</section>
			{/if}

			<!-- Tab Navigation -->
			<div class="mb-6 flex gap-2">
				{#each [
					{ id: 'thermostats', label: 'Thermostats' },
					{ id: 'rooms', label: 'Par pièce' },
					{ id: 'all', label: 'Tous' }
				] as tab}
					<button
						onclick={() => (activeTab = tab.id as typeof activeTab)}
						class="rounded-lg px-4 py-2 text-sm font-medium transition-colors"
						class:bg-[var(--color-primary)]={activeTab === tab.id}
						class:text-white={activeTab === tab.id}
						class:bg-[var(--color-surface)]={activeTab !== tab.id}
						class:text-[var(--color-text)]={activeTab !== tab.id}
					>
						{tab.label}
					</button>
				{/each}
			</div>

			<!-- Content -->
			{#if activeTab === 'thermostats'}
				<div class="grid gap-4 md:grid-cols-2">
					{#each overview.thermostats as thermostat}
						<TemperatureWidget reading={thermostat} size="large" />
					{/each}
				</div>

				{#if overview.thermostats.length === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucun thermostat trouvé</p>
					</div>
				{/if}
			{:else if activeTab === 'rooms'}
				<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
					{#each Object.entries(overview.by_room) as [room, readings]}
						{@const avgTemp =
							readings.reduce((sum, r) => sum + (r.temperature ?? 0), 0) / readings.length}
						{@const avgHumidity =
							readings.filter((r) => r.humidity !== null).length > 0
								? readings.reduce((sum, r) => sum + (r.humidity ?? 0), 0) /
									readings.filter((r) => r.humidity !== null).length
								: null}
						<RoomTemperature
							roomTemp={{
								room,
								temperature: avgTemp || null,
								humidity: avgHumidity,
								devices: readings.map((r) => ({
									device_id: r.device_id,
									device_name: r.device_name,
									temperature: r.temperature
								}))
							}}
							showDevices={true}
						/>
					{/each}
				</div>

				{#if Object.keys(overview.by_room).length === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucune donnée de température par pièce</p>
					</div>
				{/if}
			{:else}
				<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
					{#each overview.readings as reading}
						<TemperatureWidget {reading} size="medium" showControls={reading.is_thermostat} />
					{/each}
				</div>

				{#if overview.readings.length === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucun capteur de température trouvé</p>
					</div>
				{/if}
			{/if}
		{/if}
	</main>
</div>
