/**
 * Device state store with WebSocket real-time updates
 */

import { writable, derived } from 'svelte/store';
import { getDevices, type DeviceWithState } from '$lib/api/devices';
import type { Device } from '$types';

export interface DeviceState {
	devices: Map<number, DeviceWithState>;
	loading: boolean;
	error: string | null;
	lastUpdated: Date | null;
}

function createDevicesStore() {
	const { subscribe, set, update } = writable<DeviceState>({
		devices: new Map(),
		loading: false,
		error: null,
		lastUpdated: null
	});

	return {
		subscribe,

		/**
		 * Load devices from API
		 */
		async load(options?: { room?: string; favorites?: boolean }) {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const response = await getDevices(options);
				const devicesMap = new Map<number, DeviceWithState>();
				for (const device of response.data) {
					devicesMap.set(device.id, device);
				}
				update((state) => ({
					...state,
					devices: devicesMap,
					loading: false,
					lastUpdated: new Date()
				}));
			} catch (err: unknown) {
				const error = err as { detail?: string };
				update((state) => ({
					...state,
					loading: false,
					error: error?.detail || 'Failed to load devices'
				}));
			}
		},

		/**
		 * Update a single device's state (from WebSocket)
		 */
		updateDeviceState(deviceId: string, attribute: string, value: unknown) {
			update((state) => {
				// Find device by name/label (deviceId from MQTT is the device name)
				let targetDevice: DeviceWithState | undefined;
				for (const [, device] of state.devices) {
					if (device.label === deviceId || device.name === deviceId) {
						targetDevice = device;
						break;
					}
				}

				if (targetDevice) {
					const updatedDevice = {
						...targetDevice,
						state: {
							...targetDevice.state,
							[attribute]: value
						}
					};
					const newDevices = new Map(state.devices);
					newDevices.set(targetDevice.id, updatedDevice);
					return { ...state, devices: newDevices };
				}
				return state;
			});
		},

		/**
		 * Set initial state from WebSocket
		 */
		setInitialState(deviceStates: Record<string, Record<string, unknown>>) {
			update((state) => {
				const newDevices = new Map(state.devices);

				for (const [deviceKey, attributes] of Object.entries(deviceStates)) {
					// Find device by name/label
					for (const [id, device] of newDevices) {
						if (device.label === deviceKey || device.name === deviceKey) {
							newDevices.set(id, {
								...device,
								state: { ...device.state, ...attributes }
							});
							break;
						}
					}
				}

				return { ...state, devices: newDevices };
			});
		},

		/**
		 * Update a device's metadata (from API response after PATCH)
		 */
		updateDevice(device: DeviceWithState) {
			update((state) => {
				const newDevices = new Map(state.devices);
				newDevices.set(device.id, device);
				return { ...state, devices: newDevices };
			});
		},

		/**
		 * Optimistic update for device state (after command success)
		 */
		setDeviceSwitch(deviceId: number, switchState: 'on' | 'off') {
			update((state) => {
				const device = state.devices.get(deviceId);
				if (device) {
					const newDevices = new Map(state.devices);
					newDevices.set(deviceId, {
						...device,
						switch_state: switchState,
						state: { ...device.state, switch: switchState }
					});
					return { ...state, devices: newDevices };
				}
				return state;
			});
		},

		/**
		 * Optimistic update for device level
		 */
		setDeviceLevel(deviceId: number, level: number) {
			update((state) => {
				const device = state.devices.get(deviceId);
				if (device) {
					const newDevices = new Map(state.devices);
					newDevices.set(deviceId, {
						...device,
						level: level,
						switch_state: level > 0 ? 'on' : 'off',
						state: { ...device.state, level: level, switch: level > 0 ? 'on' : 'off' }
					});
					return { ...state, devices: newDevices };
				}
				return state;
			});
		},

		/**
		 * Clear error
		 */
		clearError() {
			update((state) => ({ ...state, error: null }));
		},

		/**
		 * Reset store
		 */
		reset() {
			set({
				devices: new Map(),
				loading: false,
				error: null,
				lastUpdated: null
			});
		}
	};
}

export const devices = createDevicesStore();

// Derived stores for convenience
export const devicesList = derived(devices, ($devices) => Array.from($devices.devices.values()));

export const favoriteDevices = derived(devices, ($devices) =>
	Array.from($devices.devices.values()).filter((d) => d.is_favorite)
);

export const devicesByRoom = derived(devices, ($devices) => {
	const byRoom = new Map<string, DeviceWithState[]>();
	for (const device of $devices.devices.values()) {
		const room = device.room || 'Unassigned';
		if (!byRoom.has(room)) {
			byRoom.set(room, []);
		}
		byRoom.get(room)!.push(device);
	}
	return byRoom;
});
