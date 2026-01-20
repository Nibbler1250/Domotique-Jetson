/**
 * Trading store for Momentum Trader V7 integration
 * Connects to MQTT via WebSocket bridge for real-time trading data
 *
 * Access restricted to: admin, simon (family_adult with username 'simon')
 */

import { writable, derived } from 'svelte/store';

// ==================== TYPES ====================

export interface ServiceStatus {
	// V7.2: Accept both uppercase (legacy) and lowercase (MQTT) status values
	// V7.5: Added RUNNING, PAUSED, STOPPED for engine status
	status: 'HEALTHY' | 'DEGRADED' | 'DOWN' | 'UNKNOWN' | 'RUNNING' | 'PAUSED' | 'STOPPED' | 'ok' | 'warning' | 'error' | 'unknown';
	timestamp?: string;
}

export interface ServicesHeartbeat extends ServiceStatus {
	uptime_seconds: number;
	services_ok: number;
	services_degraded: number;
	services_down: number;
	memory_mb: number;
	cpu_percent: number;
}

export interface MLEntryStatus extends ServiceStatus {
	model_loaded: boolean;
	predictions_1h: number;
	avg_latency_ms: number;
	accuracy_7d: number;
	last_prediction: string;
	cache_hit_rate: number;
}

export interface MLExitStatus extends ServiceStatus {
	model_loaded: boolean;
	decisions_1h: number;
	avg_latency_ms: number;
	hit_rate_7d: number;
	last_decision: string;
}

export interface OnlineLearningStatus extends ServiceStatus {
	last_train: string;
	samples_total: number;
	samples_today: number;
	model_version: string;
	next_train_in_minutes: number;
}

export interface DNAStatus extends ServiceStatus {
	records_total: number;
	records_today: number;
	last_write: string;
	db_size_mb: number;
	pending_closes: number;
}

export interface T5008Status extends ServiceStatus {
	transactions_ytd: number;
	transactions_today: number;
	last_record: string;
	total_gains_ytd: number;
	total_losses_ytd: number;
}

export interface ScannerStockStatus extends ServiceStatus {
	last_scan: string;
	symbols_scanned: number;
	candidates_found: number;
	scan_duration_ms: number;
	next_scan_seconds: number;
}

export interface ScannerForexStatus extends ServiceStatus {
	last_scan: string;
	pairs_active: number;
	signals_pending: number;
	session: string;
	regime: string;
}

export interface EngineStatus extends ServiceStatus {
	mode: 'PAPER' | 'LIVE';
	orders_pending: number;
	orders_today: number;
	health_score: number;
}

export interface IBKRStatus extends ServiceStatus {
	latency_ms: number;
	last_heartbeat: string;
	client_ids_active: number[];
	account: string;
	data_farm: string;
}

export interface BreakersStatus extends ServiceStatus {
	open_count: number;
	states: Record<string, string>;
	last_trip: string | null;
	trips_24h: number;
}

export interface Position {
	symbol: string;
	quantity: number;
	entry_price: number;
	current_price: number;
	unrealized_pnl: number;
	pnl_percent: number;
	asset_type: 'stock' | 'forex';
	entry_time: number;
	score: number;
}

export interface ClosedTrade {
	symbol: string;
	pnl: number;
	pnl_pct: number;
	exit_reason: string;
	exit_time: string;
	duration_min: number;
}

export interface PortfolioSummary {
	equity: number;
	initial_capital: number;
	pnl_total: number;
	pnl_pct: number;
	pnl_realized: number;
	pnl_unrealized: number;
	positions_open: number;
	positions_stock: number;
	positions_forex: number;
	win_rate_today: number;
	trades_today: number;
	max_drawdown_today: number;
	timestamp?: string;
}

export interface ScannerPipeline {
	stock: {
		scanned: number;
		passed_volume: number;
		passed_pattern: number;
		passed_ml: number;
		entered: number;
		rejected: number;
	};
	forex: {
		pairs_monitored: number;
		signals_detected: number;
		passed_ml: number;
		entered: number;
		rejected: number;
	};
	funnel_efficiency: number;
	timestamp?: string;
}

export interface ScannerCandidate {
	symbol: string;
	ml_score: number;
	pattern: string;
	volume_ratio?: number;
	pip_potential?: number;
	price?: number;
	reason_skip: string | null;
}

