<script lang="ts">
	import { onMount } from 'svelte';
	import { websocket } from '$stores/websocket';
	import {
		getAutomations,
		getAllExecutions,
		getExecutionStats,
		getAlertCounts,
		updateAutomation,
		triggerAutomation,
		type Automation,
		type AutomationExecution,
		type ExecutionStats,
		type AlertCounts
	} from '$lib/api/automations';

	let wsConnected = $derived($websocket.connected);

	let loading = $state(true);
	let error = $state<string | null>(null);
	let automations = $state<Automation[]>([]);
	let executions = $state<AutomationExecution[]>([]);
	let stats = $state<ExecutionStats | null>(null);
	let alertCounts = $state<AlertCounts | null>(null);
	let notification = $state<{ message: string; type: 'success' | 'error' } | null>(null);
	let activeTab = $state<'automations' | 'history' | 'alerts'>('automations');

	onMount(async () => {
		websocket.connect();
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			const [automationsRes, executionsRes, statsRes, alertsRes] = await Promise.all([
				getAutomations(),
				getAllExecutions(20),
				getExecutionStats(24),
				getAlertCounts()
			]);
			automations = automationsRes.data;
			executions = executionsRes.data;
			stats = statsRes.data;
			alertCounts = alertsRes.data;
		} catch (e) {
			console.error('Failed to load admin data:', e);
			error = 'Impossible de charger les données';
		} finally {
			loading = false;
		}
	}

	async function handleToggleAutomation(automation: Automation) {
		try {
			await updateAutomation(automation.id, { is_enabled: !automation.is_enabled });
			automations = automations.map((a) =>
				a.id === automation.id ? { ...a, is_enabled: !a.is_enabled } : a
			);
			showNotification(
				`${automation.label} ${!automation.is_enabled ? 'activée' : 'désactivée'}`,
				'success'
			);
		} catch (e) {
			showNotification("Erreur lors de la mise à jour", 'error');
		}
	}

	async function handleTriggerAutomation(automation: Automation) {
		try {
			await triggerAutomation(automation.id);
			showNotification(`${automation.label} déclenchée`, 'success');
			// Reload executions
			const executionsRes = await getAllExecutions(20);
			executions = executionsRes.data;
		} catch (e) {
			showNotification("Erreur lors du déclenchement", 'error');
		}
	}

	function showNotification(message: string, type: 'success' | 'error') {
		notification = { message, type };
		setTimeout(() => {
			notification = null;
		}, 3000);
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleString('fr-CA', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<svelte:head>
	<title>Admin - Family Hub</title>
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
				<h1 class="text-lg font-semibold text-[var(--color-text)]">Administration</h1>

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
					class="mb-6 rounded-lg bg-green-100 p-4 text-green-700 dark:bg-green-900/30 dark:text-green-400"
				>
					{notification.message}
				</div>
			{:else}
				<div
					class="mb-6 rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900/30 dark:text-red-400"
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

		<!-- Stats Cards -->
		{#if stats && alertCounts}
			<section class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
				<div class="rounded-xl bg-[var(--color-surface)] p-4">
					<p class="text-sm text-[var(--color-text-muted)]">Exécutions (24h)</p>
					<p class="text-2xl font-bold text-[var(--color-text)]">{stats.total_executions}</p>
				</div>
				<div class="rounded-xl bg-[var(--color-surface)] p-4">
					<p class="text-sm text-[var(--color-text-muted)]">Taux de succès</p>
					<p class="text-2xl font-bold text-green-600">{stats.success_rate.toFixed(1)}%</p>
				</div>
				<div class="rounded-xl bg-[var(--color-surface)] p-4">
					<p class="text-sm text-[var(--color-text-muted)]">Échecs</p>
					<p class="text-2xl font-bold text-red-600">{stats.failed}</p>
				</div>
				<div class="rounded-xl bg-[var(--color-surface)] p-4">
					<p class="text-sm text-[var(--color-text-muted)]">Alertes</p>
					<p class="text-2xl font-bold text-amber-600">{alertCounts.total}</p>
				</div>
			</section>
		{/if}

		<!-- Tab Navigation -->
		<div class="mb-6 flex gap-2">
			{#each [
				{ id: 'automations', label: 'Automations' },
				{ id: 'history', label: 'Historique' },
				{ id: 'alerts', label: `Alertes ${alertCounts?.total ? `(${alertCounts.total})` : ''}` }
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
		{:else if activeTab === 'automations'}
			<!-- Automations List -->
			<div class="space-y-3">
				{#each automations as automation}
					<div class="flex items-center justify-between rounded-xl bg-[var(--color-surface)] p-4 transition-colors hover:bg-[var(--color-bg)]">
						<a
							href="/admin/automations/{automation.id}"
							class="flex-1"
						>
							<div class="flex items-center gap-2">
								<h3 class="font-medium text-[var(--color-text)]">{automation.label}</h3>
								{#if !automation.is_enabled}
									<span
										class="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-400"
									>
										Désactivée
									</span>
								{/if}
								<span class="text-xs text-[var(--color-text-muted)]">
									({automation.actions_count} actions)
								</span>
							</div>
							<p class="text-sm text-[var(--color-text-muted)]">
								{automation.trigger_type || 'Manuel'} • {automation.trigger_count} exécutions •
								{automation.success_count} succès
							</p>
							{#if automation.last_triggered}
								<p class="text-xs text-[var(--color-text-muted)]">
									Dernière: {formatDate(automation.last_triggered)}
									{#if automation.last_success === false}
										<span class="text-red-500">(échec)</span>
									{/if}
								</p>
							{/if}
						</a>

						<div class="flex items-center gap-2">
							<button
								onclick={(e) => { e.preventDefault(); e.stopPropagation(); handleTriggerAutomation(automation); }}
								disabled={!automation.is_enabled}
								class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
								aria-label="Déclencher {automation.label}"
							>
								Déclencher
							</button>
							<button
								onclick={(e) => { e.preventDefault(); e.stopPropagation(); handleToggleAutomation(automation); }}
								class="rounded-lg px-3 py-1.5 text-sm"
								class:bg-green-600={!automation.is_enabled}
								class:hover:bg-green-700={!automation.is_enabled}
								class:bg-gray-500={automation.is_enabled}
								class:hover:bg-gray-600={automation.is_enabled}
								class:text-white={true}
								aria-label={automation.is_enabled ? 'Désactiver' : 'Activer'}
							>
								{automation.is_enabled ? 'Désactiver' : 'Activer'}
							</button>
						</div>
					</div>
				{/each}

				{#if automations.length === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucune automation trouvée</p>
					</div>
				{/if}
			</div>
		{:else if activeTab === 'history'}
			<!-- Execution History -->
			<div class="space-y-2">
				{#each executions as execution}
					<div
						class="flex items-center justify-between rounded-lg bg-[var(--color-surface)] p-3"
						class:border-l-4={true}
						class:border-green-500={execution.success}
						class:border-red-500={!execution.success}
					>
						<div>
							<div class="flex items-center gap-2">
								<span
									class="h-2 w-2 rounded-full"
									class:bg-green-500={execution.success}
									class:bg-red-500={!execution.success}
								></span>
								<span class="font-medium text-[var(--color-text)]">{execution.brain_name}</span>
							</div>
							<p class="text-sm text-[var(--color-text-muted)]">
								{execution.triggered_by || 'Auto'} •
								{execution.actions_succeeded}/{execution.actions_total} actions
								{#if execution.duration_ms}
									• {execution.duration_ms}ms
								{/if}
							</p>
							{#if execution.error_message}
								<p class="text-sm text-red-500">{execution.error_message}</p>
							{/if}
						</div>
						<span class="text-sm text-[var(--color-text-muted)]">
							{formatDate(execution.executed_at)}
						</span>
					</div>
				{/each}

				{#if executions.length === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucune exécution récente</p>
					</div>
				{/if}
			</div>
		{:else if activeTab === 'alerts'}
			<!-- Alerts -->
			<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
				<p class="text-[var(--color-text-muted)]">
					{alertCounts?.total === 0 ? 'Aucune alerte' : 'Alertes à implémenter'}
				</p>
			</div>
		{/if}

		<!-- Quick Links -->
		<section class="mt-8">
			<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Liens rapides</h2>
			<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
				<a
					href="/admin/users"
					class="flex items-center gap-2 rounded-xl bg-[var(--color-surface)] p-4 hover:bg-[var(--color-bg)]"
				>
					<span class="text-xl">👥</span>
					<span class="text-[var(--color-text)]">Utilisateurs</span>
				</a>
				<a
					href="http://192.168.1.66"
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-2 rounded-xl bg-[var(--color-surface)] p-4 hover:bg-[var(--color-bg)]"
				>
					<span class="text-xl">🏠</span>
					<span class="text-[var(--color-text)]">Hubitat</span>
				</a>
				<a
					href="http://192.168.1.118:1880"
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-2 rounded-xl bg-[var(--color-surface)] p-4 hover:bg-[var(--color-bg)]"
				>
					<span class="text-xl">🔴</span>
					<span class="text-[var(--color-text)]">Node-RED</span>
				</a>
				<a
					href="http://192.168.1.118:1880/ui"
					target="_blank"
					rel="noopener noreferrer"
					class="flex items-center gap-2 rounded-xl bg-[var(--color-surface)] p-4 hover:bg-[var(--color-bg)]"
				>
					<span class="text-xl">📊</span>
					<span class="text-[var(--color-text)]">Dashboard</span>
				</a>
				<a
					href="/modes"
					class="flex items-center gap-2 rounded-xl bg-[var(--color-surface)] p-4 hover:bg-[var(--color-bg)]"
				>
					<span class="text-xl">🌙</span>
					<span class="text-[var(--color-text)]">Modes</span>
				</a>
			</div>
		</section>
	</main>
</div>
