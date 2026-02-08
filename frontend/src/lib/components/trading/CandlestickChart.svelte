<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	interface Props {
		symbol: string;
		assetType: 'stock' | 'forex';
		entryPrice?: number;
		entryTime?: number;
	}

	let { symbol, assetType, entryPrice, entryTime }: Props = $props();

	let containerElement: HTMLDivElement;
	let chart: any = null;
	let loading = $state(true);
	let error = $state<string | null>(null);

	interface Candle {
		time: number;
		open: number;
		high: number;
		low: number;
		close: number;
		volume?: number;
	}

	async function fetchChartData(): Promise<Candle[]> {
		// Clean symbol - remove slashes for forex pairs (AUD/JPY -> AUDJPY)
		const cleanSymbol = symbol.replace('/', '');
		const response = await fetch(
			`/api/v1/chart/history/${encodeURIComponent(cleanSymbol)}?asset_type=${assetType}&period=1mo&interval=1h`
		);

		if (!response.ok) {
			throw new Error(`Failed to fetch data: ${response.statusText}`);
		}

		const data = await response.json();
		return data.candles;
	}

	async function createChart() {
		if (!browser || !containerElement) return;

		loading = true;
		error = null;

		try {
			// Dynamically import lightweight-charts (v4+ API)
			const { createChart: createLWChart, ColorType, CrosshairMode, CandlestickSeries, HistogramSeries } = await import('lightweight-charts');

			const candles = await fetchChartData();

			if (candles.length === 0) {
				error = 'No data available';
				loading = false;
				return;
			}

			// Create chart
			chart = createLWChart(containerElement, {
				layout: {
					background: { type: ColorType.Solid, color: '#0f1419' },
					textColor: '#9ca3af',
				},
				grid: {
					vertLines: { color: '#1e2530' },
					horzLines: { color: '#1e2530' },
				},
				crosshair: {
					mode: CrosshairMode.Normal,
				},
				rightPriceScale: {
					borderColor: '#1e2530',
					scaleMargins: { top: 0.1, bottom: 0.2 },
				},
				timeScale: {
					borderColor: '#1e2530',
					timeVisible: true,
					secondsVisible: false,
				},
				width: containerElement.clientWidth,
				height: 300,
			});

			// Add candlestick series (v4 API)
			const candleSeries = chart.addSeries(CandlestickSeries, {
				upColor: '#22c55e',
				downColor: '#ef4444',
				borderUpColor: '#22c55e',
				borderDownColor: '#ef4444',
				wickUpColor: '#22c55e',
				wickDownColor: '#ef4444',
			});

			// Format data for lightweight-charts (time in seconds)
			const formattedCandles = candles.map((c) => ({
				time: Math.floor(c.time / 1000) as any, // Convert ms to seconds
				open: c.open,
				high: c.high,
				low: c.low,
				close: c.close,
			}));

			candleSeries.setData(formattedCandles);

			// Add entry price line if provided
			if (entryPrice) {
				candleSeries.createPriceLine({
					price: entryPrice,
					color: '#3b82f6',
					lineWidth: 2,
					lineStyle: 2, // Dashed
					axisLabelVisible: true,
					title: 'Entry',
				});
			}

			// Add volume if available (v4 API)
			if (candles[0]?.volume !== undefined) {
				const volumeSeries = chart.addSeries(HistogramSeries, {
					color: '#6b728080',
					priceFormat: { type: 'volume' },
					priceScaleId: '',
				});

				chart.priceScale('').applyOptions({
					scaleMargins: { top: 0.8, bottom: 0 },
				});

				const volumeData = candles.map((c) => ({
					time: Math.floor(c.time / 1000) as any,
					value: c.volume || 0,
					color: c.close >= c.open ? '#22c55e40' : '#ef444440',
				}));

				volumeSeries.setData(volumeData);
			}

			// Fit content
			chart.timeScale().fitContent();

			loading = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load chart';
			loading = false;
		}
	}

	function handleResize() {
		if (chart && containerElement) {
			chart.applyOptions({ width: containerElement.clientWidth });
		}
	}

	onMount(() => {
		if (browser) {
			createChart();
			window.addEventListener('resize', handleResize);
		}
	});

	onDestroy(() => {
		if (browser) {
			window.removeEventListener('resize', handleResize);
			if (chart) {
				chart.remove();
				chart = null;
			}
		}
	});
</script>

<div class="chart-wrapper">
	<div bind:this={containerElement} class="chart-container"></div>

	{#if loading}
		<div class="loading-overlay">
			<div class="spinner"></div>
			<span>Loading chart...</span>
		</div>
	{/if}

	{#if error}
		<div class="error-overlay">
			<span>{error}</span>
		</div>
	{/if}
</div>

<style>
	.chart-wrapper {
		position: relative;
		width: 100%;
		min-height: 300px;
	}

	.chart-container {
		width: 100%;
		height: 300px;
	}

	.loading-overlay,
	.error-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		background: rgba(15, 20, 25, 0.9);
		color: #9ca3af;
		font-size: 0.875rem;
	}

	.error-overlay {
		color: #ef4444;
	}

	.spinner {
		width: 24px;
		height: 24px;
		border: 2px solid #1e2530;
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