export interface ErrorsSummary {
	errors_1h: number;
	errors_24h: number;
	warnings_1h: number;
	warnings_24h: number;
	by_category: Record<string, number>;
	last_critical: string | null;
	last_critical_msg: string | null;
	timestamp?: string;
}

// V7.4: Account & Capital Management Types
export interface AccountSummary {
	net_liquidation: number;
	available_funds: number;
	buying_power: number;
	margin_used: number;
	maintenance_margin: number;
	excess_liquidity: number;
	cushion: number;
	sma: number;
	margin_pct_used: number;
	timestamp?: string;
}

export interface CurrencyBalance {
	cash: number;
	settled_cash: number;
	accrued_interest: number;
}

export interface AccountCurrencies {
	currencies: Record<string, CurrencyBalance>;
	base_currency: string;
	timestamp?: string;
}

export interface CapitalAllocation {
	stock_budget: number;
	stock_used: number;
	stock_available: number;
	forex_budget: number;
	forex_used: number;
	forex_available: number;
	reserve: number;
	session: string;
	stock_enabled: boolean;
	forex_enabled: boolean;
	timestamp?: string;
}

export interface MarketControlStatus {
	stock_enabled: boolean;
	forex_enabled: boolean;
	stock_reason: string;
	forex_reason: string;
	timestamp?: string;
}

// V7.5: Margin Protection Types
export interface MarginProtectionConfig {
	enabled: boolean;
	target_cushion_pct: number;
	min_cushion_pct: number;
	check_start_time: string;
	aggressive_time: string;
	weight_ml_exit: number;
	weight_pnl_negative: number;
	weight_time_held: number;
	weight_stop_proximity: number;
	weight_volume_decay: number;
	immediate_sell_score: number;
	candidate_sell_score: number;
	max_positions_to_sell: number;
	min_position_value: number;
	excluded_symbols: string[];
}

export interface PositionSellScore {
	symbol: string;
	score: number;
	action: 'SELL_IMMEDIATE' | 'SELL_CANDIDATE' | 'HOLD';
	pnl_pct: number;
	pnl_dollars: number;
	days_held: number;
	ml_action: string;
	ml_confidence: number;
	position_value: number;
}

export interface MarginProtectionScores {
	timestamp: string;
	enabled: boolean;
	positions: PositionSellScore[];
}

export interface TradingConfig {
	max_positions: number;
	timestamp?: string;
}

// ==================== STORE STATE ====================

export interface TradingState {
	connected: boolean;
	lastUpdate: string | null;
	error: string | null;

	// Services
	heartbeat: ServicesHeartbeat | null;
	mlEntry: MLEntryStatus | null;
	mlExit: MLExitStatus | null;
	onlineLearning: OnlineLearningStatus | null;
	dna: DNAStatus | null;
	t5008: T5008Status | null;
	scannerStock: ScannerStockStatus | null;
	scannerForex: ScannerForexStatus | null;
	engine: EngineStatus | null;
	ibkr: IBKRStatus | null;
	breakers: BreakersStatus | null;

	// Portfolio
	positions: Position[];
	closedToday: ClosedTrade[];
	summary: PortfolioSummary | null;

	// Scanner
	pipeline: ScannerPipeline | null;
	recommendations: ScannerCandidate[];

	// Errors
	errors: ErrorsSummary | null;

	// V7.4: Account & Capital
	account: AccountSummary | null;
	currencies: AccountCurrencies | null;
	capital: CapitalAllocation | null;
	marketControl: MarketControlStatus | null;

	// V7.5: Margin Protection
	marginProtectionConfig: MarginProtectionConfig | null;
	marginProtectionScores: MarginProtectionScores | null;
	tradingConfig: TradingConfig | null;
}

const initialState: TradingState = {
	connected: false,
	lastUpdate: null,
	error: null,
	heartbeat: null,
	mlEntry: null,
	mlExit: null,
	onlineLearning: null,
	dna: null,
	t5008: null,
	scannerStock: null,
	scannerForex: null,
	engine: null,
	ibkr: null,
	breakers: null,
	positions: [],
	closedToday: [],
	summary: null,
	pipeline: null,
	recommendations: [],
	errors: null,
	// V7.4: Account & Capital
	account: null,
	currencies: null,
	capital: null,
	marketControl: null,

	// V7.5: Margin Protection
	marginProtectionConfig: null,
	marginProtectionScores: null,
	tradingConfig: null
};

// ==================== STALE DATA DETECTION ====================

