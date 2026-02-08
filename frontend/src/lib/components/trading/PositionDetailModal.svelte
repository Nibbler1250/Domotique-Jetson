<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Position } from '$lib/stores/trading';
	import CandlestickChart from './CandlestickChart.svelte';

	interface Props {
		position: Position | null;
		onClose: () => void;
	}

	let { position, onClose }: Props = $props();

	function formatCurrency(value: number): string {
		return value >= 0 ? `+$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`;
	}

	function formatPercent(value: number): string {
		return value >= 0 ? `+${value.toFixed(2)}%` : `${value.toFixed(2)}%`;
	}

	function formatHeldTime(entryTime: number): string {
		const now = Date.now();
		const diffMs = now - entryTime;
		const hours = Math.floor(diffMs / (1000 * 60 * 60));
		const days = Math.floor(hours / 24);

		if (days > 0) return `${days}d ${hours % 24}h`;
		if (hours > 0) return `${hours}h`;
		const minutes = Math.floor(diffMs / (1000 * 60));
		return `${minutes}m`;
	}

	function getPnlColorClass(value: number): string {
		return value >= 0 ? 'text-profit' : 'text-loss';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onClose();
		}
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	onMount(() => {
		if (typeof document !== 'undefined') {
			document.addEventListener('keydown', handleKeydown);
		}
	});

	onDestroy(() => {
		if (typeof document !== 'undefined') {
			document.removeEventListener('keydown', handleKeydown);
		}
	});
</script>

{#if position}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
		onclick={handleBackdropClick}
	>
		<div class="relative w-full max-w-2xl mx-4 bg-terminal-panel border border-terminal-border rounded-lg shadow-2xl max-h-[90vh] overflow-y-auto">
			<!-- Header -->
			<div class="sticky top-0 flex items-center justify-between border-b border-terminal-border px-4 py-3 bg-terminal-panel z-10">
				<div class="flex items-center gap-3">
					<h2 class="text-lg font-bold">{position.symbol}</h2>
					<span
						class="rounded px-2 py-0.5 text-xs font-medium"
						class:bg-info-dim={position.asset_type === 'stock'}
						class:text-info={position.asset_type === 'stock'}
						class:bg-purple-dim={position.asset_type === 'forex'}
						class:text-purple-400={position.asset_type === 'forex'}
					>
						{position.asset_type.toUpperCase()}
					</span>
				</div>
				<button
					onclick={onClose}
					class="p-1 hover:bg-terminal-hover rounded transition-colors text-muted hover:text-foreground"
					aria-label="Close"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-4 space-y-4">
				<!-- P&L Summary -->
				<div class="flex items-center justify-center gap-6 py-3 bg-terminal-card rounded-lg">
					<div class="text-center">
						<div class="text-xs text-muted uppercase tracking-wide">P&L</div>
						<div class="text-2xl font-bold tabular-nums {getPnlColorClass(position.unrealized_pnl)}">
							{formatCurrency(position.unrealized_pnl)}
						</div>
					</div>
					<div class="h-10 w-px bg-terminal-border"></div>
					<div class="text-center">
						<div class="text-xs text-muted uppercase tracking-wide">Return</div>
						<div class="text-2xl font-bold tabular-nums {getPnlColorClass(position.pnl_percent)}">
							{formatPercent(position.pnl_percent)}
						</div>
					</div>
				</div>

				<!-- Candlestick Chart -->
				<div class="bg-terminal-card rounded-lg p-3">
					<div class="text-xs text-muted uppercase tracking-wide mb-2">Price History (1 Month)</div>
					<CandlestickChart
						symbol={position.symbol}
						assetType={position.asset_type}
						entryPrice={position.entry_price}
						entryTime={position.entry_time}
					/>
				</div>

				<!-- Details Grid -->
				<div class="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide">Quantity</div>
						<div class="font-medium tabular-nums mt-1">
							{position.asset_type === 'forex' ? `$${position.quantity.toFixed(0)}` : position.quantity}
						</div>
					</div>
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide">Position Value</div>
						<div class="font-medium tabular-nums mt-1">
							${(position.current_price * position.quantity).toFixed(2)}
						</div>
					</div>
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide">Time Held</div>
						<div class="font-medium mt-1">{formatHeldTime(position.entry_time)}</div>
					</div>
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide">Entry Price</div>
						<div class="font-medium tabular-nums mt-1 text-muted">
							${position.entry_price.toFixed(position.asset_type === 'forex' ? 5 : 2)}
						</div>
					</div>
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide">Current Price</div>
						<div class="font-medium tabular-nums mt-1">
							${position.current_price.toFixed(position.asset_type === 'forex' ? 5 : 2)}
						</div>
					</div>
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide">ML Score</div>
						<div class="flex items-center gap-2 mt-1">
							<span
								class="rounded px-1.5 py-0.5 text-xs font-medium"
								class:bg-profit-dim={(position.ml_score || 0) > 0.7}
								class:text-profit={(position.ml_score || 0) > 0.7}
								class:bg-warning-dim={(position.ml_score || 0) > 0.5 && (position.ml_score || 0) <= 0.7}
								class:text-warning={(position.ml_score || 0) > 0.5 && (position.ml_score || 0) <= 0.7}
								class:bg-terminal-card={(position.ml_score || 0) <= 0.5}
								class:text-muted={(position.ml_score || 0) <= 0.5}
							>
								{((position.ml_score || 0) * 100).toFixed(0)}%
							</span>
						</div>
					</div>
				</div>

				<!-- Score Bar -->
				{#if position.score > 0}
					<div class="bg-terminal-card rounded-lg p-3">
						<div class="text-xs text-muted uppercase tracking-wide mb-2">Entry Score</div>
						<div class="flex items-center gap-3">
							<div class="flex-1 h-2 bg-terminal-border rounded-full overflow-hidden">
								<div
									class="h-full rounded-full transition-all"
									class:bg-profit={position.score > 0.7}
									class:bg-warning={position.score > 0.5 && position.score <= 0.7}
									class:bg-info={position.score <= 0.5}
									style="width: {position.score * 100}%"
								></div>
							</div>
							<span class="text-sm font-medium tabular-nums">{(position.score * 100).toFixed(0)}%</span>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.text-profit {
		color: rgb(34, 197, 94);
	}
	.text-loss {
		color: rgb(239, 68, 68);
	}
	.text-warning {
		color: rgb(251, 191, 36);
	}
	.text-info {
		color: rgb(59, 130, 246);
	}
	.bg-profit-dim {
		background-color: rgba(34, 197, 94, 0.15);
	}
	.bg-warning-dim {
		background-color: rgba(251, 191, 36, 0.15);
	}
	.bg-info-dim {
		background-color: rgba(59, 130, 246, 0.15);
	}
	.bg-purple-dim {
		background-color: rgba(168, 85, 247, 0.15);
	}
</style>
