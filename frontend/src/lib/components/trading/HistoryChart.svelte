<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Chart, registerables, type ChartConfiguration } from 'chart.js';
	import type { DailyStats, MLMetrics } from '$lib/stores/trading';

	// Register Chart.js components
	Chart.register(...registerables);

	interface Props {
		dailyStats: DailyStats[];
		mlMetrics: MLMetrics[];
		chartType?: 'pnl' | 'winrate' | 'ml';
	}

	let { dailyStats = [], mlMetrics = [], chartType = 'pnl' }: Props = $props();

	let canvasElement: HTMLCanvasElement;
	let chartInstance: Chart | null = null;

	function getChartConfig(): ChartConfiguration {
		const labels = dailyStats.map((d) => {
			const date = new Date(d.date);
			return date.toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' });
		});

		if (chartType === 'pnl') {
			const pnlData = dailyStats.map((d) => d.realized_pnl);
			const colors = pnlData.map((v) => (v >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'));
			const borderColors = pnlData.map((v) => (v >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'));

			return {
				type: 'bar',
				data: {
					labels,
					datasets: [
						{
							label: 'P&L ($)',
							data: pnlData,
							backgroundColor: colors,
							borderColor: borderColors,
							borderWidth: 1
						}
					]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: { display: false },
						tooltip: {
							callbacks: {
								label: (ctx) => `P&L: $${ctx.parsed.y.toFixed(2)}`
							}
						}
					},
					scales: {
						y: {
							beginAtZero: true,
							grid: { color: 'rgba(255, 255, 255, 0.1)' },
							ticks: { color: '#9ca3af' }
						},
						x: {
							grid: { display: false },
							ticks: { color: '#9ca3af' }
						}
					}
				}
			};
		}

		if (chartType === 'winrate') {
			return {
				type: 'line',
				data: {
					labels,
					datasets: [
						{
							label: 'Win Rate (%)',
							data: dailyStats.map((d) => d.win_rate * 100),
							borderColor: 'rgb(59, 130, 246)',
							backgroundColor: 'rgba(59, 130, 246, 0.1)',
							fill: true,
							tension: 0.3,
							pointRadius: 4,
							pointBackgroundColor: 'rgb(59, 130, 246)'
						}
					]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: { display: false },
						tooltip: {
							callbacks: {
								label: (ctx) => `Win Rate: ${ctx.parsed.y.toFixed(1)}%`
							}
						}
					},
					scales: {
						y: {
							min: 0,
							max: 100,
							grid: { color: 'rgba(255, 255, 255, 0.1)' },
							ticks: {
								color: '#9ca3af',
								callback: (v) => `${v}%`
							}
						},
						x: {
							grid: { display: false },
							ticks: { color: '#9ca3af' }
						}
					}
				}
			};
		}

		// ML Accuracy Chart
		const mlLabels = mlMetrics.map((m) => {
			const date = new Date(m.date);
			return date.toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' });
		});

		return {
			type: 'line',
			data: {
				labels: mlLabels,
				datasets: [
					{
						label: 'Accuracy',
						data: mlMetrics.map((m) => m.accuracy * 100),
						borderColor: 'rgb(168, 85, 247)',
						backgroundColor: 'transparent',
						tension: 0.3,
						pointRadius: 4
					},
					{
						label: 'Precision',
						data: mlMetrics.map((m) => m.precision * 100),
						borderColor: 'rgb(34, 197, 94)',
						backgroundColor: 'transparent',
						tension: 0.3,
						pointRadius: 4
					},
					{
						label: 'Recall',
						data: mlMetrics.map((m) => m.recall * 100),
						borderColor: 'rgb(251, 191, 36)',
						backgroundColor: 'transparent',
						tension: 0.3,
						pointRadius: 4
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: true,
						position: 'bottom',
						labels: { color: '#9ca3af' }
					},
					tooltip: {
						callbacks: {
							label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%`
						}
					}
				},
				scales: {
					y: {
						min: 0,
						max: 100,
						grid: { color: 'rgba(255, 255, 255, 0.1)' },
						ticks: {
							color: '#9ca3af',
							callback: (v) => `${v}%`
						}
					},
					x: {
						grid: { display: false },
						ticks: { color: '#9ca3af' }
					}
				}
			}
		};
	}

	function createChart() {
		if (!canvasElement) return;

		// Destroy existing chart
		if (chartInstance) {
			chartInstance.destroy();
			chartInstance = null;
		}

		const hasData =
			(chartType === 'ml' && mlMetrics.length > 0) ||
			(chartType !== 'ml' && dailyStats.length > 0);

		if (!hasData) return;

		chartInstance = new Chart(canvasElement, getChartConfig());
	}

	$effect(() => {
		// React to data changes
		if (dailyStats || mlMetrics || chartType) {
			createChart();
		}
	});

	onMount(() => {
		createChart();
	});

	onDestroy(() => {
		if (chartInstance) {
			chartInstance.destroy();
		}
	});
</script>

<div class="chart-container">
	<canvas bind:this={canvasElement}></canvas>
	{#if (chartType === 'ml' && mlMetrics.length === 0) || (chartType !== 'ml' && dailyStats.length === 0)}
		<div class="no-data">
			<span>No data available</span>
		</div>
	{/if}
</div>

<style>
	.chart-container {
		position: relative;
		width: 100%;
		height: 200px;
	}

	canvas {
		width: 100% !important;
		height: 100% !important;
	}

	.no-data {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		color: #6b7280;
		font-size: 0.875rem;
	}
</style>