// How long before data is considered stale (trader heartbeat is every 60s)
const STALE_THRESHOLD_MS = 75_000; // 75 seconds = 60s heartbeat + 15s margin

// Check if lastUpdate timestamp is stale
function isDataStale(lastUpdate: string | null): boolean {
	if (!lastUpdate) return true;
	const lastTime = new Date(lastUpdate).getTime();
	const now = Date.now();
	return (now - lastTime) > STALE_THRESHOLD_MS;
}

// ==================== MQTT TOPICS MAPPING ====================

const TOPIC_HANDLERS: Record<string, (state: TradingState, payload: unknown) => Partial<TradingState>> = {
	'trader/services/heartbeat': (state, payload) => ({ heartbeat: payload as ServicesHeartbeat }),
	'trader/services/ml_entry': (state, payload) => ({ mlEntry: payload as MLEntryStatus }),
	'trader/services/ml_exit': (state, payload) => ({ mlExit: payload as MLExitStatus }),
	'trader/services/online_learning': (state, payload) => ({ onlineLearning: payload as OnlineLearningStatus }),
	'trader/services/dna': (state, payload) => ({ dna: payload as DNAStatus }),
	'trader/services/t5008': (state, payload) => ({ t5008: payload as T5008Status }),
	'trader/services/scanner_stock': (state, payload) => ({ scannerStock: payload as ScannerStockStatus }),
	'trader/services/scanner_forex': (state, payload) => ({ scannerForex: payload as ScannerForexStatus }),
	'trader/services/engine': (state, payload) => ({ engine: payload as EngineStatus }),
	'trader/services/ibkr': (state, payload) => ({ ibkr: payload as IBKRStatus }),
	'trader/services/breakers': (state, payload) => ({ breakers: payload as BreakersStatus }),
	'trader/portfolio/positions': (state, payload) => {
		const data = payload as { positions: Position[] };
		return { positions: data.positions || [] };
	},
	'trader/portfolio/closed_today': (state, payload) => {
		const data = payload as { trades: ClosedTrade[] };
		return { closedToday: data.trades || [] };
	},
	'trader/portfolio/summary': (state, payload) => ({ summary: payload as PortfolioSummary }),
	'trader/scanner/pipeline': (state, payload) => ({ pipeline: payload as ScannerPipeline }),
	'trader/scanner/recommendations': (state, payload) => {
		const data = payload as { candidates: ScannerCandidate[] };
		return { recommendations: data.candidates || [] };
	},
	'trader/errors/summary': (state, payload) => ({ errors: payload as ErrorsSummary }),
	// V7.4: Account & Capital topics (with payload transformation)
	'trader/account/summary': (state, payload) => ({ account: payload as AccountSummary }),
	'trader/account/currencies': (state, payload) => {
		// Transform currencies format: backend uses "currencies" key with nested objects
		const data = payload as { currencies?: Record<string, { cash: number; settled?: number; settled_cash?: number; accrued_interest?: number }>, base_currency?: string, primary_currency?: string };
		const transformed: AccountCurrencies = {
			currencies: {},
			base_currency: data.base_currency || data.primary_currency || 'USD'
		};
		if (data.currencies) {
			for (const [currency, balance] of Object.entries(data.currencies)) {
				transformed.currencies[currency] = {
					cash: balance.cash || 0,
					settled_cash: balance.settled_cash || balance.settled || 0,
					accrued_interest: balance.accrued_interest || 0
				};
			}
		}
		return { currencies: transformed };
	},
	'trader/capital/allocation': (state, payload) => {
		// Transform nested format to flat format expected by frontend
		const data = payload as {
			stock?: { budget: number; used: number; available: number; enabled: boolean };
			forex?: { budget: number; used: number; available: number; enabled: boolean };
			reserve?: number;
			session?: string;
		};
		const transformed: CapitalAllocation = {
			stock_budget: data.stock?.budget || 0,
			stock_used: data.stock?.used || 0,
			stock_available: data.stock?.available || 0,
			forex_budget: data.forex?.budget || 0,
			forex_used: data.forex?.used || 0,
			forex_available: data.forex?.available || 0,
			reserve: data.reserve || 0,
			session: data.session || 'UNKNOWN',
			stock_enabled: data.stock?.enabled ?? true,
			forex_enabled: data.forex?.enabled ?? true
		};
		return { capital: transformed };
	},
	'trader/control/status': (state, payload) => {
		// Transform nested format to flat format expected by frontend
		const data = payload as {
			stock?: { enabled: boolean; reason?: string };
			forex?: { enabled: boolean; reason?: string };
			stock_enabled?: boolean;
			forex_enabled?: boolean;
			stock_reason?: string;
			forex_reason?: string;
		};
		const transformed: MarketControlStatus = {
			stock_enabled: data.stock?.enabled ?? data.stock_enabled ?? true,
			forex_enabled: data.forex?.enabled ?? data.forex_enabled ?? true,
			stock_reason: data.stock?.reason || data.stock_reason || '',
			forex_reason: data.forex?.reason || data.forex_reason || ''
		};
		return { marketControl: transformed };
	},
	// V7.5: Margin Protection topics
	'trader/margin_protection/config': (state, payload) => ({
		marginProtectionConfig: payload as MarginProtectionConfig
	}),
	'trader/margin_protection/scores': (state, payload) => ({
		marginProtectionScores: payload as MarginProtectionScores
	}),
	'trader/config/trading': (state, payload) => ({
		tradingConfig: payload as TradingConfig
	})
};

