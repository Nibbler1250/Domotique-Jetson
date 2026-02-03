<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$stores/auth';
	import HistoryChart from '$lib/components/trading/HistoryChart.svelte';
	import PositionDetailModal from '$lib/components/trading/PositionDetailModal.svelte';
	import { QuickThemePicker } from '$lib/components/settings';
	import type { Position } from '$lib/stores/trading';
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

	// Active view for center panel
	let activeView = $state<'positions' | 'scanner' | 'history'>('positions');

	// Settings modal state
	let showSettingsModal = $state(false);
	let settingsTab = $state<'limits' | 'budget' | 'margin' | 'services'>('limits');

	// Position detail modal state
	let selectedPosition = $state<Position | null>(null);

	// V7.47.2: Chart modal state (for kiosk mode - can't navigate away)
	// V7.47.3: Extended to support etf, penny_stock types
	type AssetType = 'stock' | 'forex' | 'etf' | 'penny_stock';
	let chartModal = $state<{ symbol: string; assetType: AssetType; interval: string } | null>(null);
	const chartIntervals = ['1', '5', '15', '60', 'D', 'W'] as const;

	function openChart(symbol: string, assetType: AssetType = 'stock', interval: string = '15') {
		chartModal = { symbol, assetType, interval };
	}

	function getChartUrl(symbol: string, assetType: AssetType, interval: string): string {
		// For TradingView: forex uses FX: prefix, everything else uses the symbol directly
		const tvSymbol = assetType === 'forex' ? `FX:${symbol.replace('/', '')}` : symbol;
		return `https://www.tradingview.com/widgetembed/?symbol=${tvSymbol}&interval=${interval}&theme=dark&style=1&locale=en&toolbar_bg=%23000000&enable_publishing=false&hide_top_toolbar=false&hide_legend=false&save_image=false&hide_volume=false`;
	}

	// Collapsed states for panels
	let scannerCollapsed = $state(false);
	let servicesCollapsed = $state(false);

	// V7.25: History data
	let historySummary = $derived($trading.historySummary);
	let allTimeStats = $derived($trading.allTimeStats);

	// V7.4: Capital & Control data
	let account = $derived($trading.account);
	let currencies = $derived($trading.currencies);
	let capital = $derived($trading.capital);
	let marketControl = $derived($trading.marketControl);

	// V7.5: Margin Protection data
	let marginConfig = $derived($trading.marginProtectionConfig);
	let marginScores = $derived($trading.marginProtectionScores);
	let tradingConfig = $derived($trading.tradingConfig);

	// V7.26: Position Size Limits
	let positionLimits = $derived($trading.positionLimits);

	// V7.29: Budget Allocation
	let budgetConfig = $derived($trading.budgetConfig);

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

	// V7.13: Min cushion for entry blocking
	let tempMinCushion = $state(10);

	$effect(() => {
		if (marginConfig) {
			tempMinCushion = Math.round(marginConfig.min_cushion_pct * 100);
		}
	});

	function saveMinCushion() {
		if (tempMinCushion < 1 || tempMinCushion > 50) {
			alert('Min cushion must be between 1% and 50%');
			return;
		}
		trading.updateMinCushion(tempMinCushion / 100);
	}

	// V7.26: Position Size Limits
	let tempStockMaxValue = $state(5000);
	let tempForexMaxValue = $state(5000);

	$effect(() => {
		if (positionLimits) {
			tempStockMaxValue = positionLimits.stock?.max_position_value ?? 5000;
			tempForexMaxValue = positionLimits.forex?.max_position_value ?? 5000;
		}
	});

	function savePositionLimits() {
		if (tempStockMaxValue < 100 || tempStockMaxValue > 50000) {
			alert('Stock max must be between $100 and $50,000');
			return;
		}
		if (tempForexMaxValue < 100 || tempForexMaxValue > 100000) {
			alert('Forex max must be between $100 and $100,000');
			return;
		}
		trading.updatePositionLimits(tempStockMaxValue, tempForexMaxValue);
	}

	// V7.29: Budget Allocation
	let tempStockBudgetPct = $state(60);
	let tempForexBudgetPct = $state(30);
	let tempEnforceBudgetLimits = $state(true);

	$effect(() => {
		if (budgetConfig) {
			tempStockBudgetPct = budgetConfig.allocation?.stock_percent ?? 60;
			tempForexBudgetPct = budgetConfig.allocation?.forex_percent ?? 30;
			tempEnforceBudgetLimits = budgetConfig.enforce_limits ?? true;
		}
	});

	function saveBudgetAllocation() {
		const total = tempStockBudgetPct + tempForexBudgetPct;
		if (total > 100) {
			alert(`Stock + Forex cannot exceed 100% (currently ${total}%)`);
			return;
		}
		if (tempStockBudgetPct < 0 || tempStockBudgetPct > 100) {
			alert('Stock budget must be between 0% and 100%');
			return;
		}
		if (tempForexBudgetPct < 0 || tempForexBudgetPct > 100) {
			alert('Forex budget must be between 0% and 100%');
			return;
		}
		trading.updateBudgetAllocation(tempStockBudgetPct, tempForexBudgetPct, tempEnforceBudgetLimits);
	}

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

	// Formatting functions
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(value);
	}

	function formatCurrencyCompact(value: number): string {
		if (Math.abs(value) >= 1000000) {
			return `$${(value / 1000000).toFixed(2)}M`;
		}
		if (Math.abs(value) >= 1000) {
			return `$${(value / 1000).toFixed(1)}K`;
		}
		return formatCurrency(value);
	}

	function formatPercent(value: number): string {
		return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
	}

	function formatHeldTime(entryTime: number | undefined): string {
		if (!entryTime) return '-';
		const now = Date.now() / 1000;
		const seconds = now - entryTime;

		// V7.47: Handle negative values (clock skew between trader and browser)
		if (seconds < 0) {
			return 'just now';
		}

		if (seconds < 60) return `${Math.floor(seconds)}s`;
		if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
		if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
		const days = Math.floor(seconds / 86400);
		const hours = Math.floor((seconds % 86400) / 3600);
		return `${days}d ${hours}h`;
	}

	function formatTime(isoString: string | null): string {
		if (!isoString) return 'N/A';
		const date = new Date(isoString);
		return date.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
	}

	function getLatencyColor(latency: number): string {
		if (latency < 50) return 'text-profit';
		if (latency < 200) return 'text-warning';
		return 'text-loss';
	}

	function getPnlColor(pnl: number): string {
		if (pnl > 0) return 'text-profit';
		if (pnl < 0) return 'text-loss';
		return 'text-muted';
	}

	// V7.47.3: Asset type styling helper
	function getAssetTypeStyle(assetType: string | undefined): { bg: string; text: string; label: string } {
		switch (assetType) {
			case 'forex':
				return { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'FOREX' };
			case 'etf':
				return { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'ETF' };
			case 'penny_stock':
				return { bg: 'bg-rose-500/20', text: 'text-rose-400', label: 'PENNY' };
			case 'stock':
			default:
				return { bg: 'bg-info-dim', text: 'text-info', label: 'STOCK' };
		}
	}

	function getStatusColor(status: string | undefined): string {
		switch (status) {
			case 'HEALTHY':
			case 'CONNECTED':
			case 'RUNNING':
				return 'bg-profit';
			case 'DEGRADED':
			case 'PAUSED':
				return 'bg-warning';
			case 'DOWN':
			case 'DISCONNECTED':
			case 'STOPPED':
				return 'bg-loss';
			default:
				return 'bg-muted';
		}
	}

	// Keyboard shortcuts
	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') showSettingsModal = false;
		if (e.key === '1' && e.ctrlKey) { activeView = 'positions'; e.preventDefault(); }
		if (e.key === '2' && e.ctrlKey) { activeView = 'scanner'; e.preventDefault(); }
		if (e.key === '3' && e.ctrlKey) { activeView = 'history'; e.preventDefault(); }
	}
