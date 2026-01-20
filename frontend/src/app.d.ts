// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		interface Error {
			message: string;
			code?: string;
		}
		interface Locals {
			user?: {
				id: number;
				username: string;
				role: 'admin' | 'family_adult' | 'family_child' | 'kiosk';
				profile_id: number;
			};
		}
		interface PageData {}
		interface PageState {}
		interface Platform {}
	}
}

export {};