// ==================== STORE ====================

function createTradingStore() {
	const { subscribe, set, update } = writable<TradingState>(initialState);

	let ws: WebSocket | null = null;
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	let staleCheckTimer: ReturnType<typeof setInterval> | null = null;

	// WebSocket URL for MQTT bridge (via backend)
	// Use dynamic host detection for network access from any device
	function getWsUrl(): string {
		if (typeof window !== 'undefined') {
			const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
			const host = window.location.hostname;
			return `${protocol}//${host}:8000/api/v1/trading/ws`;
		}
		return import.meta.env.VITE_TRADING_WS_URL || 'ws://localhost:8000/api/v1/trading/ws';
	}
	const WS_URL = getWsUrl();

	// Start periodic stale check (every 30 seconds)
	function startStaleCheck() {
		if (staleCheckTimer) return;
		staleCheckTimer = setInterval(() => {
			update(state => {
				if (state.lastUpdate && isDataStale(state.lastUpdate)) {
					console.log('[Trading] Data is stale, marking trader as OFFLINE');
					// Mark engine as STOPPED when data is stale
					return {
						...state,
						engine: state.engine ? { ...state.engine, status: 'DOWN' as const } : null,
						error: 'Trader offline - no heartbeat received'
					};
				}
				return state;
			});
		}, 30_000); // Check every 30 seconds
	}

	function stopStaleCheck() {
		if (staleCheckTimer) {
			clearInterval(staleCheckTimer);
			staleCheckTimer = null;
		}
	}

	function connect() {
		if (ws?.readyState === WebSocket.OPEN) return;

		update(state => ({ ...state, error: null }));

		try {
			ws = new WebSocket(WS_URL);

			ws.onopen = () => {
				update(state => ({ ...state, connected: true, error: null }));
				console.log('Trading WebSocket connected');

				// Start stale data detection
				startStaleCheck();

				// Subscribe to all trader topics
				ws?.send(JSON.stringify({
					type: 'subscribe',
					topics: ['trader/#']
				}));
			};

			ws.onmessage = (event) => {
				try {
					const message = JSON.parse(event.data);
					handleMessage(message);
				} catch (e) {
					console.error('Failed to parse trading message:', e);
				}
			};

			ws.onerror = (error) => {
				console.error('Trading WebSocket error:', error);
				update(state => ({ ...state, error: 'Connection error' }));
			};

			ws.onclose = () => {
				update(state => ({ ...state, connected: false }));
				console.log('Trading WebSocket closed');

				// Reconnect after delay
				if (!reconnectTimer) {
					reconnectTimer = setTimeout(() => {
						reconnectTimer = null;
						connect();
					}, 5000);
				}
			};
		} catch (e) {
			console.error('Failed to create Trading WebSocket:', e);
			update(state => ({ ...state, error: 'Failed to connect' }));
		}
	}

	function handleMessage(message: { type: string; topic?: string; payload?: unknown }) {
		console.log('[Trading] Message received:', message.type, message.topic);
		if (message.type === 'mqtt' && message.topic && message.payload) {
			const handler = TOPIC_HANDLERS[message.topic];
			if (handler) {
				console.log('[Trading] Handler found for:', message.topic);
				update(state => {
					const updates = handler(state, message.payload);
					console.log('[Trading] State updated:', Object.keys(updates));

					// V7.5: Use timestamp from payload if available (critical for stale detection)
					// MQTT retained messages have old timestamps - don't use current time!
					const payload = message.payload as Record<string, unknown>;
					const payloadTimestamp = payload?.timestamp as string | undefined;
					const messageTime = payloadTimestamp || new Date().toISOString();

					return {
						...state,
						...updates,
						lastUpdate: messageTime
					};
				});
			} else {
				console.log('[Trading] No handler for topic:', message.topic);
			}
		}
	}

	function disconnect() {
		stopStaleCheck();
		if (reconnectTimer) {
			clearTimeout(reconnectTimer);
			reconnectTimer = null;
		}
		if (ws) {
			ws.close();
			ws = null;
		}
		set(initialState);
	}

	// V7.4: Send control commands via WebSocket
	function sendCommand(topic: string, payload: Record<string, unknown>) {
		if (ws?.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify({
				type: 'publish',
				topic,
				payload
			}));
			return true;
		}
		console.error('WebSocket not connected, cannot send command');
		return false;
	}

	function toggleStockTrading(enabled: boolean, reason?: string) {
		return sendCommand('trader/control/stock/toggle', {
			enabled,
			reason: reason || (enabled ? 'Manual enable via dashboard' : 'Manual disable via dashboard'),
			source: 'dashboard'
		});
	}

	function toggleForexTrading(enabled: boolean, reason?: string) {
		return sendCommand('trader/control/forex/toggle', {
			enabled,
			reason: reason || (enabled ? 'Manual enable via dashboard' : 'Manual disable via dashboard'),
			source: 'dashboard'
		});
	}

	function closePosition(symbol: string, reason?: string) {
		return sendCommand('trader/control/position/close', {
			symbol,
			reason: reason || 'Manual close via dashboard',
			source: 'dashboard'
		});
	}

	function closeAllPositions(assetType?: 'stock' | 'forex', reason?: string) {
		return sendCommand('trader/control/positions/close_all', {
			asset_type: assetType || 'all',
			reason: reason || 'Manual close all via dashboard',
			source: 'dashboard'
		});
	}

	// V7.5: Margin Protection controls
	function toggleMarginProtection(enabled: boolean) {
		return sendCommand('trader/control/margin_protection/toggle', {
			enabled,
			source: 'dashboard'
		});
	}

	function updateMarginProtectionConfig(config: Partial<MarginProtectionConfig>) {
		return sendCommand('trader/control/margin_protection/config', {
			...config,
			source: 'dashboard'
		});
	}

	function updateMaxPositions(maxPositions: number) {
		return sendCommand('trader/control/config/max_positions', {
			max_positions: maxPositions,
			source: 'dashboard'
		});
	}

	return {
		subscribe,
		connect,
		disconnect,
		reset: () => set(initialState),
		// V7.4: Control methods
		toggleStockTrading,
		toggleForexTrading,
		closePosition,
		closeAllPositions,
		// V7.5: Margin Protection methods
		toggleMarginProtection,
		updateMarginProtectionConfig,
		updateMaxPositions
	};
}