</script>

<svelte:head>
	<title>Trading Terminal - Momentum V7</title>
</svelte:head>

<svelte:window on:keydown={handleKeydown} />

{#if !hasAccess}
	<div class="flex min-h-screen items-center justify-center bg-terminal-base">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-loss">Access Denied</h1>
			<p class="mt-2 text-muted">This section is restricted to admin users.</p>
			<a href="/dashboard" class="mt-4 inline-block text-info underline">Back to Dashboard</a>
		</div>
	</div>
{:else}
	<div class="flex h-screen flex-col bg-terminal-base text-primary font-mono">
		<!-- ==================== HEADER BAR (48px) ==================== -->
		<header class="flex h-12 items-center justify-between border-b border-terminal-border bg-terminal-panel px-3">
			<div class="flex items-center gap-4">
				<!-- Logo & Title -->
				<a href="/dashboard" class="flex items-center gap-2 text-muted hover:text-primary transition-colors">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
					</svg>
				</a>
				<div class="flex items-center gap-2">
					<div class="flex h-7 w-7 items-center justify-center rounded bg-gradient-to-br from-profit to-emerald-600">
						<span class="text-xs font-bold text-white">M7</span>
					</div>
					<span class="text-sm font-semibold">Momentum Trader V7</span>
				</div>

				<!-- Connection Status -->
				<div class="flex items-center gap-2 text-xs">
					<span class="relative flex h-2 w-2">
						<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
							class:bg-profit={connected}
							class:bg-loss={!connected}></span>
						<span class="relative inline-flex h-2 w-2 rounded-full"
							class:bg-profit={connected}
							class:bg-loss={!connected}></span>
					</span>
					<span class:text-profit={connected} class:text-loss={!connected}>
						{connected ? 'LIVE' : 'OFFLINE'}
					</span>
				</div>

				<!-- Trader Status Badge -->
				<div class="rounded px-2 py-0.5 text-xs font-medium"
					class:bg-profit-dim={status.status === 'RUNNING'}
					class:text-profit={status.status === 'RUNNING'}
					class:bg-warning-dim={status.status === 'PAUSED'}
					class:text-warning={status.status === 'PAUSED'}
					class:bg-loss-dim={status.status === 'STOPPED' || status.status === 'OFFLINE'}
					class:text-loss={status.status === 'STOPPED' || status.status === 'OFFLINE'}
					class:bg-terminal-card={status.status === 'UNKNOWN'}
					class:text-muted={status.status === 'UNKNOWN'}>
					{#if status.mode}<span class="opacity-70">{status.mode}</span> · {/if}{status.status}
					{#if status.isStale}<span class="ml-1 text-loss">!</span>{/if}
				</div>
			</div>

			<div class="flex items-center gap-4 text-xs">
				<!-- IBKR Latency -->
				{#if ibkr}
					<div class="flex items-center gap-2">
						<span class="text-muted">IBKR</span>
						<span class={getLatencyColor(ibkr.latency_ms)}>{ibkr.latency_ms}ms</span>
					</div>
				{/if}

				<!-- Last Update -->
				{#if lastUpdate}
					<span class="text-muted">{formatTime(lastUpdate)}</span>
				{/if}

				<!-- Error Count -->
				{#if $hasErrors}
					<span class="flex items-center gap-1 text-loss">
						<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
						</svg>
						{errors?.errors_1h}
					</span>
				{/if}

				<!-- Theme Picker -->
				<QuickThemePicker />

				<!-- Settings Button -->
				<button
					onclick={() => showSettingsModal = true}
					class="rounded p-1 text-muted hover:text-primary hover:bg-terminal-hover transition-colors"
					title="Settings (Position Limits, Budget, Margin)">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
					</svg>
				</button>
			</div>
		</header>

		<!-- Error/Stale Banner -->
		{#if error}
			<div class="bg-loss-dim px-4 py-1.5 text-center text-xs text-loss">{error}</div>
		{/if}
		{#if status.isStale && status.status === 'OFFLINE'}
			<div class="bg-warning-dim px-4 py-1.5 text-center text-xs text-warning">
				No heartbeat for 90+ seconds. Data may be stale.
				{#if status.lastUpdate} Last: {formatTime(status.lastUpdate)}{/if}
			</div>
		{/if}

		<!-- ==================== MAIN 3-PANEL LAYOUT ==================== -->
		<div class="flex flex-1 overflow-hidden">
			<!-- ==================== LEFT PANEL (Account & Controls) ==================== -->
			<aside class="flex w-56 flex-col border-r border-terminal-border bg-terminal-panel">
				<!-- P&L Banner -->
				<div class="border-b border-terminal-border p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-1">Total P&L</div>
					{#if metrics}
						<div class="text-2xl font-bold tabular-nums {getPnlColor(metrics.pnlTotal)}">
							{formatCurrency(metrics.pnlTotal)}
						</div>
						<div class="flex gap-2 text-xs mt-1">
							<span class={getPnlColor(metrics.pnlUnrealized)}>Unreal: {formatCurrencyCompact(metrics.pnlUnrealized)}</span>
							<span class="text-muted">|</span>
							<span class={getPnlColor(metrics.pnlRealized)}>Real: {formatCurrencyCompact(metrics.pnlRealized)}</span>
						</div>
					{:else}
						<div class="text-muted">---</div>
					{/if}
				</div>

				<!-- Account Summary -->
				<div class="border-b border-terminal-border p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">Account</div>
					{#if account}
						<div class="space-y-1.5 text-sm">
							<div class="flex justify-between">
								<span class="text-muted">Equity</span>
								<span class="tabular-nums">{formatCurrencyCompact(account.net_liquidation)}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-muted">Available</span>
								<span class="tabular-nums text-profit">{formatCurrencyCompact(account.available_funds)}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-muted">Buying Power</span>
								<span class="tabular-nums">{formatCurrencyCompact(account.buying_power)}</span>
							</div>
						</div>
					{:else}
						<div class="text-muted text-sm">Loading...</div>
					{/if}
				</div>

				<!-- Margin Health -->
				<div class="border-b border-terminal-border p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">Margin Health</div>
					{#if account}
						<div class="space-y-2">
							<div>
								<div class="flex justify-between text-xs mb-1">
									<span class="text-muted">Used</span>
									<span class:text-profit={account.margin_pct_used < 50}
										  class:text-warning={account.margin_pct_used >= 50 && account.margin_pct_used < 80}
										  class:text-loss={account.margin_pct_used >= 80}>
										{account.margin_pct_used.toFixed(1)}%
									</span>
								</div>
								<div class="h-1 overflow-hidden rounded-full bg-terminal-hover">
									<div class="h-full transition-all"
										class:bg-profit={account.margin_pct_used < 50}
										class:bg-warning={account.margin_pct_used >= 50 && account.margin_pct_used < 80}
										class:bg-loss={account.margin_pct_used >= 80}
										style="width: {Math.min(account.margin_pct_used, 100)}%"></div>
								</div>
							</div>
							<div class="flex justify-between text-sm">
								<span class="text-muted">Cushion</span>
								<span class:text-profit={account.cushion > 0.3}
									  class:text-warning={account.cushion <= 0.3 && account.cushion > 0.15}
									  class:text-loss={account.cushion <= 0.15}>
									{(account.cushion * 100).toFixed(1)}%
								</span>
							</div>
						</div>
					{:else}
						<div class="text-muted text-sm">Loading...</div>
					{/if}
				</div>

				<!-- Capital Allocation -->
				<div class="border-b border-terminal-border p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">Allocation</div>
					{#if capital}
						<div class="space-y-2">
							<!-- Stock -->
							<div>
								<div class="flex justify-between text-xs mb-1">
									<span class="flex items-center gap-1">
										<span class="h-2 w-2 rounded-sm bg-info"></span>
										Stock
									</span>
									<span class="tabular-nums">{formatCurrencyCompact(capital.stock_used)} / {formatCurrencyCompact(capital.stock_budget)}</span>
								</div>
								<div class="h-1 overflow-hidden rounded-full bg-terminal-hover">
									<div class="h-full bg-info" style="width: {capital.stock_budget > 0 ? (capital.stock_used / capital.stock_budget) * 100 : 0}%"></div>
								</div>
							</div>
							<!-- Forex -->
							<div>
								<div class="flex justify-between text-xs mb-1">
									<span class="flex items-center gap-1">
										<span class="h-2 w-2 rounded-sm bg-purple-500"></span>
										Forex
									</span>
									<span class="tabular-nums">{formatCurrencyCompact(capital.forex_used)} / {formatCurrencyCompact(capital.forex_budget)}</span>
								</div>
								<div class="h-1 overflow-hidden rounded-full bg-terminal-hover">
									<div class="h-full bg-purple-500" style="width: {capital.forex_budget > 0 ? (capital.forex_used / capital.forex_budget) * 100 : 0}%"></div>
								</div>
							</div>
							<!-- Reserve -->
							<div class="flex justify-between text-xs">
								<span class="flex items-center gap-1">
									<span class="h-2 w-2 rounded-sm bg-profit"></span>
									Reserve
								</span>
								<span class="tabular-nums text-profit">{formatCurrencyCompact(capital.reserve)}</span>
							</div>
						</div>
					{:else}
						<div class="text-muted text-sm">Loading...</div>
					{/if}
				</div>

				<!-- Currency Balances -->
				{#if currencies?.currencies}
					<div class="border-b border-terminal-border p-3">
						<div class="text-xs text-muted uppercase tracking-wide mb-2">Currencies</div>
						<div class="space-y-1 text-sm">
							{#each Object.entries(currencies.currencies) as [currency, balance]}
								<div class="flex justify-between">
									<span class="text-muted">{currency}</span>
									<span class="tabular-nums">{new Intl.NumberFormat('en-CA', { style: 'currency', currency, maximumFractionDigits: 0 }).format(balance.cash)}</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Trading Controls -->
				<div class="p-3 mt-auto">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">Controls</div>
					<div class="space-y-2">
						<!-- Stock Toggle -->
						<div class="flex items-center justify-between">
							<span class="text-sm flex items-center gap-2">
								<span class="h-2 w-2 rounded-full" class:bg-profit={marketControl?.stock_enabled} class:bg-loss={!marketControl?.stock_enabled}></span>
								Stock
							</span>
							<button
								onclick={() => trading.toggleStockTrading(!marketControl?.stock_enabled)}
								class="rounded px-2 py-0.5 text-xs font-medium transition-colors"
								class:bg-profit-dim={marketControl?.stock_enabled}
								class:text-profit={marketControl?.stock_enabled}
								class:bg-terminal-card={!marketControl?.stock_enabled}
								class:text-muted={!marketControl?.stock_enabled}>
								{marketControl?.stock_enabled ? 'ON' : 'OFF'}
							</button>
						</div>
						<!-- Forex Toggle -->
						<div class="flex items-center justify-between">
							<span class="text-sm flex items-center gap-2">
								<span class="h-2 w-2 rounded-full" class:bg-profit={marketControl?.forex_enabled} class:bg-loss={!marketControl?.forex_enabled}></span>
								Forex
							</span>
							<button
								onclick={() => trading.toggleForexTrading(!marketControl?.forex_enabled)}
								class="rounded px-2 py-0.5 text-xs font-medium transition-colors"
								class:bg-profit-dim={marketControl?.forex_enabled}
								class:text-profit={marketControl?.forex_enabled}
								class:bg-terminal-card={!marketControl?.forex_enabled}
								class:text-muted={!marketControl?.forex_enabled}>
								{marketControl?.forex_enabled ? 'ON' : 'OFF'}
							</button>
						</div>
						<!-- Emergency Stop -->
						<button
							onclick={() => { trading.toggleStockTrading(false); trading.toggleForexTrading(false); }}
							class="w-full rounded bg-loss py-1.5 text-xs font-bold text-white uppercase tracking-wide hover:bg-red-600 transition-colors">
							Emergency Stop
						</button>
					</div>
				</div>
			</aside>

			<!-- ==================== CENTER PANEL (Main Trading View) ==================== -->
			<main class="flex flex-1 flex-col overflow-hidden">
				<!-- Metrics Bar -->
				<div class="flex items-center justify-between border-b border-terminal-border bg-terminal-card px-4 py-2">
					<div class="flex items-center gap-6">
						{#if metrics}
							<div class="text-center">
								<div class="text-xs text-muted">Win Rate</div>
								<div class="text-lg font-bold tabular-nums" class:text-profit={metrics.winRate >= 50} class:text-loss={metrics.winRate < 50}>
									{metrics.winRate.toFixed(0)}%
								</div>
							</div>
							<div class="text-center">
								<div class="text-xs text-muted">Trades Today</div>
								<div class="text-lg font-bold tabular-nums">{metrics.tradesToday}</div>
							</div>
							<div class="text-center">
								<div class="text-xs text-muted">Open</div>
								<div class="text-lg font-bold tabular-nums text-info">{metrics.positionsOpen}</div>
							</div>
							<!-- V7.47.5: Risk-adjusted metrics -->
							<div class="border-l border-terminal-border pl-4"></div>
							<div class="text-center" title="Sharpe Ratio (annualized) - Risk-adjusted return">
								<div class="text-xs text-muted">Sharpe</div>
								<div class="text-lg font-bold tabular-nums" class:text-profit={metrics.sharpeRatio > 1} class:text-warning={metrics.sharpeRatio > 0 && metrics.sharpeRatio <= 1} class:text-loss={metrics.sharpeRatio <= 0}>
									{metrics.sharpeRatio.toFixed(2)}
								</div>
							</div>
							<div class="text-center" title="Sortino Ratio (annualized) - Downside risk-adjusted return">
								<div class="text-xs text-muted">Sortino</div>
								<div class="text-lg font-bold tabular-nums" class:text-profit={metrics.sortinoRatio > 1} class:text-warning={metrics.sortinoRatio > 0 && metrics.sortinoRatio <= 1} class:text-loss={metrics.sortinoRatio <= 0}>
									{metrics.sortinoRatio.toFixed(2)}
								</div>
							</div>
							<div class="text-center" title="Profit Factor - Gross profit / Gross loss">
								<div class="text-xs text-muted">P.Factor</div>
								<div class="text-lg font-bold tabular-nums" class:text-profit={metrics.profitFactor > 1.5} class:text-warning={metrics.profitFactor > 1 && metrics.profitFactor <= 1.5} class:text-loss={metrics.profitFactor <= 1}>
									{metrics.profitFactor.toFixed(2)}
								</div>
							</div>
						{/if}
					</div>

					<!-- View Tabs -->
					<div class="flex gap-1">
						<button
							onclick={() => activeView = 'positions'}
							class="rounded px-3 py-1 text-xs font-medium transition-colors hover:text-primary"
							class:bg-terminal-panel={activeView === 'positions'}
							class:text-primary={activeView === 'positions'}
							class:text-muted={activeView !== 'positions'}>
							Positions
						</button>
						<button
							onclick={() => activeView = 'scanner'}
							class="rounded px-3 py-1 text-xs font-medium transition-colors hover:text-primary"
							class:bg-terminal-panel={activeView === 'scanner'}
							class:text-primary={activeView === 'scanner'}
							class:text-muted={activeView !== 'scanner'}>
							Scanner
						</button>
						<button
							onclick={() => activeView = 'history'}
							class="rounded px-3 py-1 text-xs font-medium transition-colors hover:text-primary"
							class:bg-terminal-panel={activeView === 'history'}
							class:text-primary={activeView === 'history'}
							class:text-muted={activeView !== 'history'}>
							History
						</button>
					</div>
				</div>

				<!-- View Content -->
				<div class="flex-1 overflow-auto p-3">
					{#if activeView === 'positions'}
						<!-- ==================== POSITIONS VIEW ==================== -->
						<div class="space-y-3">
							<!-- Open Positions Table -->
							<div class="rounded border border-terminal-border bg-terminal-panel">
								<div class="flex items-center justify-between border-b border-terminal-border px-3 py-2">
									<h2 class="text-xs font-medium uppercase tracking-wide text-muted">Open Positions ({$trading.positions.length})</h2>
								</div>
								{#if $trading.positions.length > 0}
									<div class="overflow-x-auto">
										<table class="w-full text-xs">
											<thead class="bg-terminal-card">
												<tr>
													<th class="px-3 py-2 text-left font-medium text-muted">Symbol</th>
													<th class="px-3 py-2 text-left font-medium text-muted">Type</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Qty</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Entry</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Current</th>
													<th class="px-3 py-2 text-right font-medium text-muted">P&L</th>
													<th class="px-3 py-2 text-right font-medium text-muted">%</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Held</th>
													<th class="px-3 py-2 text-right font-medium text-muted">ML</th>
													<th class="px-3 py-2 text-center font-medium text-muted">Chart</th>
												</tr>
											</thead>
											<tbody class="divide-y divide-terminal-border">
												{#each $trading.positions as pos}
													{@const assetStyle = getAssetTypeStyle(pos.asset_type)}
													<tr
														class="hover:bg-terminal-hover cursor-pointer transition-colors"
														onclick={() => (selectedPosition = pos)}
														role="button"
														tabindex="0"
														onkeydown={(e) => e.key === 'Enter' && (selectedPosition = pos)}
													>
														<td class="px-3 py-2 font-medium">{pos.symbol}</td>
														<td class="px-3 py-2">
															<span class="rounded px-1.5 py-0.5 text-[10px] font-medium {assetStyle.bg} {assetStyle.text}">
																{assetStyle.label}
															</span>
														</td>
														<td class="px-3 py-2 text-right tabular-nums">
															{pos.asset_type === 'forex' ? `$${pos.quantity.toFixed(0)}` : pos.quantity}
														</td>
														<td class="px-3 py-2 text-right tabular-nums text-muted">
															${pos.entry_price.toFixed(pos.asset_type === 'forex' ? 5 : 2)}
														</td>
														<td class="px-3 py-2 text-right tabular-nums">
															${pos.current_price.toFixed(pos.asset_type === 'forex' ? 5 : 2)}
														</td>
														<td class="px-3 py-2 text-right tabular-nums font-medium {getPnlColor(pos.unrealized_pnl)}">
															{formatCurrency(pos.unrealized_pnl)}
														</td>
														<td class="px-3 py-2 text-right tabular-nums {getPnlColor(pos.pnl_percent)}">
															{formatPercent(pos.pnl_percent)}
														</td>
														<td class="px-3 py-2 text-right tabular-nums text-muted">
															{formatHeldTime(pos.entry_time)}
														</td>
														<td class="px-3 py-2 text-right">
															<span class="rounded px-1.5 py-0.5 text-[10px] font-medium"
																class:bg-profit-dim={(pos.ml_score || 0) > 0.7}
																class:text-profit={(pos.ml_score || 0) > 0.7}
																class:bg-warning-dim={(pos.ml_score || 0) > 0.5 && (pos.ml_score || 0) <= 0.7}
																class:text-warning={(pos.ml_score || 0) > 0.5 && (pos.ml_score || 0) <= 0.7}
																class:bg-terminal-card={(pos.ml_score || 0) <= 0.5}
																class:text-muted={(pos.ml_score || 0) <= 0.5}>
																{((pos.ml_score || 0) * 100).toFixed(0)}%
															</span>
														</td>
														<td class="px-3 py-2 text-center">
															<button
																onclick={(e) => { e.stopPropagation(); openChart(pos.symbol, pos.asset_type as 'stock' | 'forex', '15'); }}
																class="px-2 py-1 rounded bg-terminal-card hover:bg-terminal-hover text-xs"
																title="View Chart"
															>
																📊
															</button>
														</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								{:else}
									<div class="p-6 text-center text-muted text-sm">No open positions</div>
								{/if}
							</div>

							<!-- Closed Today - V7.47.2: Enriched with qty, prices, ML -->
							<div class="rounded border border-terminal-border bg-terminal-panel">
								<div class="flex items-center justify-between border-b border-terminal-border px-3 py-2">
									<h2 class="text-xs font-medium uppercase tracking-wide text-muted">Closed Today ({$trading.closedToday.length})</h2>
								</div>
								{#if $trading.closedToday.length > 0}
									<div class="divide-y divide-terminal-border max-h-96 overflow-y-auto">
										{#each $trading.closedToday as trade, i (trade.symbol + trade.exit_time)}
											{@const tradeAssetStyle = getAssetTypeStyle(trade.asset_type)}
											<details class="group">
												<summary class="flex items-center justify-between px-3 py-2 hover:bg-terminal-hover cursor-pointer list-none">
													<div class="flex items-center gap-2">
														<!-- Win/Loss indicator -->
														<span class="w-2 h-2 rounded-full {trade.is_win || trade.pnl > 0 ? 'bg-profit' : 'bg-loss'}"></span>
														<span class="font-medium">{trade.symbol}</span>
														<span class="text-xs px-1.5 py-0.5 rounded {tradeAssetStyle.bg} {tradeAssetStyle.text}">
															{tradeAssetStyle.label}
														</span>
														<span class="text-xs text-muted">{trade.exit_reason}</span>
														<span class="text-xs text-muted">({trade.duration_min}m)</span>
													</div>
													<div class="flex items-center gap-3">
														<div class="text-right">
															<span class="font-medium tabular-nums {getPnlColor(trade.pnl)}">{formatCurrency(trade.pnl)}</span>
															<span class="text-xs ml-1 {getPnlColor(trade.pnl_pct)}">{formatPercent(trade.pnl_pct)}</span>
														</div>
														<span class="text-muted group-open:rotate-180 transition-transform">▼</span>
													</div>
												</summary>
												<!-- Expanded details -->
												<div class="px-3 py-2 bg-terminal-card/50 text-xs border-t border-terminal-border/50">
													<div class="grid grid-cols-2 md:grid-cols-4 gap-2">
														{#if trade.quantity}
															<div>
																<span class="text-muted">Qty:</span>
																<span class="ml-1 font-medium">{trade.quantity.toLocaleString()}</span>
															</div>
														{/if}
														{#if trade.entry_price}
															<div>
																<span class="text-muted">Entry:</span>
																<span class="ml-1 font-medium tabular-nums">${trade.entry_price.toFixed(trade.asset_type === 'forex' ? 5 : 2)}</span>
															</div>
														{/if}
														{#if trade.exit_price}
															<div>
																<span class="text-muted">Exit:</span>
																<span class="ml-1 font-medium tabular-nums">${trade.exit_price.toFixed(trade.asset_type === 'forex' ? 5 : 2)}</span>
															</div>
														{/if}
														{#if trade.ml_score !== undefined && trade.ml_score > 0}
															<div>
																<span class="text-muted">ML Score:</span>
																<span class="ml-1 font-medium {trade.ml_score >= 0.7 ? 'text-profit' : trade.ml_score >= 0.5 ? 'text-warning' : 'text-muted'}">{(trade.ml_score * 100).toFixed(0)}%</span>
															</div>
														{/if}
														{#if trade.exit_time}
															<div>
																<span class="text-muted">Closed:</span>
																<span class="ml-1">{new Date(trade.exit_time).toLocaleTimeString()}</span>
															</div>
														{/if}
													</div>
													<!-- Chart button - V7.47.2: Opens modal instead of navigating (kiosk compatible) -->
													<div class="mt-2 flex gap-2">
														<button
															onclick={() => openChart(trade.symbol, trade.asset_type || 'stock', '15')}
															class="inline-flex items-center gap-1 px-2 py-1 rounded bg-terminal-border hover:bg-terminal-hover text-xs"
														>
															📊 Chart
														</button>
														<button
															onclick={() => openChart(trade.symbol, trade.asset_type || 'stock', '60')}
															class="inline-flex items-center gap-1 px-2 py-1 rounded bg-terminal-border hover:bg-terminal-hover text-xs"
														>
															📊 1H
														</button>
														<button
															onclick={() => openChart(trade.symbol, trade.asset_type || 'stock', 'D')}
															class="inline-flex items-center gap-1 px-2 py-1 rounded bg-terminal-border hover:bg-terminal-hover text-xs"
														>
															📊 Daily
														</button>
													</div>
												</div>
											</details>
										{/each}
									</div>
								{:else}
									<div class="p-4 text-center text-muted text-sm">No trades closed today</div>
								{/if}
							</div>

							<!-- Margin Protection Scores (if available) -->
							{#if marginScores && marginScores.positions.length > 0}
								<div class="rounded border border-terminal-border bg-terminal-panel">
									<div class="flex items-center justify-between border-b border-terminal-border px-3 py-2">
										<h2 class="text-xs font-medium uppercase tracking-wide text-muted">Margin Protection Scores</h2>
										<span class="text-xs" class:text-profit={marginConfig?.enabled} class:text-muted={!marginConfig?.enabled}>
											{marginConfig?.enabled ? 'ACTIVE' : 'DISABLED'}
										</span>
									</div>
									<div class="overflow-x-auto">
										<table class="w-full text-xs">
											<thead class="bg-terminal-card">
												<tr>
													<th class="px-3 py-2 text-left font-medium text-muted">Symbol</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Score</th>
													<th class="px-3 py-2 text-center font-medium text-muted">Action</th>
													<th class="px-3 py-2 text-right font-medium text-muted">P&L</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Days</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Value</th>
												</tr>
											</thead>
											<tbody class="divide-y divide-terminal-border">
												{#each marginScores.positions as pos}
													<tr class="hover:bg-terminal-hover">
														<td class="px-3 py-2 font-medium">{pos.symbol}</td>
														<td class="px-3 py-2 text-right">
															<span class="rounded px-1.5 py-0.5 text-[10px] font-medium"
																class:bg-loss-dim={pos.score >= 0.7}
																class:text-loss={pos.score >= 0.7}
																class:bg-warning-dim={pos.score >= 0.5 && pos.score < 0.7}
																class:text-warning={pos.score >= 0.5 && pos.score < 0.7}
																class:bg-profit-dim={pos.score < 0.5}
																class:text-profit={pos.score < 0.5}>
																{(pos.score * 100).toFixed(0)}%
															</span>
														</td>
														<td class="px-3 py-2 text-center">
															<span class="text-[10px] font-medium"
																class:text-loss={pos.action === 'SELL_IMMEDIATE'}
																class:text-warning={pos.action === 'SELL_CANDIDATE'}
																class:text-profit={pos.action === 'HOLD'}>
																{pos.action}
															</span>
														</td>
														<td class="px-3 py-2 text-right tabular-nums {getPnlColor(pos.pnl_pct)}">
															{formatPercent(pos.pnl_pct)}
														</td>
														<td class="px-3 py-2 text-right tabular-nums text-muted">{pos.days_held}</td>
														<td class="px-3 py-2 text-right tabular-nums">{formatCurrencyCompact(pos.position_value)}</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
							{/if}
						</div>

					{:else if activeView === 'scanner'}
						<!-- ==================== SCANNER VIEW ==================== -->
						<div class="space-y-3">
							<!-- Pipeline Stats -->
							{#if pipeline}
								<div class="grid grid-cols-2 gap-3">
									<!-- Stock Pipeline -->
									<div class="rounded border border-terminal-border bg-terminal-panel p-3">
										<div class="flex items-center gap-2 mb-3">
											<span class="h-2 w-2 rounded-full bg-info"></span>
											<h3 class="text-xs font-medium uppercase tracking-wide text-muted">Stock Pipeline</h3>
										</div>
										<div class="grid grid-cols-3 gap-2 text-center">
											<div>
												<div class="text-lg font-bold tabular-nums">{pipeline.stock.scanned}</div>
												<div class="text-[10px] text-muted">Scanned</div>
											</div>
											<div>
												<div class="text-lg font-bold tabular-nums text-info">{pipeline.stock.passed_ml}</div>
												<div class="text-[10px] text-muted">ML Pass</div>
											</div>
											<div>
												<div class="text-lg font-bold tabular-nums text-profit">{pipeline.stock.entered}</div>
												<div class="text-[10px] text-muted">Entered</div>
											</div>
										</div>
									</div>
									<!-- Forex Pipeline -->
									<div class="rounded border border-terminal-border bg-terminal-panel p-3">
										<div class="flex items-center gap-2 mb-3">
											<span class="h-2 w-2 rounded-full bg-purple-500"></span>
											<h3 class="text-xs font-medium uppercase tracking-wide text-muted">Forex Pipeline</h3>
										</div>
										<div class="grid grid-cols-3 gap-2 text-center">
											<div>
												<div class="text-lg font-bold tabular-nums">{pipeline.forex.pairs_monitored}</div>
												<div class="text-[10px] text-muted">Monitored</div>
											</div>
											<div>
												<div class="text-lg font-bold tabular-nums text-purple-400">{pipeline.forex.passed_ml}</div>
												<div class="text-[10px] text-muted">ML Pass</div>
											</div>
											<div>
												<div class="text-lg font-bold tabular-nums text-profit">{pipeline.forex.entered}</div>
												<div class="text-[10px] text-muted">Entered</div>
											</div>
										</div>
									</div>
								</div>
							{/if}

							<!-- Top Candidates -->
							<div class="rounded border border-terminal-border bg-terminal-panel">
								<div class="border-b border-terminal-border px-3 py-2">
									<h2 class="text-xs font-medium uppercase tracking-wide text-muted">Top Candidates ({recommendations.length})</h2>
								</div>
								{#if recommendations.length > 0}
									<div class="grid gap-2 p-3 md:grid-cols-2">
										{#each recommendations as candidate}
											<div class="rounded border border-terminal-border bg-terminal-card p-3">
												<div class="flex items-center justify-between">
													<span class="font-medium">{candidate.symbol}</span>
													<span class="rounded px-1.5 py-0.5 text-[10px] font-medium"
														class:bg-profit-dim={candidate.ml_score > 0.8}
														class:text-profit={candidate.ml_score > 0.8}
														class:bg-warning-dim={candidate.ml_score <= 0.8}
														class:text-warning={candidate.ml_score <= 0.8}>
														ML: {(candidate.ml_score * 100).toFixed(0)}%
													</span>
												</div>
												<div class="mt-1 text-xs text-muted">
													{candidate.pattern}
													{#if candidate.volume_ratio}
														<span class="ml-1">Vol x{candidate.volume_ratio.toFixed(1)}</span>
													{/if}
												</div>
												{#if candidate.reason_skip}
													<div class="mt-1 text-[10px] text-warning">Skip: {candidate.reason_skip}</div>
												{:else}
													<div class="mt-1 text-[10px] text-profit">Ready</div>
												{/if}
											</div>
										{/each}
									</div>
								{:else}
									<div class="p-6 text-center text-muted text-sm">No candidates</div>
								{/if}
							</div>
						</div>

					{:else if activeView === 'history'}
						<!-- ==================== HISTORY VIEW ==================== -->
						<div class="space-y-3">
							<!-- Stats Summary -->
							<div class="grid grid-cols-4 gap-3">
								{#if allTimeStats}
									<div class="rounded border border-terminal-border bg-terminal-panel p-3 text-center">
										<div class="text-[10px] text-muted uppercase">Total Trades</div>
										<div class="text-xl font-bold tabular-nums">{allTimeStats.total_trades}</div>
									</div>
									<div class="rounded border border-terminal-border bg-terminal-panel p-3 text-center">
										<div class="text-[10px] text-muted uppercase">Win Rate</div>
										<div class="text-xl font-bold tabular-nums" class:text-profit={allTimeStats.win_rate >= 50} class:text-loss={allTimeStats.win_rate < 50}>
											{allTimeStats.win_rate.toFixed(1)}%
										</div>
									</div>
									<div class="rounded border border-terminal-border bg-terminal-panel p-3 text-center">
										<div class="text-[10px] text-muted uppercase">Total P&L</div>
										<div class="text-xl font-bold tabular-nums {getPnlColor(allTimeStats.total_pnl)}">
											{formatCurrencyCompact(allTimeStats.total_pnl)}
										</div>
									</div>
									<div class="rounded border border-terminal-border bg-terminal-panel p-3 text-center">
										<div class="text-[10px] text-muted uppercase">Profit Factor</div>
										<div class="text-xl font-bold tabular-nums" class:text-profit={allTimeStats.profit_factor >= 1} class:text-loss={allTimeStats.profit_factor < 1}>
											{allTimeStats.profit_factor.toFixed(2)}
										</div>
									</div>
								{/if}
							</div>

							<!-- Charts -->
							<div class="grid grid-cols-2 gap-3">
								<div class="rounded border border-terminal-border bg-terminal-panel p-3">
									<h3 class="text-xs font-medium uppercase tracking-wide text-muted mb-2">Daily P&L</h3>
									<HistoryChart
										dailyStats={historySummary?.daily_stats || []}
										mlMetrics={historySummary?.ml_metrics || []}
										chartType="pnl"
									/>
								</div>
								<div class="rounded border border-terminal-border bg-terminal-panel p-3">
									<h3 class="text-xs font-medium uppercase tracking-wide text-muted mb-2">Win Rate Trend</h3>
									<HistoryChart
										dailyStats={historySummary?.daily_stats || []}
										mlMetrics={historySummary?.ml_metrics || []}
										chartType="winrate"
									/>
								</div>
							</div>

							<!-- Daily Stats Table -->
							{#if historySummary?.daily_stats && historySummary.daily_stats.length > 0}
								<div class="rounded border border-terminal-border bg-terminal-panel">
									<div class="border-b border-terminal-border px-3 py-2">
										<h2 class="text-xs font-medium uppercase tracking-wide text-muted">Daily Breakdown</h2>
									</div>
									<div class="overflow-x-auto">
										<table class="w-full text-xs">
											<thead class="bg-terminal-card">
												<tr>
													<th class="px-3 py-2 text-left font-medium text-muted">Date</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Trades</th>
													<th class="px-3 py-2 text-right font-medium text-muted">W/L</th>
													<th class="px-3 py-2 text-right font-medium text-muted">Win Rate</th>
													<th class="px-3 py-2 text-right font-medium text-muted">P&L</th>
													<th class="px-3 py-2 text-right font-medium text-muted">PF</th>
												</tr>
											</thead>
											<tbody class="divide-y divide-terminal-border">
												{#each historySummary.daily_stats as day}
													<tr class="hover:bg-terminal-hover">
														<td class="px-3 py-2 font-medium">{day.date}</td>
														<td class="px-3 py-2 text-right tabular-nums">{day.trades}</td>
														<td class="px-3 py-2 text-right">
															<span class="text-profit">{day.wins}</span>/<span class="text-loss">{day.losses}</span>
														</td>
														<td class="px-3 py-2 text-right tabular-nums" class:text-profit={day.win_rate >= 50} class:text-loss={day.win_rate < 50}>
															{day.win_rate.toFixed(1)}%
														</td>
														<td class="px-3 py-2 text-right tabular-nums font-medium {getPnlColor(day.realized_pnl)}">
															{formatCurrency(day.realized_pnl)}
														</td>
														<td class="px-3 py-2 text-right tabular-nums" class:text-profit={day.profit_factor >= 1} class:text-loss={day.profit_factor < 1}>
															{day.profit_factor.toFixed(2)}
														</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</main>

			<!-- ==================== RIGHT PANEL (System Health & Services) ==================== -->
			<aside class="flex w-52 flex-col border-l border-terminal-border bg-terminal-panel">
				<!-- IBKR Connection -->
				<div class="border-b border-terminal-border p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">IBKR</div>
					{#if ibkr}
						<div class="space-y-1.5 text-sm">
							<div class="flex justify-between">
								<span class="text-muted">Status</span>
								<span class="flex items-center gap-1">
									<span class="h-2 w-2 rounded-full {getStatusColor(ibkr.status)}"></span>
									<span class:text-profit={ibkr.status === 'CONNECTED'} class:text-loss={ibkr.status !== 'CONNECTED'}>
										{ibkr.status}
									</span>
								</span>
							</div>
							<div class="flex justify-between">
								<span class="text-muted">Latency</span>
								<span class={getLatencyColor(ibkr.latency_ms)}>{ibkr.latency_ms}ms</span>
							</div>
							<div class="flex justify-between">
								<span class="text-muted">Account</span>
								<span class="text-xs tabular-nums">{ibkr.account}</span>
							</div>
						</div>
					{:else}
						<div class="text-muted text-sm">Loading...</div>
					{/if}
				</div>

				<!-- Services Health -->
				<div class="border-b border-terminal-border p-3">
					<button
						onclick={() => servicesCollapsed = !servicesCollapsed}
						class="flex items-center justify-between w-full text-xs text-muted uppercase tracking-wide mb-2 hover:text-primary">
						<span>Services ({health.healthy}/{health.total})</span>
						<svg class="h-3 w-3 transition-transform" class:rotate-180={!servicesCollapsed} fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
						</svg>
					</button>
					{#if !servicesCollapsed}
						<div class="space-y-1">
							{#each health.services.slice(0, 8) as service}
								<div class="flex items-center justify-between text-xs">
									<span class="text-muted truncate" title={service.name}>{service.name}</span>
									<span class="h-2 w-2 rounded-full {getStatusColor(service.status)}"></span>
								</div>
							{/each}
							{#if health.services.length > 8}
								<div class="text-[10px] text-muted">+{health.services.length - 8} more</div>
							{/if}
						</div>
					{/if}
				</div>

				<!-- ML Models -->
				<div class="border-b border-terminal-border p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">ML Models</div>
					<div class="space-y-1.5 text-sm">
						{#if $trading.mlEntry}
							<div class="flex justify-between">
								<span class="text-muted">Entry</span>
								<span class="text-profit">{($trading.mlEntry.accuracy_7d * 100).toFixed(0)}%</span>
							</div>
						{/if}
						{#if $trading.mlExit}
							<div class="flex justify-between">
								<span class="text-muted">Exit</span>
								<span class="text-profit">{($trading.mlExit.hit_rate_7d * 100).toFixed(0)}%</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Quick Stats -->
				<div class="p-3 mt-auto">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">Session</div>
					<div class="space-y-1 text-sm">
						{#if capital?.session}
							<div class="flex justify-between">
								<span class="text-muted">Market</span>
								<span class="text-info">{capital.session}</span>
							</div>
						{/if}
						{#if tradingConfig}
							<div class="flex justify-between">
								<span class="text-muted">Max Pos</span>
								<span>{tradingConfig.max_positions}</span>
							</div>
						{/if}
					</div>
				</div>
			</aside>
		</div>
	</div>

	<!-- ==================== SETTINGS MODAL ==================== -->
	{#if showSettingsModal}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onclick={() => showSettingsModal = false}>
			<div class="w-full max-w-2xl rounded-lg border border-terminal-border bg-terminal-panel shadow-2xl" onclick={(e) => e.stopPropagation()}>
				<!-- Modal Header -->
				<div class="flex items-center justify-between border-b border-terminal-border px-4 py-3">
					<h2 class="text-sm font-semibold">Settings</h2>
					<button onclick={() => showSettingsModal = false} class="text-muted hover:text-primary">
						<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
						</svg>
					</button>
				</div>

				<!-- Modal Tabs -->
				<div class="flex border-b border-terminal-border">
					{#each [
						{ id: 'limits', label: 'Position Limits' },
						{ id: 'budget', label: 'Budget' },
						{ id: 'margin', label: 'Margin Protection' },
						{ id: 'services', label: 'Services' }
					] as tab}
						<button
							onclick={() => settingsTab = tab.id as typeof settingsTab}
							class="px-4 py-2 text-xs font-medium border-b-2 transition-colors"
							class:border-info={settingsTab === tab.id}
							class:text-info={settingsTab === tab.id}
							class:border-transparent={settingsTab !== tab.id}
							class:text-muted={settingsTab !== tab.id}>
							{tab.label}
						</button>
					{/each}
				</div>

				<!-- Modal Content -->
				<div class="p-4 max-h-[60vh] overflow-y-auto">
					{#if settingsTab === 'limits'}
						<!-- Position Limits -->
						<div class="space-y-4">
							<div>
								<label class="block text-xs text-muted mb-1">Stock Max Position ($)</label>
								<div class="flex items-center gap-2">
									<input
										type="number"
										bind:value={tempStockMaxValue}
										min="100"
										max="50000"
										step="100"
										class="flex-1 rounded border border-terminal-border bg-terminal-card text-primary px-3 py-2 text-sm focus:border-info focus:outline-none"
									/>
									<span class="text-xs text-muted">Current: {formatCurrency(positionLimits?.stock?.max_position_value ?? 5000)}</span>
								</div>
							</div>
							<div>
								<label class="block text-xs text-muted mb-1">Forex Max Position ($)</label>
								<div class="flex items-center gap-2">
									<input
										type="number"
										bind:value={tempForexMaxValue}
										min="100"
										max="100000"
										step="100"
										class="flex-1 rounded border border-terminal-border bg-terminal-card text-primary px-3 py-2 text-sm focus:border-info focus:outline-none"
									/>
									<span class="text-xs text-muted">Current: {formatCurrency(positionLimits?.forex?.max_position_value ?? 5000)}</span>
								</div>
							</div>
							<div>
								<label class="block text-xs text-muted mb-1">Max Concurrent Positions</label>
								<div class="flex items-center gap-2">
									<input
										type="number"
										bind:value={tempMaxPositions}
										min="1"
										max="100"
										class="w-24 rounded border border-terminal-border bg-terminal-card text-primary px-3 py-2 text-sm focus:border-info focus:outline-none"
									/>
									<span class="text-xs text-muted">Current: {tradingConfig?.max_positions ?? 'N/A'}</span>
								</div>
							</div>
							<div class="flex gap-2">
								<button
									onclick={savePositionLimits}
									class="rounded bg-info px-4 py-2 text-xs font-medium text-white hover:opacity-90">
									Save Position Limits
								</button>
								<button
									onclick={saveMaxPositions}
									class="rounded bg-info px-4 py-2 text-xs font-medium text-white hover:opacity-90">
									Save Max Positions
								</button>
							</div>
						</div>

					{:else if settingsTab === 'budget'}
						<!-- Budget Allocation -->
						<div class="space-y-4">
							<div>
								<label class="block text-xs text-muted mb-1">Stock Budget: {tempStockBudgetPct}%</label>
								<input
									type="range"
									bind:value={tempStockBudgetPct}
									min="0"
									max="100"
									step="5"
									class="w-full h-2 bg-terminal-card rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div>
								<label class="block text-xs text-muted mb-1">Forex Budget: {tempForexBudgetPct}%</label>
								<input
									type="range"
									bind:value={tempForexBudgetPct}
									min="0"
									max="100"
									step="5"
									class="w-full h-2 bg-terminal-card rounded-lg appearance-none cursor-pointer"
								/>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm">Reserve: {100 - tempStockBudgetPct - tempForexBudgetPct}%</span>
								<label class="flex items-center gap-2">
									<span class="text-xs text-muted">Enforce Limits</span>
									<button
										onclick={() => tempEnforceBudgetLimits = !tempEnforceBudgetLimits}
										class="relative h-5 w-9 rounded-full transition-colors"
										class:bg-profit={tempEnforceBudgetLimits}
										class:bg-terminal-card={!tempEnforceBudgetLimits}>
										<span
											class="absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform"
											class:left-0.5={!tempEnforceBudgetLimits}
											class:left-4={tempEnforceBudgetLimits}></span>
									</button>
								</label>
							</div>
							<!-- Visual breakdown -->
							<div class="h-3 overflow-hidden rounded-full bg-terminal-card flex">
								<div class="bg-info" style="width: {tempStockBudgetPct}%"></div>
								<div class="bg-purple-500" style="width: {tempForexBudgetPct}%"></div>
								<div class="bg-profit" style="width: {100 - tempStockBudgetPct - tempForexBudgetPct}%"></div>
							</div>
							<div class="flex justify-between text-xs text-muted">
								<span>Stock {tempStockBudgetPct}%</span>
								<span>Forex {tempForexBudgetPct}%</span>
								<span>Reserve {100 - tempStockBudgetPct - tempForexBudgetPct}%</span>
							</div>
							{#if tempStockBudgetPct + tempForexBudgetPct > 100}
								<div class="text-xs text-loss">Total exceeds 100%!</div>
							{/if}
							<button
								onclick={saveBudgetAllocation}
								disabled={tempStockBudgetPct + tempForexBudgetPct > 100}
								class="rounded bg-info px-4 py-2 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50">
								Save Budget
							</button>
						</div>

					{:else if settingsTab === 'margin'}
						<!-- Margin Protection -->
						<div class="space-y-4">
							<div class="flex items-center justify-between">
								<span class="text-sm">Margin Protection</span>
								<button
									onclick={() => trading.toggleMarginProtection(!marginConfig?.enabled)}
									class="relative h-6 w-11 rounded-full transition-colors"
									class:bg-profit={marginConfig?.enabled}
									class:bg-terminal-card={!marginConfig?.enabled}>
									<span
										class="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform"
										class:left-0.5={!marginConfig?.enabled}
										class:left-5={marginConfig?.enabled}></span>
								</button>
							</div>

							<div>
								<label class="block text-xs text-muted mb-1">Min Cushion for Entry (%)</label>
								<div class="flex items-center gap-2">
									<input
										type="number"
										bind:value={tempMinCushion}
										min="1"
										max="50"
										class="w-20 rounded border border-terminal-border bg-terminal-card text-primary px-3 py-2 text-sm focus:border-info focus:outline-none"
									/>
									<button
										onclick={saveMinCushion}
										class="rounded bg-info px-3 py-2 text-xs font-medium text-white hover:opacity-90">
										Set
									</button>
								</div>
							</div>

							{#if marginConfig}
								<div class="text-xs text-muted space-y-1">
									<div>Target Cushion: {(marginConfig.target_cushion_pct * 100).toFixed(0)}%</div>
									<div>Check Start: {marginConfig.check_start_time}</div>
									<div>Aggressive Time: {marginConfig.aggressive_time}</div>
								</div>
							{/if}

							<!-- Weights -->
							<div class="border-t border-terminal-border pt-4">
								<div class="flex items-center justify-between mb-2">
									<span class="text-xs text-muted uppercase">Scoring Weights</span>
									{#if !editingWeights}
										<button onclick={() => editingWeights = true} class="text-xs text-info hover:underline">Edit</button>
									{:else}
										<div class="flex gap-2">
											<button onclick={saveWeights} class="text-xs text-profit hover:underline">Save</button>
											<button onclick={() => editingWeights = false} class="text-xs text-loss hover:underline">Cancel</button>
										</div>
									{/if}
								</div>
								{#if editingWeights}
									<div class="space-y-2">
										{#each [
											{ key: 'weight_ml_exit', label: 'ML Exit' },
											{ key: 'weight_pnl_negative', label: 'P&L Negative' },
											{ key: 'weight_time_held', label: 'Time Held' },
											{ key: 'weight_stop_proximity', label: 'Stop Proximity' },
											{ key: 'weight_volume_decay', label: 'Volume Decay' }
										] as weight}
											<div class="flex items-center justify-between">
												<span class="text-xs text-muted">{weight.label}</span>
												<div class="flex items-center gap-2">
													<input
														type="range"
														min="0"
														max="100"
														step="5"
														value={tempWeights[weight.key] * 100}
														oninput={(e) => tempWeights[weight.key] = parseInt(e.currentTarget.value) / 100}
														class="w-24 h-1 bg-terminal-card rounded-lg appearance-none cursor-pointer"
													/>
													<span class="text-xs w-8 text-right">{(tempWeights[weight.key] * 100).toFixed(0)}%</span>
												</div>
											</div>
										{/each}
										<div class="flex justify-between text-xs font-medium pt-2 border-t border-terminal-border">
											<span>Total</span>
											<span class:text-profit={Math.abs(getTotalWeight() - 1.0) < 0.01}
												  class:text-loss={Math.abs(getTotalWeight() - 1.0) >= 0.01}>
												{(getTotalWeight() * 100).toFixed(0)}%
											</span>
										</div>
									</div>
								{:else if marginConfig}
									<div class="grid grid-cols-2 gap-1 text-xs">
										<div class="flex justify-between"><span class="text-muted">ML Exit</span><span>{(marginConfig.weight_ml_exit * 100).toFixed(0)}%</span></div>
										<div class="flex justify-between"><span class="text-muted">P&L Neg</span><span>{(marginConfig.weight_pnl_negative * 100).toFixed(0)}%</span></div>
										<div class="flex justify-between"><span class="text-muted">Time</span><span>{(marginConfig.weight_time_held * 100).toFixed(0)}%</span></div>
										<div class="flex justify-between"><span class="text-muted">Stop</span><span>{(marginConfig.weight_stop_proximity * 100).toFixed(0)}%</span></div>
										<div class="flex justify-between"><span class="text-muted">Volume</span><span>{(marginConfig.weight_volume_decay * 100).toFixed(0)}%</span></div>
									</div>
								{/if}
							</div>
						</div>

					{:else if settingsTab === 'services'}
						<!-- Services Details -->
						<div class="space-y-2">
							{#each health.services as service}
								<div class="flex items-center justify-between p-2 rounded bg-terminal-card">
									<span class="text-sm">{service.name}</span>
									<span class="flex items-center gap-2">
										<span class="text-xs text-muted">{service.status}</span>
										<span class="h-2 w-2 rounded-full {getStatusColor(service.status)}"></span>
									</span>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
{/if}

<!-- Position Detail Modal -->
<PositionDetailModal position={selectedPosition} onClose={() => (selectedPosition = null)} />

<!-- V7.47.2: Chart Modal (kiosk-compatible - no navigation away) -->
{#if chartModal}
	<div
		class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
		onclick={() => chartModal = null}
		onkeydown={(e) => e.key === 'Escape' && (chartModal = null)}
		role="dialog"
		aria-modal="true"
		tabindex="-1"
	>
		<div
			class="bg-terminal-panel border border-terminal-border rounded-lg w-full max-w-6xl h-[80vh] flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="flex items-center justify-between px-4 py-3 border-b border-terminal-border">
				<div class="flex items-center gap-4">
					<h2 class="text-lg font-medium">{chartModal.symbol}</h2>
					<span class="text-xs px-2 py-1 rounded {chartModal.assetType === 'forex' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}">
						{chartModal.assetType}
					</span>
					<!-- Interval selector -->
					<div class="flex gap-1">
						{#each chartIntervals as interval}
							<button
								class="px-2 py-1 text-xs rounded {chartModal.interval === interval ? 'bg-info text-white' : 'bg-terminal-card hover:bg-terminal-hover'}"
								onclick={() => chartModal = { ...chartModal, interval }}
							>
								{interval === '1' ? '1m' : interval === '5' ? '5m' : interval === '15' ? '15m' : interval === '60' ? '1H' : interval === 'D' ? 'Day' : 'Week'}
							</button>
						{/each}
					</div>
				</div>
				<button
					onclick={() => chartModal = null}
					class="p-2 rounded hover:bg-terminal-hover text-xl"
				>
					✕
				</button>
			</div>
			<!-- Chart iframe -->
			<div class="flex-1 p-2">
				<iframe
					src={getChartUrl(chartModal.symbol, chartModal.assetType, chartModal.interval)}
					title="TradingView Chart"
					class="w-full h-full rounded border-0"
					allowfullscreen
				></iframe>
			</div>
		</div>
	</div>
{/if}

<style>
	/* Terminal Dark Theme Colors */
	:global(:root) {
		--terminal-base: #0a0e14;
		--terminal-panel: #0f1419;
		--terminal-card: #151b23;
		--terminal-hover: #1a2230;
		--terminal-border: #1e2530;

		--text-primary: #e6e8eb;
		--text-secondary: #8b9198;
		--text-tertiary: #5c6370;

		--color-profit: #00d26a;
		--color-loss: #ff3b30;
		--color-warning: #f5a623;
		--color-info: #0a84ff;
	}

	/* Utility Classes */
	.bg-terminal-base { background-color: var(--terminal-base); }
	.bg-terminal-panel { background-color: var(--terminal-panel); }
	.bg-terminal-card { background-color: var(--terminal-card); }
	.bg-terminal-hover { background-color: var(--terminal-hover); }
	.border-terminal-border { border-color: var(--terminal-border); }

	.text-primary { color: var(--text-primary); }
	.text-muted { color: var(--text-secondary); }

	.text-profit { color: var(--color-profit); }
	.text-loss { color: var(--color-loss); }
	.text-warning { color: var(--color-warning); }
	.text-info { color: var(--color-info); }

	.bg-profit { background-color: var(--color-profit); }
	.bg-loss { background-color: var(--color-loss); }
	.bg-warning { background-color: var(--color-warning); }
	.bg-info { background-color: var(--color-info); }

	.bg-profit-dim { background-color: rgba(0, 210, 106, 0.15); }
	.bg-loss-dim { background-color: rgba(255, 59, 48, 0.15); }
	.bg-warning-dim { background-color: rgba(245, 166, 35, 0.15); }
	.bg-info-dim { background-color: rgba(10, 132, 255, 0.15); }
	.bg-purple-dim { background-color: rgba(168, 85, 247, 0.2); }

	.tabular-nums { font-variant-numeric: tabular-nums; }

	/* Custom scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	::-webkit-scrollbar-track {
		background: var(--terminal-base);
	}
	::-webkit-scrollbar-thumb {
		background: var(--terminal-border);
		border-radius: 3px;
	}
	::-webkit-scrollbar-thumb:hover {
		background: var(--text-tertiary);
	}

	/* Range slider styling */
	input[type="range"] {
		-webkit-appearance: none;
		appearance: none;
		background: transparent;
	}
	input[type="range"]::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: var(--color-info);
		cursor: pointer;
		margin-top: -5px;
	}
	input[type="range"]::-webkit-slider-runnable-track {
		width: 100%;
		height: 4px;
		background: var(--terminal-card);
		border-radius: 2px;
	}
</style>
