<script lang="ts">
	import { onMount } from 'svelte';
	import { theme } from '$lib/stores/theme';
	import ThemeSelector from '$lib/components/settings/ThemeSelector.svelte';
	import FontSizeSelector from '$lib/components/settings/FontSizeSelector.svelte';
	import AccessibilitySettings from '$lib/components/settings/AccessibilitySettings.svelte';

	let loading = $derived($theme.loading);

	onMount(() => {
		theme.load();
		return theme.initSystemListener();
	});
</script>

<svelte:head>
	<title>Paramètres - Family Hub</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3">
			<a
				href="/dashboard"
				class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
				aria-label="Retour au tableau de bord"
			>
				<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 19l-7-7 7-7"
					></path>
				</svg>
			</a>
			<h1 class="text-lg font-semibold text-[var(--color-text)]">Paramètres</h1>
		</div>
	</header>

	<main class="mx-auto max-w-3xl px-4 py-6">
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
		{:else}
			<div class="space-y-8">
				<!-- Theme Selection -->
				<section class="rounded-xl bg-[var(--color-surface)] p-4">
					<ThemeSelector />
				</section>

				<!-- Font Size -->
				<section class="rounded-xl bg-[var(--color-surface)] p-4">
					<FontSizeSelector />
				</section>

				<!-- Accessibility -->
				<section class="rounded-xl bg-[var(--color-surface)] p-4">
					<AccessibilitySettings />
				</section>

				<!-- Info -->
				<section class="rounded-xl bg-[var(--color-surface)] p-4">
					<h3 class="text-sm font-medium text-[var(--color-text-muted)]">À propos</h3>
					<div class="mt-3 space-y-2 text-sm text-[var(--color-text)]">
						<p>Family Hub v0.1.0</p>
						<p class="text-[var(--color-text-muted)]">
							Application de domotique pour la maison connectée.
						</p>
					</div>
				</section>
			</div>
		{/if}
	</main>
</div>
