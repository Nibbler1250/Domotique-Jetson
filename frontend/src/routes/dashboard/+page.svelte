<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$stores/auth';
	import { devices, devicesList, favoriteDevices, devicesByRoom } from '$stores/devices';
	import { websocket } from '$stores/websocket';
	import { DeviceList } from '$components/devices';
	import { ActiveModeIndicator } from '$components/modes';
	import { syncDevices } from '$lib/api/devices';
	import { getActiveMode, type Mode } from '$lib/api/modes';
	import {
		getInvoiceStats,
		getUpcomingDueDates,
		type Invoice,
		type InvoiceStats
	} from '$lib/api/emails';

	let user = $derived($auth.data);
	let loading = $derived($devices.loading);
	let error = $derived($devices.error);
	let wsConnected = $derived($websocket.connected);

	// Trading access: admin or simon only
	let hasTradingAccess = $derived(
		user?.role === 'admin' || (user?.role === 'family_adult' && user?.username === 'simon')
	);

	let syncing = $state(false);
	let activeTab = $state<'favorites' | 'all' | 'rooms'>('favorites');
	let activeMode = $state<Mode | null>(null);

	// Invoice data (Simon/Admin only)
	let invoiceStats = $state<InvoiceStats | null>(null);
	let upcomingInvoices = $state<Invoice[]>([]);

	onMount(async () => {
		// Connect WebSocket
		websocket.connect();

		// Load devices and active mode
		await Promise.all([devices.load(), loadActiveMode()]);

		// Load invoices for Simon/Admin
		if (
			$auth.data?.role === 'admin' ||
			($auth.data?.role === 'family_adult' && $auth.data?.username === 'simon')
		) {
			await loadInvoiceData();
		}
	});

	async function loadInvoiceData() {
		try {
			const [statsRes, upcomingRes] = await Promise.all([
				getInvoiceStats(),
				getUpcomingDueDates(3)
			]);
			invoiceStats = statsRes.data || null;
			upcomingInvoices = upcomingRes.data || [];
		} catch (e) {
			console.error('Failed to load invoice data:', e);
		}
	}

	async function loadActiveMode() {
		try {
			const result = await getActiveMode();
			activeMode = result.data;
		} catch (e) {
			console.error('Failed to load active mode:', e);
		}
	}

	onDestroy(() => {
		websocket.disconnect();
	});

	async function handleLogout() {
		await auth.logout();
		goto('/login');
	}

	async function handleSync() {
		syncing = true;
		try {
			await syncDevices();
			await devices.load();
		} catch (e) {
			console.error('Sync failed:', e);
		} finally {
			syncing = false;
		}
	}

	function formatAmount(amount: number | null): string {
		if (amount === null) return '-';
		return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD' }).format(amount);
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString('fr-CA');
	}
</script>

