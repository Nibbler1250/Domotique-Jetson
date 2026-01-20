<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		getAutomationDetails,
		updateAutomation,
		triggerAutomation,
		type AutomationDetails,
		type AutomationAction
	} from '$lib/api/automations';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let automation = $state<AutomationDetails | null>(null);
	let notification = $state<{ message: string; type: 'success' | 'error' } | null>(null);
	let triggering = $state(false);

	const automationId = $derived(Number($page.params.id));

	onMount(async () => {
		await loadAutomation();
	});

	async function loadAutomation() {
		loading = true;
		error = null;
		try {
			const response = await getAutomationDetails(automationId);
			automation = response.data;
		} catch (e) {
			console.error('Failed to load automation:', e);
			error = 'Impossible de charger les détails';
		} finally {
			loading = false;
		}
	}

	async function handleToggle() {
		if (!automation) return;
		try {
			await updateAutomation(automation.id, { is_enabled: !automation.is_enabled });
			automation = { ...automation, is_enabled: !automation.is_enabled };
			showNotification(
				`Automation ${automation.is_enabled ? 'activée' : 'désactivée'}`,
				'success'
			);
		} catch (e) {
			showNotification('Erreur lors de la mise à jour', 'error');
		}
	}

	async function handleTrigger() {
		if (!automation) return;
		triggering = true;
		try {
			await triggerAutomation(automation.id);
			showNotification('Automation déclenchée avec succès', 'success');
		} catch (e) {
			showNotification('Erreur lors du déclenchement', 'error');
		} finally {
			triggering = false;
		}
	}

	function showNotification(message: string, type: 'success' | 'error') {
		notification = { message, type };
		setTimeout(() => {
			notification = null;
		}, 3000);
	}

	function formatTrigger(trigger: Record<string, unknown>): string {
		if (!trigger || !trigger.type) return 'Manuel';

		switch (trigger.type) {
			case 'time':
				const hour = String(trigger.hour || 0).padStart(2, '0');
				const minute = String(trigger.minute || 0).padStart(2, '0');
				return `Horaire: ${hour}:${minute}`;
			case 'event':
				return `Événement: ${trigger.device || 'inconnu'}`;
			case 'sunrise':
				return 'Au lever du soleil';
			case 'sunset':
				return 'Au coucher du soleil';
			default:
				return String(trigger.type);
		}
	}

	function formatAction(action: AutomationAction): string {
		let str = action.action;
		if (action.value !== undefined && action.value !== null) {
			str += ` → ${action.value}`;
		}
		return str;
	}

	function getActionIcon(action: string): string {
		if (action.includes('Setpoint') || action.includes('Temperature')) return '🌡️';
		if (action === 'on') return '💡';
		if (action === 'off') return '🌑';
		if (action.includes('Level')) return '🔆';
		if (action.includes('lock')) return '🔒';
		return '⚡';
	}
</script>

