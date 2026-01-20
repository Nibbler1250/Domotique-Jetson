import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/login');
	});

	test('should display login form', async ({ page }) => {
		await expect(page.getByRole('heading', { name: 'Family Hub' })).toBeVisible();
		await expect(page.getByLabel('Utilisateur')).toBeVisible();
		await expect(page.getByLabel('Mot de passe')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Se connecter' })).toBeVisible();
	});

	test('should show validation for empty fields', async ({ page }) => {
		// Button should be disabled when fields are empty
		const submitButton = page.getByRole('button', { name: 'Se connecter' });
		await expect(submitButton).toBeDisabled();
	});

	test('should enable submit when fields are filled', async ({ page }) => {
		await page.getByLabel('Utilisateur').fill('testuser');
		await page.getByLabel('Mot de passe').fill('testpass');

		const submitButton = page.getByRole('button', { name: 'Se connecter' });
		await expect(submitButton).toBeEnabled();
	});

	test('should show error for invalid credentials', async ({ page }) => {
		await page.getByLabel('Utilisateur').fill('invaliduser');
		await page.getByLabel('Mot de passe').fill('invalidpass');
		await page.getByRole('button', { name: 'Se connecter' }).click();

		// Wait for error message
		await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });
	});

	test('should be touch-friendly on mobile', async ({ page }) => {
		// Check minimum touch target size (44px)
		const usernameInput = page.getByLabel('Utilisateur');
		const box = await usernameInput.boundingBox();
		expect(box?.height).toBeGreaterThanOrEqual(44);
	});
});

test.describe('Route Protection', () => {
	test('should redirect to login when not authenticated', async ({ page }) => {
		await page.goto('/');
		// Should redirect to login
		await expect(page).toHaveURL('/login');
	});
});