export const trading = createTradingStore();

// ==================== DERIVED STORES ====================

export const servicesHealth = derived(trading, ($trading) => {
	const services = [
		{ name: 'ML Entry', status: $trading.mlEntry?.status },
		{ name: 'ML Exit', status: $trading.mlExit?.status },
		{ name: 'Online Learning', status: $trading.onlineLearning?.status },
		{ name: 'Position DNA', status: $trading.dna?.status },
		{ name: 'T5008 Tax', status: $trading.t5008?.status },
		{ name: 'Stock Scanner', status: $trading.scannerStock?.status },
		{ name: 'Forex Scanner', status: $trading.scannerForex?.status },
		{ name: 'Trading Engine', status: $trading.engine?.status },
		{ name: 'IBKR', status: $trading.ibkr?.status },
		{ name: 'Circuit Breakers', status: $trading.breakers?.status }
	];

	// V7.2 FIX: MQTT sends lowercase status values ("ok", "warning", "error")
	// Map them to expected states
	const isHealthy = (status: string | undefined) => status === 'ok' || status === 'HEALTHY' || status === 'RUNNING';
	const isDegraded = (status: string | undefined) => status === 'warning' || status === 'DEGRADED';
	const isDown = (status: string | undefined) => status === 'error' || status === 'DOWN';

	const healthy = services.filter(s => isHealthy(s.status)).length;
	const degraded = services.filter(s => isDegraded(s.status)).length;
	const down = services.filter(s => isDown(s.status)).length;
	const unknown = services.filter(s => !s.status || s.status === 'UNKNOWN' || s.status === 'unknown').length;

	return { services, healthy, degraded, down, unknown, total: services.length };
});