<svelte:head>
	<title>Dashboard - Family Hub</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
			<div class="flex items-center gap-3">
				<div
					class="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-primary)]"
				>
					<svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
						></path>
					</svg>
				</div>
				<h1 class="text-lg font-semibold text-[var(--color-text)]">Family Hub</h1>

				<!-- WebSocket status -->
				<span
					class="h-2 w-2 rounded-full"
					class:bg-green-500={wsConnected}
					class:bg-red-500={!wsConnected}
					title={wsConnected ? 'Connecté' : 'Déconnecté'}
				></span>
			</div>

			{#if user}
				<div class="flex items-center gap-3">
					<a
						href="/admin"
						class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-text)] hover:bg-[var(--color-bg)]"
					>
						Admin
					</a>
					<span class="text-sm text-[var(--color-text)]">{user.display_name}</span>
					<button
						onclick={handleLogout}
						class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-text)] hover:bg-[var(--color-bg)]"
					>
						Déconnexion
					</button>
				</div>
			{/if}
		</div>
	</header>

	<!-- Main Content -->
	<main class="mx-auto max-w-7xl px-4 py-6">
		<!-- Active mode and quick access -->
		<section class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
			<!-- Active Mode Indicator -->
			<ActiveModeIndicator mode={activeMode} />

			<!-- Quick access buttons -->
			<a
				href="/modes"
				class="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-white shadow-md hover:bg-indigo-700"
			>
				<span class="text-xl">🌙</span>
				<span class="font-medium">Modes</span>
			</a>
			<a
				href="/climate"
				class="flex items-center gap-2 rounded-xl bg-orange-500 px-4 py-3 text-white shadow-md hover:bg-orange-600"
			>
				<span class="text-xl">🌡️</span>
				<span class="font-medium">Climat</span>
			</a>
		</section>

		<!-- Trading Quick Access (Simon/Admin only) -->
		{#if hasTradingAccess}
			<section class="mb-6">
				<a
					href="/trading"
					class="flex items-center gap-3 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 px-4 py-3 text-white shadow-md hover:from-green-700 hover:to-emerald-700"
				>
					<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-white/20">
						<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
						</svg>
					</div>
					<div>
						<span class="font-semibold">Momentum Trader V7</span>
						<p class="text-sm text-white/80">Trading Dashboard</p>
					</div>
				</a>
			</section>
		{/if}

		<!-- Emails/Factures (Simon/Admin only) -->
		{#if hasTradingAccess && invoiceStats}
			<section class="mb-6 rounded-xl bg-[var(--color-surface)] p-4 shadow-md">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
						<span>📧</span> Factures
					</h2>
					<a
						href="/admin/emails"
						class="text-sm text-[var(--color-primary)] hover:underline"
					>
						Voir tout
					</a>
				</div>

				<!-- Stats -->
				<div class="mb-4 grid grid-cols-3 gap-3">
					<div class="rounded-lg bg-[var(--color-bg)] p-3 text-center">
						<p class="text-2xl font-bold text-[var(--color-text)]">{invoiceStats.totals.total_invoices}</p>
						<p class="text-xs text-[var(--color-text-muted)]">Total</p>
					</div>
					<div class="rounded-lg bg-red-50 p-3 text-center dark:bg-red-900/20">
						<p class="text-2xl font-bold text-red-600">{invoiceStats.totals.unpaid_count}</p>
						<p class="text-xs text-red-600">Non payées</p>
					</div>
					<div class="rounded-lg bg-[var(--color-bg)] p-3 text-center">
						<p class="text-lg font-bold text-red-600">{formatAmount(invoiceStats.totals.unpaid_amount)}</p>
						<p class="text-xs text-[var(--color-text-muted)]">À payer</p>
					</div>
				</div>

				<!-- Upcoming due dates -->
				{#if upcomingInvoices.length > 0}
					<div class="space-y-2">
						<p class="text-sm font-medium text-[var(--color-text-muted)]">Prochaines échéances</p>
						{#each upcomingInvoices as invoice}
							<div class="flex items-center justify-between rounded-lg bg-[var(--color-bg)] p-2 text-sm">
								<span class="truncate text-[var(--color-text)]" title={invoice.subject}>
									{invoice.sender}
								</span>
								<div class="flex items-center gap-2">
									{#if invoice.amount}
										<span class="font-medium text-[var(--color-text)]">
											{formatAmount(invoice.amount)}
										</span>
									{/if}
									<span class="text-orange-600">{formatDate(invoice.due_date)}</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</section>
		{/if}

		<!-- Tab Navigation -->
		<div class="mb-6 flex items-center justify-between">
			<div class="flex gap-2">
				{#each [
					{ id: 'favorites', label: 'Favoris' },
					{ id: 'all', label: 'Tous' },
					{ id: 'rooms', label: 'Par pièce' }
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

			<button
				onclick={handleSync}
				disabled={syncing}
				class="flex items-center gap-2 rounded-lg bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-bg)] disabled:opacity-50"
			>
				<svg
					class="h-4 w-4"
					class:animate-spin={syncing}
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
				{syncing ? 'Sync...' : 'Sync'}
			</button>
		</div>

		<!-- Error message -->
		{#if error}
			<div
				class="mb-6 rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900/30 dark:text-red-400"
			>
				{error}
				<button onclick={() => devices.clearError()} class="ml-2 underline">Fermer</button>
			</div>
		{/if}

		<!-- Loading state -->
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<svg class="h-8 w-8 animate-spin text-[var(--color-primary)]" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
				</svg>
			</div>
		{:else}
			<!-- Content based on active tab -->
			{#if activeTab === 'favorites'}
				<DeviceList
					devices={$favoriteDevices}
					title="Favoris"
					emptyMessage="Aucun favori. Marquez des appareils comme favoris pour les voir ici."
				/>
			{:else if activeTab === 'all'}
				<DeviceList devices={$devicesList} title="Tous les appareils" />
			{:else if activeTab === 'rooms'}
				{#each [...$devicesByRoom.entries()] as [room, roomDevices]}
					<div class="mb-8">
						<DeviceList devices={roomDevices} title={room} />
					</div>
				{/each}
				{#if $devicesByRoom.size === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucun appareil</p>
					</div>
				{/if}
			{/if}
		{/if}
	</main>
</div>
