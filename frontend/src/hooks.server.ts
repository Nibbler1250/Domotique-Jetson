/**
 * Server hooks for route protection
 */

import { redirect, type Handle } from '@sveltejs/kit';

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/api'];

export const handle: Handle = async ({ event, resolve }) => {
	const { pathname } = event.url;

	// Allow public routes
	if (PUBLIC_ROUTES.some((route) => pathname.startsWith(route))) {
		return resolve(event);
	}

	// Check for access token in cookies
	const accessToken = event.cookies.get('access_token');

	// Redirect to login if not authenticated
	if (!accessToken) {
		throw redirect(303, '/login');
	}

	// Continue with the request
	return resolve(event);
};