export const portfolioMetrics = derived(trading, ($trading) => {
	if (!$trading.summary) return null;

	return {
		equity: $trading.summary.equity,
		pnlTotal: $trading.summary.pnl_total,
		pnlPct: $trading.summary.pnl_pct,
		winRate: $trading.summary.win_rate_today,
		positionsOpen: $trading.summary.positions_open,
		tradesToday: $trading.summary.trades_today,
		maxDrawdown: $trading.summary.max_drawdown_today
	};
});

export const topPositions = derived(trading, ($trading) => {
	return [...$trading.positions]
		.sort((a, b) => Math.abs(b.unrealized_pnl) - Math.abs(a.unrealized_pnl))
		.slice(0, 5);
});

export const hasErrors = derived(trading, ($trading) => {
	return ($trading.errors?.errors_1h ?? 0) > 0;
});

// ==================== TRADER STATUS (with stale detection) ====================

export type TraderStatusValue = 'RUNNING' | 'PAUSED' | 'STOPPED' | 'OFFLINE' | 'UNKNOWN';

export interface TraderStatusInfo {
	status: TraderStatusValue;
	mode: 'PAPER' | 'LIVE' | null;
	lastUpdate: string | null;
	isStale: boolean;
	uptimeSeconds: number | null;
	reason: string;
}

/**
 * Derived store that provides accurate trader status with stale data detection.
 * - RUNNING: Trader is active and sending heartbeats
 * - PAUSED: Trader is connected but IBKR disconnected
 * - STOPPED: Trader engine explicitly stopped
 * - OFFLINE: No heartbeat received for 90+ seconds (stale data)
 * - UNKNOWN: No data available
 */
export const traderStatus = derived(trading, ($trading): TraderStatusInfo => {
	const stale = isDataStale($trading.lastUpdate);

	// No data at all
	if (!$trading.engine && !$trading.heartbeat) {
		return {
			status: 'UNKNOWN',
			mode: null,
			lastUpdate: $trading.lastUpdate,
			isStale: true,
			uptimeSeconds: null,
			reason: 'No data received from trader'
		};
	}

	// Data is stale (no heartbeat for 90+ seconds)
	if (stale) {
		return {
			status: 'OFFLINE',
			mode: $trading.engine?.mode || null,
			lastUpdate: $trading.lastUpdate,
			isStale: true,
			uptimeSeconds: $trading.heartbeat?.uptime_seconds || null,
			reason: 'No heartbeat received - trader may be stopped'
		};
	}

	// Engine status available and fresh
	const engineStatus = $trading.engine?.status;
	if (engineStatus === 'RUNNING' || engineStatus === 'ok') {
		return {
			status: 'RUNNING',
			mode: $trading.engine?.mode || 'PAPER',
			lastUpdate: $trading.lastUpdate,
			isStale: false,
			uptimeSeconds: $trading.heartbeat?.uptime_seconds || null,
			reason: 'Trader is active'
		};
	}

	if (engineStatus === 'PAUSED' || engineStatus === 'warning') {
		return {
			status: 'PAUSED',
			mode: $trading.engine?.mode || 'PAPER',
			lastUpdate: $trading.lastUpdate,
			isStale: false,
			uptimeSeconds: $trading.heartbeat?.uptime_seconds || null,
			reason: 'Trader paused - IBKR may be disconnected'
		};
	}

	if (engineStatus === 'DOWN' || engineStatus === 'error' || engineStatus === 'STOPPED') {
		return {
			status: 'STOPPED',
			mode: $trading.engine?.mode || null,
			lastUpdate: $trading.lastUpdate,
			isStale: false,
			uptimeSeconds: $trading.heartbeat?.uptime_seconds || null,
			reason: 'Trader engine stopped'
		};
	}

	// Fallback
	return {
		status: 'UNKNOWN',
		mode: $trading.engine?.mode || null,
		lastUpdate: $trading.lastUpdate,
		isStale: stale,
		uptimeSeconds: $trading.heartbeat?.uptime_seconds || null,
		reason: `Unknown engine status: ${engineStatus}`
	};
});
