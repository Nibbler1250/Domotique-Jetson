/**
 * WebSocket store for real-time device updates
 */

import { writable } from 'svelte/store';
import { devices } from './devices';

export interface WsState {
	connected: boolean;
	error: string | null;
	reconnecting: boolean;
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws';

function createWebSocketStore() {
	const { subscribe, set, update } = writable<WsState>({
		connected: false,
		error: null,
		reconnecting: false
	});

	let ws: WebSocket | null = null;
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	let pingInterval: ReturnType<typeof setInterval> | null = null;

	function connect() {
		if (ws?.readyState === WebSocket.OPEN) return;

		update((state) => ({ ...state, error: null, reconnecting: false }));

		try {
			ws = new WebSocket(WS_URL);

			ws.onopen = () => {
				update((state) => ({ ...state, connected: true, error: null, reconnecting: false }));
				console.log('WebSocket connected');

				// Start ping interval
				pingInterval = setInterval(() => {
					if (ws?.readyState === WebSocket.OPEN) {
						ws.send(JSON.stringify({ type: 'ping' }));
					}
				}, 30000);
			};

			ws.onmessage = (event) => {
				try {
					const message = JSON.parse(event.data);
					handleMessage(message);
				} catch (e) {
					console.error('Failed to parse WebSocket message:', e);
				}
			};

			ws.onerror = (error) => {
				console.error('WebSocket error:', error);
				update((state) => ({ ...state, error: 'Connection error' }));
			};

			ws.onclose = () => {
				update((state) => ({ ...state, connected: false }));
				console.log('WebSocket closed');

				// Clear ping interval
				if (pingInterval) {
					clearInterval(pingInterval);
					pingInterval = null;
				}

				// Reconnect after delay
				if (!reconnectTimer) {
					update((state) => ({ ...state, reconnecting: true }));
					reconnectTimer = setTimeout(() => {
						reconnectTimer = null;
						connect();
					}, 5000);
				}
			};
		} catch (e) {
			console.error('Failed to create WebSocket:', e);
			update((state) => ({ ...state, error: 'Failed to connect' }));
		}
	}

	function handleMessage(message: { type: string; payload: unknown }) {
		switch (message.type) {
			case 'initial_state': {
				const payload = message.payload as { devices: Record<string, Record<string, unknown>> };
				devices.setInitialState(payload.devices);
				break;
			}
			case 'device_state': {
				const payload = message.payload as {
					device_id: string;
					attribute: string;
					value: unknown;
				};
				devices.updateDeviceState(payload.device_id, payload.attribute, payload.value);
				break;
			}
			case 'pong':
				// Keepalive response, no action needed
				break;
			default:
				console.log('Unknown WebSocket message type:', message.type);
		}
	}

	function disconnect() {
		if (reconnectTimer) {
			clearTimeout(reconnectTimer);
			reconnectTimer = null;
		}
		if (pingInterval) {
			clearInterval(pingInterval);
			pingInterval = null;
		}
		if (ws) {
			ws.close();
			ws = null;
		}
		set({ connected: false, error: null, reconnecting: false });
	}

	return {
		subscribe,
		connect,
		disconnect
	};
}

export const websocket = createWebSocketStore();
