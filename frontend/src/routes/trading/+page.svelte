<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$stores/auth';
	import {
		trading,
		servicesHealth,
		portfolioMetrics,
		topPositions,
		hasErrors,
		traderStatus
	} from '$stores/trading';

	// Access control: only admin or simon
	let user = $derived($auth.data);
	let hasAccess = $derived(
		user?.role === 'admin' || (user?.role === 'family_adult' && user?.username === 'simon')
	);

	let connected = $derived($trading.connected);
	let lastUpdate = $derived($trading.lastUpdate);
	let error = $derived($trading.error);

	// Trader status with stale data detection
	let status = $derived($traderStatus);

	// Data
	let health = $derived($servicesHealth);
	let metrics = $derived($portfolioMetrics);
	let positions = $derived($topPositions);
	let errors = $derived($trading.errors);
	let engine = $derived($trading.engine);
	let ibkr = $derived($trading.ibkr);
	let pipeline = $derived($trading.pipeline);
	let recommendations = $derived($trading.recommendations);

	// Active tab
	let activeTab = $state<'overview' | 'services' | 'positions' | 'scanner' | 'capital'>('overview');

	// V7.4: Capital & Control data
	let account = $derived($trading.account);
	let currencies = $derived($trading.currencies);
	let capital = $derived($trading.capital);
	let marketControl = $derived($trading.marketControl);

	// V7.5: Margin Protection data
	let marginConfig = $derived($trading.marginProtectionConfig);
	let marginScores = $derived($trading.marginProtectionScores);
	let tradingConfig = $derived($trading.tradingConfig);

	// Local state for editing margin protection weights
	let editingWeights = $state(false);
	let tempWeights = $state({
		weight_ml_exit: 0.35,
		weight_pnl_negative: 0.30,
		weight_time_held: 0.15,
		weight_stop_proximity: 0.10,
		weight_volume_decay: 0.10
	});
	let tempMaxPositions = $state(20);

	// Sync temp values when config changes
	$effect(() => {
		if (marginConfig) {
			tempWeights = {
				weight_ml_exit: marginConfig.weight_ml_exit,
				weight_pnl_negative: marginConfig.weight_pnl_negative,
				weight_time_held: marginConfig.weight_time_held,
				weight_stop_proximity: marginConfig.weight_stop_proximity,
				weight_volume_decay: marginConfig.weight_volume_decay
			};
		}
	});

	$effect(() => {
		if (tradingConfig) {
			tempMaxPositions = tradingConfig.max_positions;
		}
	});

	function getTotalWeight(): number {
		return tempWeights.weight_ml_exit + tempWeights.weight_pnl_negative +
			tempWeights.weight_time_held + tempWeights.weight_stop_proximity +
			tempWeights.weight_volume_decay;
	}

	function saveWeights() {
		const total = getTotalWeight();
		if (Math.abs(total - 1.0) > 0.01) {
			alert(`Weights must sum to 1.0 (currently ${total.toFixed(2)})`);
			return;
		}
		trading.updateMarginProtectionConfig(tempWeights);
		editingWeights = false;
	}

	function saveMaxPositions() {
		if (tempMaxPositions < 1 || tempMaxPositions > 100) {
			alert('Max positions must be between 1 and 100');
			return;
		}
		trading.updateMaxPositions(tempMaxPositions);
	}

	onMount(() => {
		if (!hasAccess) {
			goto('/dashboard');
			return;
		}
		trading.connect();
	});

	onDestroy(() => {
		trading.disconnect();
	});

	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(value);
	}

	function formatPercent(value: number): string {
		return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
	}

	function formatTime(isoString: string | null): string {
		if (!isoString) return 'N/A';
		const date = new Date(isoString);
		return date.toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' });
	}

	function getStatusColor(status: string | undefined): string {
		switch (status) {
			case 'HEALTHY':
			case 'CONNECTED':
			case 'RUNNING':
				return 'bg-green-500';
			case 'DEGRADED':
			case 'PAUSED':
				return 'bg-yellow-500';
			case 'DOWN':
			case 'DISCONNECTED':
			case 'STOPPED':
				return 'bg-red-500';
			default:
				return 'bg-gray-400';
		}
	}

	function getPnlColor(pnl: number): string {
		if (pnl > 0) return 'text-green-500';
		if (pnl < 0) return 'text-red-500';
		return 'text-gray-400';
	}
</script>

<svelte:head>
	<title>Trading - Family Hub</title>
</svelte:head>

