<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$stores/auth';

	let username = $state('');
	let password = $state('');
	let isSubmitting = $state(false);

	// Subscribe to auth state for error display
	let authError = $derived($auth.error);

	async function handleSubmit(event: Event) {
		event.preventDefault();
		if (isSubmitting) return;

		isSubmitting = true;
		auth.clearError();

		try {
			await auth.login({ username, password });
			goto('/');
		} catch {
			// Error is handled by the store
		} finally {
			isSubmitting = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !isSubmitting) {
			handleSubmit(event);
		}
	}
</script>

<svelte:head>
	<title>Login - Family Hub</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-[var(--color-bg)] p-4">
	<div class="w-full max-w-sm">
		<!-- Logo / Title -->
		<div class="mb-8 text-center">
			<div
				class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-primary)]"
			>
				<svg
					class="h-8 w-8 text-white"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
					></path>
				</svg>
			</div>
			<h1 class="text-2xl font-bold text-[var(--color-text)]">Family Hub</h1>
			<p class="mt-1 text-[var(--color-text-muted)]">Bienvenue</p>
		</div>

		<!-- Login Form -->
		<form
			onsubmit={handleSubmit}
			class="rounded-xl bg-[var(--color-surface)] p-6 shadow-lg"
		>
			{#if authError}
				<div
					class="mb-4 rounded-lg bg-red-100 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400"
					role="alert"
				>
					{authError}
				</div>
			{/if}

			<div class="space-y-4">
				<div>
					<label for="username" class="block text-sm font-medium text-[var(--color-text)]">
						Utilisateur
					</label>
					<input
						type="text"
						id="username"
						bind:value={username}
						onkeydown={handleKeydown}
						autocomplete="username"
						required
						class="mt-1 block w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
						style="min-height: var(--touch-target);"
						placeholder="Entrez votre nom d'utilisateur"
					/>
				</div>

				<div>
					<label for="password" class="block text-sm font-medium text-[var(--color-text)]">
						Mot de passe
					</label>
					<input
						type="password"
						id="password"
						bind:value={password}
						onkeydown={handleKeydown}
						autocomplete="current-password"
						required
						class="mt-1 block w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-4 py-3 text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20"
						style="min-height: var(--touch-target);"
						placeholder="Entrez votre mot de passe"
					/>
				</div>
			</div>

			<button
				type="submit"
				disabled={isSubmitting || !username || !password}
				class="mt-6 flex w-full items-center justify-center rounded-lg bg-[var(--color-primary)] px-4 py-3 font-medium text-white transition-colors hover:bg-[var(--color-primary)]/90 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50 disabled:cursor-not-allowed disabled:opacity-50"
				style="min-height: var(--touch-target);"
			>
				{#if isSubmitting}
					<svg class="mr-2 h-5 w-5 animate-spin" viewBox="0 0 24 24">
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
					Connexion...
				{:else}
					Se connecter
				{/if}
			</button>
		</form>

		<!-- Footer -->
		<p class="mt-6 text-center text-sm text-[var(--color-text-muted)]">
			Family Hub v0.1.0
		</p>
	</div>
</div>
