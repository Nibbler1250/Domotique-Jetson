<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		symbol: string;
		assetType: 'stock' | 'forex';
	}

	let { symbol, assetType }: Props = $props();

	let containerElement: HTMLDivElement;

	// Convert symbol format for TradingView
	function getTradingViewSymbol(sym: string, type: 'stock' | 'forex'): string {
		if (type === 'forex') {
			// AUDJPY -> FX:AUDJPY or OANDA:AUDJPY
			const clean = sym.replace('/', '');
			return `OANDA:${clean}`;
		}
		// Stocks - use default exchange
		return sym;
	}

	onMount(() => {
		const tvSymbol = getTradingViewSymbol(symbol, assetType);

		// Create TradingView widget
		const script = document.createElement('script');
		script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
		script.type = 'text/javascript';
		script.async = true;
		script.innerHTML = JSON.stringify({
			autosize: true,
			symbol: tvSymbol,
			interval: '60', // 1 hour
			timezone: 'America/New_York',
			theme: 'dark',
			style: '1', // Candlestick
			locale: 'en',
			enable_publishing: false,
			hide_top_toolbar: false,
			hide_legend: false,
			save_image: false,
			calendar: false,
			support_host: 'https://www.tradingview.com',
			container_id: 'tradingview-widget'
		});

		containerElement.appendChild(script);
	});
</script>

<div class="tradingview-widget-container" bind:this={containerElement}>
	<div id="tradingview-widget" class="w-full h-full"></div>
</div>

<style>
	.tradingview-widget-container {
		width: 100%;
		height: 400px;
	}
</style>
