<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getInvoices,
		getInvoiceStats,
		getUpcomingDueDates,
		getInvoiceTodos,
		markInvoicePaid,
		runEmailSorter,
		checkEmailServiceHealth,
		type Invoice,
		type InvoiceStats,
		type InvoiceTodo
	} from '$lib/api/emails';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let invoices = $state<Invoice[]>([]);
	let stats = $state<InvoiceStats | null>(null);
	let upcomingDue = $state<Invoice[]>([]);
	let todos = $state<InvoiceTodo[]>([]);
	let serviceHealth = $state<{ available: boolean } | null>(null);
	let notification = $state<{ message: string; type: 'success' | 'error' } | null>(null);
	let runningSort = $state(false);

	// Filters
	let categoryFilter = $state<string>('');
	let paidFilter = $state<string>('');

	const categories = [
		{ value: '', label: 'Toutes catégories' },
		{ value: 'a_payer', label: 'À payer' },
		{ value: 'payees', label: 'Payées' },
		{ value: 'gouv_canada', label: 'Gouvernement Canada' },
		{ value: 'gouv_quebec', label: 'Gouvernement Québec' }
	];

	onMount(async () => {
		await loadAll();
	});

	async function loadAll() {
		loading = true;
		error = null;
		try {
			const [invoicesRes, statsRes, upcomingRes, todosRes, healthRes] = await Promise.all([
				getInvoices(categoryFilter || undefined, paidFilter === '' ? undefined : paidFilter === 'true'),
				getInvoiceStats(),
				getUpcomingDueDates(5),
				getInvoiceTodos('pending', 10),
				checkEmailServiceHealth()
			]);
			invoices = invoicesRes.data || [];
			stats = statsRes.data || null;
			upcomingDue = upcomingRes.data || [];
			todos = todosRes.data || [];
			serviceHealth = healthRes.data || null;
		} catch (e) {
			console.error('Failed to load email data:', e);
			error = 'Impossible de charger les données';
		} finally {
			loading = false;
		}
	}

	async function handleMarkPaid(invoiceId: number) {
		try {
			await markInvoicePaid(invoiceId);
			showNotification('Facture marquée comme payée', 'success');
			await loadAll();
		} catch (e) {
			showNotification('Erreur lors de la mise à jour', 'error');
		}
	}

	async function handleRunSorter() {
		runningSort = true;
		try {
			const result = await runEmailSorter();
			if (result.data?.success) {
				showNotification('Tri des emails terminé avec succès', 'success');
				await loadAll();
			} else {
				showNotification('Erreur lors du tri', 'error');
			}
		} catch (e) {
			showNotification('Erreur lors du tri des emails', 'error');
		} finally {
			runningSort = false;
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
		return new Date(dateStr).toLocaleDateString('fr-CA');
	}

	function formatAmount(amount: number | null, currency: string = 'CAD'): string {
		if (amount === null) return '-';
		return new Intl.NumberFormat('fr-CA', { style: 'currency', currency }).format(amount);
	}

	function getCategoryLabel(cat: string): string {
		const found = categories.find((c) => c.value === cat);
		return found?.label || cat;
	}

	function getCategoryColor(cat: string): string {
		switch (cat) {
			case 'a_payer':
				return 'bg-red-100 text-red-700';
			case 'payees':
				return 'bg-green-100 text-green-700';
			case 'gouv_canada':
				return 'bg-blue-100 text-blue-700';
			case 'gouv_quebec':
				return 'bg-purple-100 text-purple-700';
			default:
				return 'bg-gray-100 text-gray-700';
		}
	}

	function getPriorityColor(priority: string): string {
		switch (priority) {
			case 'urgent':
				return 'bg-red-100 text-red-700';
			case 'high':
				return 'bg-orange-100 text-orange-700';
			default:
				return 'bg-gray-100 text-gray-700';
		}
	}

	async function applyFilters() {
		await loadAll();
	}
</script>

<svelte:head>
	<title>Emails & Factures - Admin</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
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
				<h1 class="text-lg font-semibold text-[var(--color-text)]">Emails & Factures</h1>
			</div>

			<div class="flex items-center gap-2">
				<!-- Service Health -->
				{#if serviceHealth}
					<span
						class="flex items-center gap-1 rounded-full px-2 py-1 text-xs"
						class:bg-green-100={serviceHealth.available}
						class:text-green-700={serviceHealth.available}
						class:bg-red-100={!serviceHealth.available}
						class:text-red-700={!serviceHealth.available}
					>
						<span
							class="h-2 w-2 rounded-full"
							class:bg-green-500={serviceHealth.available}
							class:bg-red-500={!serviceHealth.available}
						></span>
						{serviceHealth.available ? 'Jetson OK' : 'Jetson Offline'}
					</span>
				{/if}

				<button
					onclick={handleRunSorter}
					disabled={runningSort || !serviceHealth?.available}
					class="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
				>
					{#if runningSort}
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
					{:else}
						<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
							></path>
						</svg>
					{/if}
					Trier emails
				</button>

				<button
					onclick={loadAll}
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
		</div>
	</header>

	<main class="mx-auto max-w-6xl px-4 py-6">
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
			<!-- Stats Cards -->
			{#if stats}
				<section class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
					<div class="rounded-xl bg-[var(--color-surface)] p-4">
						<p class="text-sm text-[var(--color-text-muted)]">Total factures</p>
						<p class="text-2xl font-bold text-[var(--color-text)]">{stats.totals.total_invoices}</p>
					</div>
					<div class="rounded-xl bg-[var(--color-surface)] p-4">
						<p class="text-sm text-[var(--color-text-muted)]">Non payées</p>
						<p class="text-2xl font-bold text-red-600">{stats.totals.unpaid_count}</p>
						<p class="text-sm text-red-600">{formatAmount(stats.totals.unpaid_amount)}</p>
					</div>
					<div class="rounded-xl bg-[var(--color-surface)] p-4">
						<p class="text-sm text-[var(--color-text-muted)]">Payées</p>
						<p class="text-2xl font-bold text-green-600">{stats.totals.paid_count}</p>
						<p class="text-sm text-green-600">{formatAmount(stats.totals.paid_amount)}</p>
					</div>
					<div class="rounded-xl bg-[var(--color-surface)] p-4">
						<p class="text-sm text-[var(--color-text-muted)]">Échéances proches</p>
						<p class="text-2xl font-bold text-orange-600">{upcomingDue.length}</p>
					</div>
				</section>
			{/if}

			<!-- Upcoming Due Dates -->
			{#if upcomingDue.length > 0}
				<section class="mb-6 rounded-xl bg-[var(--color-surface)] p-6">
					<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">
						Prochaines échéances
					</h2>
					<div class="space-y-2">
						{#each upcomingDue as invoice}
							<div
								class="flex items-center justify-between rounded-lg bg-[var(--color-bg)] p-3"
							>
								<div class="flex-1">
									<p class="font-medium text-[var(--color-text)]">{invoice.sender}</p>
									<p class="text-sm text-[var(--color-text-muted)]">{invoice.subject}</p>
								</div>
								<div class="text-right">
									<p class="font-medium text-orange-600">{formatDate(invoice.due_date)}</p>
									{#if invoice.amount}
										<p class="text-sm text-[var(--color-text-muted)]">
											{formatAmount(invoice.amount)}
										</p>
									{/if}
								</div>
								<button
									onclick={() => handleMarkPaid(invoice.id)}
									class="ml-3 rounded-lg bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700"
								>
									Payer
								</button>
							</div>
						{/each}
					</div>
				</section>
			{/if}

			<!-- Todos -->
			{#if todos.length > 0}
				<section class="mb-6 rounded-xl bg-[var(--color-surface)] p-6">
					<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">
						Tâches en attente ({todos.length})
					</h2>
					<div class="space-y-2">
						{#each todos as todo}
							<div
								class="flex items-center gap-3 rounded-lg bg-[var(--color-bg)] p-3"
							>
								<span class={`rounded-full px-2 py-0.5 text-xs ${getPriorityColor(todo.priority)}`}>
									{todo.priority}
								</span>
								<div class="flex-1">
									<p class="font-medium text-[var(--color-text)]">{todo.title}</p>
									{#if todo.description}
										<p class="text-sm text-[var(--color-text-muted)]">{todo.description}</p>
									{/if}
								</div>
								{#if todo.due_date}
									<span class="text-sm text-orange-600">{formatDate(todo.due_date)}</span>
								{/if}
								{#if todo.amount}
									<span class="text-sm font-medium text-[var(--color-text)]">
										{formatAmount(todo.amount)}
									</span>
								{/if}
							</div>
						{/each}
					</div>
				</section>
			{/if}

			<!-- Filters -->
			<section class="mb-4 flex flex-wrap gap-3">
				<select
					bind:value={categoryFilter}
					onchange={applyFilters}
					class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]"
				>
					{#each categories as cat}
						<option value={cat.value}>{cat.label}</option>
					{/each}
				</select>

				<select
					bind:value={paidFilter}
					onchange={applyFilters}
					class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]"
				>
					<option value="">Tous statuts</option>
					<option value="false">Non payées</option>
					<option value="true">Payées</option>
				</select>
			</section>

			<!-- Invoices List -->
			<section class="rounded-xl bg-[var(--color-surface)] p-6">
				<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">
					Factures ({invoices.length})
				</h2>

				{#if invoices.length > 0}
					<div class="overflow-x-auto">
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b border-[var(--color-border)] text-left">
									<th class="pb-3 text-[var(--color-text-muted)]">Date</th>
									<th class="pb-3 text-[var(--color-text-muted)]">Expéditeur</th>
									<th class="pb-3 text-[var(--color-text-muted)]">Sujet</th>
									<th class="pb-3 text-[var(--color-text-muted)]">Catégorie</th>
									<th class="pb-3 text-right text-[var(--color-text-muted)]">Montant</th>
									<th class="pb-3 text-[var(--color-text-muted)]">Échéance</th>
									<th class="pb-3 text-[var(--color-text-muted)]">Statut</th>
									<th class="pb-3"></th>
								</tr>
							</thead>
							<tbody>
								{#each invoices as invoice}
									<tr class="border-b border-[var(--color-border)] last:border-0">
										<td class="py-3 text-[var(--color-text)]">
											{formatDate(invoice.date_received)}
										</td>
										<td class="py-3 text-[var(--color-text)]">{invoice.sender}</td>
										<td class="max-w-xs truncate py-3 text-[var(--color-text)]" title={invoice.subject}>
											{invoice.subject}
										</td>
										<td class="py-3">
											<span class={`rounded-full px-2 py-0.5 text-xs ${getCategoryColor(invoice.category)}`}>
												{getCategoryLabel(invoice.category)}
											</span>
										</td>
										<td class="py-3 text-right text-[var(--color-text)]">
											{formatAmount(invoice.amount, invoice.currency)}
										</td>
										<td class="py-3 text-[var(--color-text)]">
											{formatDate(invoice.due_date)}
										</td>
										<td class="py-3">
											{#if invoice.is_paid}
												<span class="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
													Payée
												</span>
											{:else}
												<span class="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
													Non payée
												</span>
											{/if}
										</td>
										<td class="py-3">
											{#if !invoice.is_paid}
												<button
													onclick={() => handleMarkPaid(invoice.id)}
													class="rounded bg-green-600 px-2 py-1 text-xs text-white hover:bg-green-700"
												>
													Payer
												</button>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="text-center text-[var(--color-text-muted)]">Aucune facture trouvée</p>
				{/if}
			</section>

			<!-- Categories Breakdown -->
			{#if stats && stats.categories.length > 0}
				<section class="mt-6 rounded-xl bg-[var(--color-surface)] p-6">
					<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Par catégorie</h2>
					<div class="grid gap-3 md:grid-cols-2">
						{#each stats.categories as cat}
							<div class="rounded-lg bg-[var(--color-bg)] p-4">
								<div class="flex items-center justify-between">
									<span class={`rounded-full px-2 py-0.5 text-xs ${getCategoryColor(cat.category)}`}>
										{getCategoryLabel(cat.category)}
									</span>
									<span class="text-sm text-[var(--color-text-muted)]">{cat.count} factures</span>
								</div>
								<div class="mt-2 flex justify-between text-sm">
									<span class="text-red-600">
										{cat.unpaid_count} non payées ({formatAmount(cat.unpaid_amount)})
									</span>
									<span class="text-green-600">
										{cat.paid_count} payées
									</span>
								</div>
							</div>
						{/each}
					</div>
				</section>
			{/if}
		{/if}
	</main>
</div>
