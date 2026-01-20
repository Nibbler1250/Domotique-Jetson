/**
 * Root layout load function
 * Initializes auth state on the client
 */

import { browser } from '$app/environment';
import { auth } from '$stores/auth';

export const ssr = true;

export async function load() {
	// Initialize auth on client side
	if (browser) {
		await auth.init();
	}

	return {};
}
