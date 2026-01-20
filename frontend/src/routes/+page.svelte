<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$stores/auth';

	// Get auth state
	let user = $derived($auth.data);
	let loading = $derived($auth.loading);

	// Redirect to dashboard if logged in
	onMount(() => {
		if (user) {
			goto('/dashboard');
		}
	});

	async function handleLogout() {
		await auth.logout();
		goto('/login');
	}
</script>

<svelte:head>
	<title>Dashboard - Family Hub</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
			<div class="flex items-center gap-3">
				<div
					class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-primary)]"
				>
					<svg
						class="h-5 w-5 text-white"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
						></path>
					</svg>
				</div>
				<h1 class="text-xl font-semibold text-[var(--color-text)]">Family Hub</h1>
			</div>

			{#if user}
				<div class="flex items-center gap-4">
					<div class="text-right">
						<p class="text-sm font-medium text-[var(--color-text)]">{user.display_name}</p>
						<p class="text-xs text-[var(--color-text-muted)]">{user.role}</p>
					</div>
					<button
						onclick={handleLogout}
						class="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-bg)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
					>
						Déconnexion
					</button>
				</div>
			{/if}
		</div>
	</header>

	<!-- Main Content -->
	<main class="mx-auto max-w-7xl px-4 py-8">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<svg class="h-8 w-8 animate-spin text-[var(--color-primary)]" viewBox="0 0 24 24">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
						fill="none"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
					></path>
				</svg>
			</div>
		{:else if user}
			<div class="rounded-xl bg-[var(--color-surface)] p-6 shadow-sm">
				<h2 class="text-lg font-semibold text-[var(--color-text)]">
					Bienvenue, {user.display_name}!
				</h2>
				<p class="mt-2 text-[var(--color-text-muted)]">
					Dashboard en construction. Les widgets seront ajoutés dans Sprint 2.
				</p>

				<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
					<!-- Placeholder cards for future widgets -->
					{#each ['Température', 'Lumières', 'Sécurité', 'Modes'] as widget}
						<div
							class="rounded-lg border border-dashed border-[var(--color-border)] p-4 text-center"
						>
							<p class="text-sm text-[var(--color-text-muted)]">{widget}</p>
							<p class="mt-1 text-xs text-[var(--color-text-muted)]">Sprint 2+</p>
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="text-center py-12">
				<p class="text-[var(--color-text-muted)]">Non authentifié</p>
			</div>
		{/if}
	</main>
</div>