<svelte:head>
	<title>{automation?.label || 'Automation'} - Admin</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
			<div class="flex items-center gap-3">
				<a
					href="/admin"
					class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
					aria-label="Retour"
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
				<h1 class="text-lg font-semibold text-[var(--color-text)]">
					{automation?.label || 'Chargement...'}
				</h1>
			</div>

			<button
				onclick={loadAutomation}
				disabled={loading}
				class="rounded-lg bg-[var(--color-surface)] p-2 text-[var(--color-text)] hover:bg-[var(--color-bg)]"
				aria-label="Actualiser"
			>
				<svg
					class="h-5 w-5"
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
			</button>
		</div>
	</header>

	<main class="mx-auto max-w-4xl px-4 py-6">
		<!-- Notification -->
		{#if notification}
			<div
				class="mb-6 rounded-lg p-4"
				class:bg-green-100={notification.type === 'success'}
				class:text-green-700={notification.type === 'success'}
				class:bg-red-100={notification.type === 'error'}
				class:text-red-700={notification.type === 'error'}
			>
				{notification.message}
			</div>
		{/if}

		<!-- Error -->
		{#if error}
			<div class="mb-6 rounded-lg bg-red-100 p-4 text-red-700">
				{error}
				<a href="/admin" class="ml-2 underline">Retour</a>
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
		{:else if automation}
			<!-- Automation Info -->
			<section class="mb-6 rounded-xl bg-[var(--color-surface)] p-6">
				<div class="mb-4 flex items-start justify-between">
					<div>
						<h2 class="text-xl font-bold text-[var(--color-text)]">{automation.label}</h2>
						{#if automation.description}
							<p class="mt-1 text-[var(--color-text-muted)]">{automation.description}</p>
						{/if}
					</div>

					<span
						class="rounded-full px-3 py-1 text-sm font-medium"
						class:bg-green-100={automation.is_enabled}
						class:text-green-700={automation.is_enabled}
						class:bg-gray-200={!automation.is_enabled}
						class:text-gray-600={!automation.is_enabled}
					>
						{automation.is_enabled ? 'Active' : 'Désactivée'}
					</span>
				</div>

				<div class="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
					<div>
						<p class="text-[var(--color-text-muted)]">Déclencheur</p>
						<p class="font-medium text-[var(--color-text)]">{formatTrigger(automation.trigger)}</p>
					</div>
					<div>
						<p class="text-[var(--color-text-muted)]">Actions</p>
						<p class="font-medium text-[var(--color-text)]">{automation.actions?.length || 0}</p>
					</div>
					<div>
						<p class="text-[var(--color-text-muted)]">Exécutions</p>
						<p class="font-medium text-[var(--color-text)]">{automation.trigger_count}</p>
					</div>
					<div>
						<p class="text-[var(--color-text-muted)]">Succès</p>
						<p class="font-medium text-green-600">{automation.success_count}</p>
					</div>
				</div>

				<!-- Action Buttons -->
				<div class="mt-6 flex gap-3">
					<button
						onclick={handleTrigger}
						disabled={!automation.is_enabled || triggering}
						class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
					>
						{#if triggering}
							<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24">
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
						{/if}
						Déclencher maintenant
					</button>

					<button
						onclick={handleToggle}
						class="rounded-lg px-4 py-2"
						class:bg-red-600={automation.is_enabled}
						class:hover:bg-red-700={automation.is_enabled}
						class:bg-green-600={!automation.is_enabled}
						class:hover:bg-green-700={!automation.is_enabled}
						class:text-white={true}
					>
						{automation.is_enabled ? 'Désactiver' : 'Activer'}
					</button>
				</div>
			</section>

			<!-- Actions List -->
			<section class="rounded-xl bg-[var(--color-surface)] p-6">
				<h3 class="mb-4 text-lg font-semibold text-[var(--color-text)]">
					Actions ({automation.actions?.length || 0})
				</h3>

				{#if automation.actions && automation.actions.length > 0}
					<div class="space-y-2">
						{#each automation.actions as action, index}
							<div
								class="flex items-center gap-3 rounded-lg bg-[var(--color-bg)] p-3"
							>
								<span class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface)] text-lg">
									{getActionIcon(action.action)}
								</span>
								<div class="flex-1">
									<p class="font-medium text-[var(--color-text)]">{action.device}</p>
									<p class="text-sm text-[var(--color-text-muted)]">{formatAction(action)}</p>
								</div>
								<span class="text-sm text-[var(--color-text-muted)]">#{index + 1}</span>
							</div>
						{/each}
					</div>
				{:else}
					<p class="text-center text-[var(--color-text-muted)]">Aucune action définie</p>
				{/if}
			</section>

			<!-- Technical Details -->
			<section class="mt-6 rounded-xl bg-[var(--color-surface)] p-6">
				<h3 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Détails techniques</h3>

				<div class="space-y-2 text-sm">
					<div class="flex justify-between">
						<span class="text-[var(--color-text-muted)]">Nom interne</span>
						<code class="rounded bg-[var(--color-bg)] px-2 py-0.5 text-[var(--color-text)]">
							{automation.brain_name}
						</code>
					</div>
					<div class="flex justify-between">
						<span class="text-[var(--color-text-muted)]">ID local</span>
						<span class="text-[var(--color-text)]">{automation.id}</span>
					</div>
					<div class="flex justify-between">
						<span class="text-[var(--color-text-muted)]">Créée le</span>
						<span class="text-[var(--color-text)]">
							{automation.created_at
								? new Date(automation.created_at).toLocaleDateString('fr-CA')
								: '-'}
						</span>
					</div>
				</div>
			</section>
		{/if}
	</main>
</div>
