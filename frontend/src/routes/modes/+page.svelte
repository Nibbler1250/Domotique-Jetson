<script lang="ts">
	import { onMount } from 'svelte';
	import { websocket } from '$stores/websocket';
	import { getModes, getActiveMode, type Mode, type ModeActivationResult } from '$lib/api/modes';
	import { ModeGrid } from '$components/modes';

	let wsConnected = $derived($websocket.connected);

	let loading = $state(true);
	let error = $state<string | null>(null);
	let modes = $state<Mode[]>([]);
	let activeMode = $state<Mode | null>(null);
	let notification = $state<{ message: string; type: 'success' | 'error' } | null>(null);

	onMount(async () => {
		// Connect WebSocket for real-time updates
		websocket.connect();

		await loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			const [modesRes, activeRes] = await Promise.all([getModes(true), getActiveMode()]);
			modes = modesRes.data;
			activeMode = activeRes.data;

			// Mark active mode
			if (activeMode) {
				modes = modes.map((m) => ({ ...m, is_active: m.id === activeMode?.id }));
			}
		} catch (e) {
			console.error('Failed to load modes:', e);
			error = 'Impossible de charger les modes';
		} finally {
			loading = false;
		}
	}

	function handleModeActivated(mode: Mode, result: ModeActivationResult) {
		// Update modes list to reflect new active state
		modes = modes.map((m) => ({ ...m, is_active: m.id === mode.id }));
		activeMode = mode;

		// Show notification
		if (result.success) {
			showNotification(`${mode.label} activé`, 'success');
		} else {
			showNotification(`${mode.label} activé avec ${result.actions_failed} erreur(s)`, 'error');
		}
	}

	function handleError(mode: Mode, err: Error) {
		showNotification(`Erreur: ${err.message || 'Échec activation'}`, 'error');
	}

	function showNotification(message: string, type: 'success' | 'error') {
		notification = { message, type };
		setTimeout(() => {
			notification = null;
		}, 3000);
	}
</script>

<svelte:head>
	<title>Modes - Family Hub</title>
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
				<h1 class="text-lg font-semibold text-[var(--color-text)]">Modes</h1>

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
				aria-label="Actualiser"
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
		<!-- Notification -->
		{#if notification}
			{#if notification.type === 'success'}
				<div
					class="mb-6 rounded-lg bg-green-100 p-4 text-green-700 transition-all dark:bg-green-900/30 dark:text-green-400"
				>
					{notification.message}
				</div>
			{:else}
				<div
					class="mb-6 rounded-lg bg-red-100 p-4 text-red-700 transition-all dark:bg-red-900/30 dark:text-red-400"
				>
					{notification.message}
				</div>
			{/if}
		{/if}

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
		{:else}
			<!-- Active mode indicator -->
			{#if activeMode}
				<section class="mb-8">
					<div
						class="flex items-center gap-3 rounded-xl bg-[var(--color-surface)] p-4 ring-2 ring-green-500/50"
					>
						<span class="relative flex h-3 w-3">
							<span
								class="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75"
							></span>
							<span class="relative inline-flex h-3 w-3 rounded-full bg-green-500"></span>
						</span>
						<div>
							<p class="text-sm text-[var(--color-text-muted)]">Mode actif</p>
							<p class="font-semibold text-[var(--color-text)]">{activeMode.label}</p>
						</div>
					</div>
				</section>
			{/if}

			<!-- Modes grid -->
			<section>
				<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Modes disponibles</h2>

				<ModeGrid
					{modes}
					columns={2}
					size="large"
					showDescriptions={true}
					onModeActivated={handleModeActivated}
					onError={handleError}
				/>
			</section>

			<!-- Quick info -->
			<section class="mt-8">
				<div class="rounded-xl bg-[var(--color-surface)] p-4">
					<h3 class="mb-2 font-medium text-[var(--color-text)]">À propos des modes</h3>
					<p class="text-sm text-[var(--color-text-muted)]">
						Les modes sont des séquences d'automatisation prédéfinies. Activez un mode pour
						exécuter plusieurs actions en même temps : contrôle des lumières, ajustement du
						chauffage, verrouillage des portes, etc.
					</p>
				</div>
			</section>
		{/if}
	</main>
</div>