{#if !hasAccess}
	<div class="flex min-h-screen items-center justify-center bg-[var(--color-bg)]">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-red-500">Access Denied</h1>
			<p class="mt-2 text-[var(--color-text-muted)]">This section is restricted to admin users.</p>
			<a href="/dashboard" class="mt-4 inline-block text-[var(--color-primary)] underline"
				>Back to Dashboard</a
			>
		</div>
	</div>
{:else}
	<div class="min-h-screen bg-[var(--color-bg)]">
		<!-- Header -->
		<header
			class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]"
		>
			<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
				<div class="flex items-center gap-3">
					<a href="/dashboard" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
						<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 19l-7-7 7-7"
							></path>
						</svg>
					</a>
					<div
						class="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-green-500 to-emerald-600"
					>
						<svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
							></path>
						</svg>
					</div>
					<h1 class="text-lg font-semibold text-[var(--color-text)]">Momentum Trader V7</h1>

					<!-- Connection status -->
					<span
						class="h-2 w-2 rounded-full"
						class:bg-green-500={connected}
						class:bg-red-500={!connected}
						class:animate-pulse={connected}
						title={connected ? 'Connected' : 'Disconnected'}
					></span>

					<!-- Trader Status with stale detection -->
					<span
						class="rounded-full px-2 py-0.5 text-xs font-medium"
						class:bg-green-100={status.status === 'RUNNING'}
						class:text-green-800={status.status === 'RUNNING'}
						class:bg-yellow-100={status.status === 'PAUSED'}
						class:text-yellow-800={status.status === 'PAUSED'}
						class:bg-red-100={status.status === 'STOPPED' || status.status === 'OFFLINE'}
						class:text-red-800={status.status === 'STOPPED' || status.status === 'OFFLINE'}
						class:bg-gray-100={status.status === 'UNKNOWN'}
						class:text-gray-800={status.status === 'UNKNOWN'}
						title={status.reason}
					>
						{#if status.mode}{status.mode} - {/if}{status.status}
						{#if status.isStale}
							<span class="ml-1 text-red-500">⚠</span>
						{/if}
					</span>
				</div>

				<div class="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
					{#if lastUpdate}
						<span>Last update: {formatTime(lastUpdate)}</span>
					{/if}
					{#if $hasErrors}
						<span class="flex items-center gap-1 text-red-500">
							<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
								<path
									fill-rule="evenodd"
									d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
									clip-rule="evenodd"
								></path>
							</svg>
							{errors?.errors_1h} errors
						</span>
					{/if}
				</div>
			</div>
		</header>

		<!-- Tab Navigation -->
		<div class="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
			<div class="mx-auto max-w-7xl px-4">
				<div class="flex gap-1">
					{#each [
						{ id: 'overview', label: 'Overview', icon: '📊' },
						{ id: 'capital', label: 'Capital', icon: '💰' },
						{ id: 'services', label: 'Services', icon: '🔧' },
						{ id: 'positions', label: 'Positions', icon: '💼' },
						{ id: 'scanner', label: 'Scanner', icon: '🔍' }
					] as tab}
						<button
							onclick={() => (activeTab = tab.id as typeof activeTab)}
							class="flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
							class:border-[var(--color-primary)]={activeTab === tab.id}
							class:text-[var(--color-primary)]={activeTab === tab.id}
							class:border-transparent={activeTab !== tab.id}
							class:text-[var(--color-text-muted)]={activeTab !== tab.id}
							class:hover:text-[var(--color-text)]={activeTab !== tab.id}
						>
							<span>{tab.icon}</span>
							{tab.label}
						</button>
					{/each}
				</div>
			</div>
		</div>

		<!-- Error Banner -->
		{#if error}
			<div class="bg-red-100 px-4 py-2 text-center text-sm text-red-700 dark:bg-red-900/30">
				{error}
			</div>
		{/if}

		<!-- Stale Data Warning Banner -->
		{#if status.isStale && status.status === 'OFFLINE'}
			<div class="bg-orange-100 px-4 py-2 text-center text-sm text-orange-700 dark:bg-orange-900/30">
				⚠️ Trader appears offline - no heartbeat received for 90+ seconds. Data shown may be stale.
				{#if status.lastUpdate}
					Last update: {formatTime(status.lastUpdate)}
				{/if}
			</div>
		{/if}

		<!-- Main Content -->
		<main class="mx-auto max-w-7xl px-4 py-6">
			{#if activeTab === 'overview'}
				<!-- Overview Tab -->
				<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
					<!-- Portfolio Summary Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-2">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Portfolio</h2>
						{#if metrics}
							<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Equity</p>
									<p class="text-2xl font-bold text-[var(--color-text)]">
										{formatCurrency(metrics.equity)}
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">P&L Total</p>
									<p class="text-2xl font-bold {getPnlColor(metrics.pnlTotal)}">
										{formatCurrency(metrics.pnlTotal)}
									</p>
									<p class="text-sm {getPnlColor(metrics.pnlPct)}">{formatPercent(metrics.pnlPct)}</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Win Rate</p>
									<p class="text-2xl font-bold text-[var(--color-text)]">
										{metrics.winRate.toFixed(0)}%
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Trades Today</p>
									<p class="text-2xl font-bold text-[var(--color-text)]">{metrics.tradesToday}</p>
									<p class="text-sm text-[var(--color-text-muted)]">
										{metrics.positionsOpen} open
									</p>
								</div>
							</div>
						{:else}
							<p class="text-[var(--color-text-muted)]">Waiting for data...</p>
						{/if}
					</div>

					<!-- Services Health Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Services Health</h2>
						{#if status.isStale}
							<!-- Show offline state when data is stale -->
							<div class="flex items-center gap-4">
								<div class="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
									<span class="text-2xl font-bold text-red-500">⚠</span>
								</div>
								<div class="flex-1">
									<p class="text-red-500 font-medium">Trader Offline</p>
									<p class="text-sm text-[var(--color-text-muted)]">No heartbeat received</p>
								</div>
							</div>
						{:else}
						<div class="flex items-center gap-4">
							<div class="flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
								<span class="text-2xl font-bold text-[var(--color-text)]">
									{health.healthy}/{health.total}
								</span>
							</div>
							<div class="flex-1">
								<div class="mb-2 flex gap-2">
									<span class="flex items-center gap-1 text-sm text-green-500">
										<span class="h-2 w-2 rounded-full bg-green-500"></span>
										{health.healthy} OK
									</span>
									{#if health.degraded > 0}
										<span class="flex items-center gap-1 text-sm text-yellow-500">
											<span class="h-2 w-2 rounded-full bg-yellow-500"></span>
											{health.degraded} Degraded
										</span>
									{/if}
									{#if health.down > 0}
										<span class="flex items-center gap-1 text-sm text-red-500">
											<span class="h-2 w-2 rounded-full bg-red-500"></span>
											{health.down} Down
										</span>
									{/if}
								</div>
								<!-- Progress bar -->
								<div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
									<div
										class="h-full bg-green-500"
										style="width: {(health.healthy / health.total) * 100}%"
									></div>
								</div>
							</div>
						</div>
						{/if}
					</div>

					<!-- Top Positions -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-2">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Top Positions</h2>
						{#if positions.length > 0}
							<div class="space-y-3">
								{#each positions as pos}
									<div
										class="flex items-center justify-between rounded-lg bg-[var(--color-bg)] p-3"
									>
										<div class="flex items-center gap-3">
											<span
												class="rounded px-2 py-0.5 text-xs font-medium"
												class:bg-blue-100={pos.asset_type === 'stock'}
												class:text-blue-800={pos.asset_type === 'stock'}
												class:bg-purple-100={pos.asset_type === 'forex'}
												class:text-purple-800={pos.asset_type === 'forex'}
											>
												{pos.asset_type.toUpperCase()}
											</span>
											<div>
												<p class="font-medium text-[var(--color-text)]">{pos.symbol}</p>
												<p class="text-xs text-[var(--color-text-muted)]">Qty: {pos.quantity}</p>
											</div>
										</div>
										<div class="text-right">
											<p class="font-medium {getPnlColor(pos.unrealized_pnl)}">{formatCurrency(pos.unrealized_pnl)}</p>
											<p class="text-xs {getPnlColor(pos.pnl_percent)}">{formatPercent(pos.pnl_percent)}</p>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-center text-[var(--color-text-muted)]">No positions</p>
						{/if}
					</div>

					<!-- IBKR Connection -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">IBKR Connection</h2>
						{#if ibkr}
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Status</span>
									<span class="flex items-center gap-2">
										<span class="h-2 w-2 rounded-full {getStatusColor(ibkr.status)}"></span>
										{ibkr.status}
									</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Latency</span>
									<span class="text-[var(--color-text)]">{ibkr.latency_ms}ms</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Account</span>
									<span class="font-mono text-sm text-[var(--color-text)]">{ibkr.account}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Data Farm</span>
									<span class="text-[var(--color-text)]">{ibkr.data_farm}</span>
								</div>
							</div>
						{:else}
							<p class="text-[var(--color-text-muted)]">Waiting for data...</p>
						{/if}
					</div>
				</div>

			{:else if activeTab === 'capital'}
				<!-- Capital Tab - V7.4 -->
				<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
					<!-- Market Controls Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-3">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Market Controls</h2>
						<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
							<!-- Stock Trading Toggle -->
							<div class="rounded-lg bg-[var(--color-bg)] p-4">
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-3">
										<span class="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-xl dark:bg-blue-900">📈</span>
										<div>
											<h3 class="font-medium text-[var(--color-text)]">Stock Trading</h3>
											<p class="text-sm text-[var(--color-text-muted)]">
												{marketControl?.stock_enabled ? 'Active' : 'Disabled'}
												{#if marketControl?.stock_reason}
													- {marketControl.stock_reason}
												{/if}
											</p>
										</div>
									</div>
									<button
										onclick={() => trading.toggleStockTrading(!marketControl?.stock_enabled)}
										class="relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2"
										class:bg-green-500={marketControl?.stock_enabled ?? true}
										class:bg-gray-300={!(marketControl?.stock_enabled ?? true)}
										role="switch"
										aria-checked={marketControl?.stock_enabled ?? true}
										aria-label="Toggle stock trading"
									>
										<span
											class="pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
											class:translate-x-6={marketControl?.stock_enabled ?? true}
											class:translate-x-0={!(marketControl?.stock_enabled ?? true)}
										></span>
									</button>
								</div>
							</div>

							<!-- Forex Trading Toggle -->
							<div class="rounded-lg bg-[var(--color-bg)] p-4">
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-3">
										<span class="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 text-xl dark:bg-purple-900">💱</span>
										<div>
											<h3 class="font-medium text-[var(--color-text)]">Forex Trading</h3>
											<p class="text-sm text-[var(--color-text-muted)]">
												{marketControl?.forex_enabled ? 'Active' : 'Disabled'}
												{#if marketControl?.forex_reason}
													- {marketControl.forex_reason}
												{/if}
											</p>
										</div>
									</div>
									<button
										onclick={() => trading.toggleForexTrading(!marketControl?.forex_enabled)}
										class="relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2"
										class:bg-green-500={marketControl?.forex_enabled ?? true}
										class:bg-gray-300={!(marketControl?.forex_enabled ?? true)}
										role="switch"
										aria-checked={marketControl?.forex_enabled ?? true}
										aria-label="Toggle forex trading"
									>
										<span
											class="pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
											class:translate-x-6={marketControl?.forex_enabled ?? true}
											class:translate-x-0={!(marketControl?.forex_enabled ?? true)}
										></span>
									</button>
								</div>
							</div>
						</div>
					</div>

					<!-- Account Summary Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-2">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Account Summary</h2>
						{#if account}
							<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Net Liquidation</p>
									<p class="text-2xl font-bold text-[var(--color-text)]">
										{formatCurrency(account.net_liquidation)}
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Available Funds</p>
									<p class="text-2xl font-bold text-green-500">
										{formatCurrency(account.available_funds)}
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Margin Used</p>
									<p class="text-2xl font-bold text-[var(--color-text)]">
										{account.margin_pct_used.toFixed(1)}%
									</p>
									<div class="mt-1 h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
										<div
											class="h-full transition-all"
											class:bg-green-500={account.margin_pct_used < 50}
											class:bg-yellow-500={account.margin_pct_used >= 50 && account.margin_pct_used < 80}
											class:bg-red-500={account.margin_pct_used >= 80}
											style="width: {Math.min(account.margin_pct_used, 100)}%"
										></div>
									</div>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Cushion</p>
									<p class="text-2xl font-bold" class:text-green-500={account.cushion > 0.3} class:text-yellow-500={account.cushion <= 0.3 && account.cushion > 0.15} class:text-red-500={account.cushion <= 0.15}>
										{(account.cushion * 100).toFixed(1)}%
									</p>
								</div>
							</div>

							<!-- Additional account metrics -->
							<div class="mt-4 grid grid-cols-2 gap-4 border-t border-[var(--color-border)] pt-4 md:grid-cols-4">
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Buying Power</p>
									<p class="font-medium text-[var(--color-text)]">{formatCurrency(account.buying_power)}</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Maintenance Margin</p>
									<p class="font-medium text-[var(--color-text)]">{formatCurrency(account.maintenance_margin)}</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Excess Liquidity</p>
									<p class="font-medium text-[var(--color-text)]">{formatCurrency(account.excess_liquidity)}</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">SMA</p>
									<p class="font-medium text-[var(--color-text)]">{formatCurrency(account.sma)}</p>
								</div>
							</div>
						{:else}
							<p class="text-[var(--color-text-muted)]">Waiting for account data...</p>
						{/if}
					</div>

					<!-- Currency Balances Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Currency Balances</h2>
						{#if currencies?.currencies}
							<div class="space-y-3">
								{#each Object.entries(currencies.currencies) as [currency, balance]}
									<div class="flex items-center justify-between rounded-lg bg-[var(--color-bg)] p-3">
										<div class="flex items-center gap-2">
											<span class="text-lg font-bold text-[var(--color-text)]">{currency}</span>
											{#if currency === currencies.base_currency}
												<span class="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-800 dark:bg-blue-900 dark:text-blue-200">Base</span>
											{/if}
										</div>
										<div class="text-right">
											<p class="font-medium text-[var(--color-text)]">
												{new Intl.NumberFormat('en-CA', { style: 'currency', currency }).format(balance.cash)}
											</p>
											{#if balance.settled_cash !== balance.cash}
												<p class="text-xs text-[var(--color-text-muted)]">
													Settled: {new Intl.NumberFormat('en-CA', { style: 'currency', currency }).format(balance.settled_cash)}
												</p>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-[var(--color-text-muted)]">Waiting for currency data...</p>
						{/if}
					</div>

					<!-- Capital Allocation Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-3">
						<div class="flex items-center justify-between mb-4">
							<h2 class="text-lg font-semibold text-[var(--color-text)]">Capital Allocation</h2>
							{#if capital?.session}
								<span class="rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-200">
									Session: {capital.session}
								</span>
							{/if}
						</div>
						{#if capital}
							<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
								<!-- Stock Budget -->
								<div class="rounded-lg bg-[var(--color-bg)] p-4">
									<div class="flex items-center justify-between mb-2">
										<h3 class="font-medium text-[var(--color-text)]">Stocks</h3>
										<span class="h-2 w-2 rounded-full" class:bg-green-500={capital.stock_enabled} class:bg-red-500={!capital.stock_enabled}></span>
									</div>
									<div class="space-y-2">
										<div class="flex justify-between text-sm">
											<span class="text-[var(--color-text-muted)]">Budget</span>
											<span class="text-[var(--color-text)]">{formatCurrency(capital.stock_budget)}</span>
										</div>
										<div class="flex justify-between text-sm">
											<span class="text-[var(--color-text-muted)]">Used</span>
											<span class="text-[var(--color-text)]">{formatCurrency(capital.stock_used)}</span>
										</div>
										<div class="flex justify-between text-sm font-medium">
											<span class="text-[var(--color-text-muted)]">Available</span>
											<span class="text-green-500">{formatCurrency(capital.stock_available)}</span>
										</div>
										<div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
											<div
												class="h-full bg-blue-500"
												style="width: {capital.stock_budget > 0 ? (capital.stock_used / capital.stock_budget) * 100 : 0}%"
											></div>
										</div>
									</div>
								</div>

								<!-- Forex Budget -->
								<div class="rounded-lg bg-[var(--color-bg)] p-4">
									<div class="flex items-center justify-between mb-2">
										<h3 class="font-medium text-[var(--color-text)]">Forex</h3>
										<span class="h-2 w-2 rounded-full" class:bg-green-500={capital.forex_enabled} class:bg-red-500={!capital.forex_enabled}></span>
									</div>
									<div class="space-y-2">
										<div class="flex justify-between text-sm">
											<span class="text-[var(--color-text-muted)]">Budget</span>
											<span class="text-[var(--color-text)]">{formatCurrency(capital.forex_budget)}</span>
										</div>
										<div class="flex justify-between text-sm">
											<span class="text-[var(--color-text-muted)]">Used</span>
											<span class="text-[var(--color-text)]">{formatCurrency(capital.forex_used)}</span>
										</div>
										<div class="flex justify-between text-sm font-medium">
											<span class="text-[var(--color-text-muted)]">Available</span>
											<span class="text-green-500">{formatCurrency(capital.forex_available)}</span>
										</div>
										<div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
											<div
												class="h-full bg-purple-500"
												style="width: {capital.forex_budget > 0 ? (capital.forex_used / capital.forex_budget) * 100 : 0}%"
											></div>
										</div>
									</div>
								</div>

								<!-- Reserve -->
								<div class="rounded-lg bg-[var(--color-bg)] p-4">
									<div class="flex items-center justify-between mb-2">
										<h3 class="font-medium text-[var(--color-text)]">Reserve</h3>
										<span class="text-xs text-[var(--color-text-muted)]">Emergency buffer</span>
									</div>
									<div class="flex items-center justify-center h-20">
										<p class="text-3xl font-bold text-[var(--color-text)]">{formatCurrency(capital.reserve)}</p>
									</div>
									<p class="text-center text-xs text-[var(--color-text-muted)]">
										Protected from allocation
									</p>
								</div>
							</div>
						{:else}
							<p class="text-[var(--color-text-muted)]">Waiting for capital allocation data...</p>
						{/if}
					</div>

					<!-- V7.5: Margin Protection Card -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-3">
						<div class="flex items-center justify-between mb-4">
							<div class="flex items-center gap-3">
								<h2 class="text-lg font-semibold text-[var(--color-text)]">Margin Protection</h2>
								<span class="text-sm text-[var(--color-text-muted)]">
									Pre-market close automatic sell system
								</span>
							</div>
							<button
								onclick={() => trading.toggleMarginProtection(!marginConfig?.enabled)}
								class="relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2"
								class:bg-green-500={marginConfig?.enabled ?? false}
								class:bg-gray-300={!(marginConfig?.enabled ?? false)}
								role="switch"
								aria-checked={marginConfig?.enabled ?? false}
								aria-label="Toggle margin protection"
							>
								<span
									class="pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
									class:translate-x-6={marginConfig?.enabled ?? false}
									class:translate-x-0={!(marginConfig?.enabled ?? false)}
								></span>
							</button>
						</div>

						{#if marginConfig}
							<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
								<!-- Config Summary -->
								<div class="rounded-lg bg-[var(--color-bg)] p-4">
									<h3 class="font-medium text-[var(--color-text)] mb-3">Configuration</h3>
									<div class="space-y-2 text-sm">
										<div class="flex justify-between">
											<span class="text-[var(--color-text-muted)]">Target Cushion</span>
											<span class="text-[var(--color-text)]">{(marginConfig.target_cushion_pct * 100).toFixed(0)}%</span>
										</div>
										<div class="flex justify-between">
											<span class="text-[var(--color-text-muted)]">Min Cushion</span>
											<span class="text-[var(--color-text)]">{(marginConfig.min_cushion_pct * 100).toFixed(0)}%</span>
										</div>
										<div class="flex justify-between">
											<span class="text-[var(--color-text-muted)]">Check Start</span>
											<span class="text-[var(--color-text)]">{marginConfig.check_start_time}</span>
										</div>
										<div class="flex justify-between">
											<span class="text-[var(--color-text-muted)]">Aggressive Time</span>
											<span class="text-[var(--color-text)]">{marginConfig.aggressive_time}</span>
										</div>
									</div>
								</div>

								<!-- Scoring Weights -->
								<div class="rounded-lg bg-[var(--color-bg)] p-4 lg:col-span-2">
									<div class="flex items-center justify-between mb-3">
										<h3 class="font-medium text-[var(--color-text)]">Scoring Weights</h3>
										{#if !editingWeights}
											<button
												onclick={() => editingWeights = true}
												class="text-sm text-[var(--color-primary)] hover:underline"
											>
												Edit
											</button>
										{:else}
											<div class="flex gap-2">
												<button
													onclick={saveWeights}
													class="text-sm text-green-500 hover:underline"
												>
													Save
												</button>
												<button
													onclick={() => editingWeights = false}
													class="text-sm text-red-500 hover:underline"
												>
													Cancel
												</button>
											</div>
										{/if}
									</div>

									{#if editingWeights}
										<div class="space-y-3">
											<div>
												<div class="flex justify-between text-sm mb-1">
													<span class="text-[var(--color-text-muted)]">ML Exit</span>
													<span class="text-[var(--color-text)]">{(tempWeights.weight_ml_exit * 100).toFixed(0)}%</span>
												</div>
												<input type="range" min="0" max="100" step="5"
													bind:value={tempWeights.weight_ml_exit}
													oninput={(e) => tempWeights.weight_ml_exit = parseInt(e.currentTarget.value) / 100}
													class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
												/>
											</div>
											<div>
												<div class="flex justify-between text-sm mb-1">
													<span class="text-[var(--color-text-muted)]">P&L Negative</span>
													<span class="text-[var(--color-text)]">{(tempWeights.weight_pnl_negative * 100).toFixed(0)}%</span>
												</div>
												<input type="range" min="0" max="100" step="5"
													bind:value={tempWeights.weight_pnl_negative}
													oninput={(e) => tempWeights.weight_pnl_negative = parseInt(e.currentTarget.value) / 100}
													class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
												/>
											</div>
											<div>
												<div class="flex justify-between text-sm mb-1">
													<span class="text-[var(--color-text-muted)]">Time Held</span>
													<span class="text-[var(--color-text)]">{(tempWeights.weight_time_held * 100).toFixed(0)}%</span>
												</div>
												<input type="range" min="0" max="100" step="5"
													bind:value={tempWeights.weight_time_held}
													oninput={(e) => tempWeights.weight_time_held = parseInt(e.currentTarget.value) / 100}
													class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
												/>
											</div>
											<div>
												<div class="flex justify-between text-sm mb-1">
													<span class="text-[var(--color-text-muted)]">Stop Proximity</span>
													<span class="text-[var(--color-text)]">{(tempWeights.weight_stop_proximity * 100).toFixed(0)}%</span>
												</div>
												<input type="range" min="0" max="100" step="5"
													bind:value={tempWeights.weight_stop_proximity}
													oninput={(e) => tempWeights.weight_stop_proximity = parseInt(e.currentTarget.value) / 100}
													class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
												/>
											</div>
											<div>
												<div class="flex justify-between text-sm mb-1">
													<span class="text-[var(--color-text-muted)]">Volume Decay</span>
													<span class="text-[var(--color-text)]">{(tempWeights.weight_volume_decay * 100).toFixed(0)}%</span>
												</div>
												<input type="range" min="0" max="100" step="5"
													bind:value={tempWeights.weight_volume_decay}
													oninput={(e) => tempWeights.weight_volume_decay = parseInt(e.currentTarget.value) / 100}
													class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
												/>
											</div>
											<div class="pt-2 border-t border-[var(--color-border)]">
												<div class="flex justify-between text-sm font-medium">
													<span class="text-[var(--color-text-muted)]">Total</span>
													<span class:text-green-500={Math.abs(getTotalWeight() - 1.0) < 0.01}
														class:text-red-500={Math.abs(getTotalWeight() - 1.0) >= 0.01}>
														{(getTotalWeight() * 100).toFixed(0)}%
														{#if Math.abs(getTotalWeight() - 1.0) >= 0.01}
															(must be 100%)
														{/if}
													</span>
												</div>
											</div>
										</div>
									{:else}
										<div class="grid grid-cols-2 gap-2 text-sm">
											<div class="flex justify-between">
												<span class="text-[var(--color-text-muted)]">ML Exit</span>
												<span class="text-[var(--color-text)]">{(marginConfig.weight_ml_exit * 100).toFixed(0)}%</span>
											</div>
											<div class="flex justify-between">
												<span class="text-[var(--color-text-muted)]">P&L Negative</span>
												<span class="text-[var(--color-text)]">{(marginConfig.weight_pnl_negative * 100).toFixed(0)}%</span>
											</div>
											<div class="flex justify-between">
												<span class="text-[var(--color-text-muted)]">Time Held</span>
												<span class="text-[var(--color-text)]">{(marginConfig.weight_time_held * 100).toFixed(0)}%</span>
											</div>
											<div class="flex justify-between">
												<span class="text-[var(--color-text-muted)]">Stop Proximity</span>
												<span class="text-[var(--color-text)]">{(marginConfig.weight_stop_proximity * 100).toFixed(0)}%</span>
											</div>
											<div class="flex justify-between">
												<span class="text-[var(--color-text-muted)]">Volume Decay</span>
												<span class="text-[var(--color-text)]">{(marginConfig.weight_volume_decay * 100).toFixed(0)}%</span>
											</div>
										</div>
									{/if}
								</div>

								<!-- Max Positions Control -->
								<div class="rounded-lg bg-[var(--color-bg)] p-4">
									<h3 class="font-medium text-[var(--color-text)] mb-3">Max Positions</h3>
									<div class="flex items-center gap-2">
										<input type="number" min="1" max="100"
											bind:value={tempMaxPositions}
											class="w-20 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)] focus:border-[var(--color-primary)] focus:outline-none"
										/>
										<button
											onclick={saveMaxPositions}
											class="rounded-lg bg-[var(--color-primary)] px-3 py-2 text-sm font-medium text-white hover:opacity-90"
										>
											Update
										</button>
									</div>
									<p class="mt-2 text-xs text-[var(--color-text-muted)]">
										Current: {tradingConfig?.max_positions ?? 'N/A'}
									</p>
								</div>
							</div>

							<!-- Position Sell Scores -->
							{#if marginScores && marginScores.positions.length > 0}
								<div class="mt-6">
									<h3 class="font-medium text-[var(--color-text)] mb-3">Position Sell Scores</h3>
									<div class="overflow-x-auto">
										<table class="w-full text-sm">
											<thead class="bg-[var(--color-bg)]">
												<tr>
													<th class="px-3 py-2 text-left text-[var(--color-text-muted)]">Symbol</th>
													<th class="px-3 py-2 text-right text-[var(--color-text-muted)]">Score</th>
													<th class="px-3 py-2 text-center text-[var(--color-text-muted)]">Action</th>
													<th class="px-3 py-2 text-right text-[var(--color-text-muted)]">P&L %</th>
													<th class="px-3 py-2 text-right text-[var(--color-text-muted)]">Days</th>
													<th class="px-3 py-2 text-left text-[var(--color-text-muted)]">ML</th>
													<th class="px-3 py-2 text-right text-[var(--color-text-muted)]">Value</th>
												</tr>
											</thead>
											<tbody class="divide-y divide-[var(--color-border)]">
												{#each marginScores.positions as pos}
													<tr class="hover:bg-[var(--color-bg)]">
														<td class="px-3 py-2 font-medium text-[var(--color-text)]">{pos.symbol}</td>
														<td class="px-3 py-2 text-right">
															<span class="rounded-full px-2 py-0.5 text-xs font-medium"
																class:bg-red-100={pos.score >= 0.7}
																class:text-red-800={pos.score >= 0.7}
																class:bg-yellow-100={pos.score >= 0.5 && pos.score < 0.7}
																class:text-yellow-800={pos.score >= 0.5 && pos.score < 0.7}
																class:bg-green-100={pos.score < 0.5}
																class:text-green-800={pos.score < 0.5}
															>
																{(pos.score * 100).toFixed(0)}%
															</span>
														</td>
														<td class="px-3 py-2 text-center">
															<span class="text-xs font-medium"
																class:text-red-500={pos.action === 'SELL_IMMEDIATE'}
																class:text-yellow-500={pos.action === 'SELL_CANDIDATE'}
																class:text-green-500={pos.action === 'HOLD'}
															>
																{pos.action}
															</span>
														</td>
														<td class="px-3 py-2 text-right {getPnlColor(pos.pnl_pct)}">
															{formatPercent(pos.pnl_pct)}
														</td>
														<td class="px-3 py-2 text-right text-[var(--color-text)]">{pos.days_held}</td>
														<td class="px-3 py-2 text-[var(--color-text-muted)]">
															{pos.ml_action} ({(pos.ml_confidence * 100).toFixed(0)}%)
														</td>
														<td class="px-3 py-2 text-right text-[var(--color-text)]">
															{formatCurrency(pos.position_value)}
														</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
							{/if}
						{:else}
							<p class="text-[var(--color-text-muted)]">Waiting for margin protection config...</p>
						{/if}
					</div>
				</div>

			{:else if activeTab === 'services'}
				<!-- Services Tab -->
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
					{#each health.services as service}
						<div class="rounded-xl bg-[var(--color-surface)] p-4 shadow-sm">
							<div class="flex items-center justify-between">
								<h3 class="font-medium text-[var(--color-text)]">{service.name}</h3>
								<span class="h-3 w-3 rounded-full {getStatusColor(service.status)}"></span>
							</div>
							<p class="mt-1 text-sm text-[var(--color-text-muted)]">
								{service.status || 'Unknown'}
							</p>
						</div>
					{/each}
				</div>

				<!-- Detailed Services -->
				<div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
					<!-- ML Entry -->
					{#if $trading.mlEntry}
						<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
							<h3 class="mb-4 font-semibold text-[var(--color-text)]">ML Entry Predictor</h3>
							<div class="grid grid-cols-2 gap-4">
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Predictions (1h)</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{$trading.mlEntry.predictions_1h}
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Accuracy (7d)</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{($trading.mlEntry.accuracy_7d * 100).toFixed(1)}%
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Avg Latency</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{$trading.mlEntry.avg_latency_ms.toFixed(0)}ms
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Cache Hit Rate</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{($trading.mlEntry.cache_hit_rate * 100).toFixed(0)}%
									</p>
								</div>
							</div>
						</div>
					{/if}

					<!-- ML Exit -->
					{#if $trading.mlExit}
						<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
							<h3 class="mb-4 font-semibold text-[var(--color-text)]">ML Exit Predictor</h3>
							<div class="grid grid-cols-2 gap-4">
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Decisions (1h)</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{$trading.mlExit.decisions_1h}
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Hit Rate (7d)</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{($trading.mlExit.hit_rate_7d * 100).toFixed(1)}%
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Avg Latency</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{$trading.mlExit.avg_latency_ms.toFixed(0)}ms
									</p>
								</div>
								<div>
									<p class="text-sm text-[var(--color-text-muted)]">Model Loaded</p>
									<p class="text-xl font-bold text-[var(--color-text)]">
										{$trading.mlExit.model_loaded ? 'Yes' : 'No'}
									</p>
								</div>
							</div>
						</div>
					{/if}
				</div>

			{:else if activeTab === 'positions'}
				<!-- Positions Tab -->
				<div class="rounded-xl bg-[var(--color-surface)] shadow-sm">
					<div class="border-b border-[var(--color-border)] p-4">
						<h2 class="text-lg font-semibold text-[var(--color-text)]">Open Positions</h2>
					</div>
					{#if $trading.positions.length > 0}
						<div class="overflow-x-auto">
							<table class="w-full">
								<thead class="bg-[var(--color-bg)]">
									<tr>
										<th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">Symbol</th>
										<th class="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-muted)]">Type</th>
										<th class="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-muted)]">Qty</th>
										<th class="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-muted)]">Entry</th>
										<th class="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-muted)]">Current</th>
										<th class="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-muted)]">P&L</th>
										<th class="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-muted)]">Score</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-[var(--color-border)]">
									{#each $trading.positions as pos}
										<tr class="hover:bg-[var(--color-bg)]">
											<td class="px-4 py-3 font-medium text-[var(--color-text)]">{pos.symbol}</td>
											<td class="px-4 py-3">
												<span
													class="rounded px-2 py-0.5 text-xs font-medium"
													class:bg-blue-100={pos.asset_type === 'stock'}
													class:text-blue-800={pos.asset_type === 'stock'}
													class:bg-purple-100={pos.asset_type === 'forex'}
													class:text-purple-800={pos.asset_type === 'forex'}
												>
													{pos.asset_type.toUpperCase()}
												</span>
											</td>
											<td class="px-4 py-3 text-right text-[var(--color-text)]">{pos.quantity}</td>
											<td class="px-4 py-3 text-right text-[var(--color-text)]">${pos.entry_price.toFixed(2)}</td>
											<td class="px-4 py-3 text-right text-[var(--color-text)]">${pos.current_price.toFixed(2)}</td>
											<td class="px-4 py-3 text-right font-medium {getPnlColor(pos.unrealized_pnl)}">
												{formatCurrency(pos.unrealized_pnl)}
												<span class="text-xs">({formatPercent(pos.pnl_percent)})</span>
											</td>
											<td class="px-4 py-3 text-right">
												<span
													class="rounded-full px-2 py-0.5 text-xs font-medium"
													class:bg-green-100={pos.score > 0.7}
													class:text-green-800={pos.score > 0.7}
													class:bg-yellow-100={pos.score > 0.5 && pos.score <= 0.7}
													class:text-yellow-800={pos.score > 0.5 && pos.score <= 0.7}
													class:bg-gray-100={pos.score <= 0.5}
													class:text-gray-800={pos.score <= 0.5}
												>
													{(pos.score * 100).toFixed(0)}%
												</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<div class="p-8 text-center text-[var(--color-text-muted)]">
							No open positions
						</div>
					{/if}
				</div>

				<!-- Closed Today -->
				<div class="mt-6 rounded-xl bg-[var(--color-surface)] shadow-sm">
					<div class="border-b border-[var(--color-border)] p-4">
						<h2 class="text-lg font-semibold text-[var(--color-text)]">Closed Today</h2>
					</div>
					{#if $trading.closedToday.length > 0}
						<div class="divide-y divide-[var(--color-border)]">
							{#each $trading.closedToday as trade}
								<div class="flex items-center justify-between p-4">
									<div>
										<p class="font-medium text-[var(--color-text)]">{trade.symbol}</p>
										<p class="text-sm text-[var(--color-text-muted)]">
											{trade.exit_reason} - {trade.duration_min}min
										</p>
									</div>
									<div class="text-right">
										<p class="font-medium {getPnlColor(trade.pnl)}">{formatCurrency(trade.pnl)}</p>
										<p class="text-sm {getPnlColor(trade.pnl_pct)}">{formatPercent(trade.pnl_pct)}</p>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="p-8 text-center text-[var(--color-text-muted)]">
							No trades closed today
						</div>
					{/if}
				</div>

			{:else if activeTab === 'scanner'}
				<!-- Scanner Tab -->
				<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
					<!-- Pipeline Stats -->
					{#if pipeline}
						<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
							<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Stock Pipeline</h2>
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Scanned</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.stock.scanned}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Passed Volume</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.stock.passed_volume}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Passed Pattern</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.stock.passed_pattern}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Passed ML</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.stock.passed_ml}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Entered</span>
									<span class="font-medium text-green-500">{pipeline.stock.entered}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Rejected</span>
									<span class="font-medium text-red-500">{pipeline.stock.rejected}</span>
								</div>
							</div>
						</div>

						<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
							<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Forex Pipeline</h2>
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Pairs Monitored</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.forex.pairs_monitored}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Signals Detected</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.forex.signals_detected}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Passed ML</span>
									<span class="font-medium text-[var(--color-text)]">{pipeline.forex.passed_ml}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Entered</span>
									<span class="font-medium text-green-500">{pipeline.forex.entered}</span>
								</div>
								<div class="flex items-center justify-between">
									<span class="text-[var(--color-text-muted)]">Rejected</span>
									<span class="font-medium text-red-500">{pipeline.forex.rejected}</span>
								</div>
							</div>
						</div>
					{:else}
						<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center shadow-sm lg:col-span-2">
							<p class="text-[var(--color-text-muted)]">Waiting for scanner data...</p>
						</div>
					{/if}

					<!-- Recommendations -->
					<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm lg:col-span-2">
						<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">Top Candidates</h2>
						{#if recommendations.length > 0}
							<div class="grid gap-3 md:grid-cols-2">
								{#each recommendations as candidate}
									<div class="rounded-lg bg-[var(--color-bg)] p-4">
										<div class="flex items-center justify-between">
											<span class="font-medium text-[var(--color-text)]">{candidate.symbol}</span>
											<span
												class="rounded-full px-2 py-0.5 text-xs font-medium"
												class:bg-green-100={candidate.ml_score > 0.8}
												class:text-green-800={candidate.ml_score > 0.8}
												class:bg-yellow-100={candidate.ml_score <= 0.8}
												class:text-yellow-800={candidate.ml_score <= 0.8}
											>
												ML: {(candidate.ml_score * 100).toFixed(0)}%
											</span>
										</div>
										<p class="mt-1 text-sm text-[var(--color-text-muted)]">
											{candidate.pattern}
											{#if candidate.volume_ratio}
												- Vol x{candidate.volume_ratio.toFixed(1)}
											{/if}
										</p>
										{#if candidate.reason_skip}
											<p class="mt-1 text-xs text-orange-500">Skip: {candidate.reason_skip}</p>
										{:else}
											<p class="mt-1 text-xs text-green-500">Ready to enter</p>
										{/if}
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-center text-[var(--color-text-muted)]">No candidates</p>
						{/if}
					</div>
				</div>
			{/if}
		</main>
	</div>
{/if}
