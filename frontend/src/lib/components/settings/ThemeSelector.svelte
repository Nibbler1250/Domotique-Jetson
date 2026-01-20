<script lang="ts">
	import { theme, themes, type ThemeId } from '$lib/stores/theme';

	let currentTheme = $derived($theme.theme);

	const themeList: { id: ThemeId; name: string; description: string }[] = [
		{ id: 'system', name: 'Système', description: 'Suit le thème du système' },
		{ id: 'light', name: 'Clair', description: 'Thème clair classique' },
		{ id: 'dark', name: 'Sombre', description: 'Économise les yeux' },
		{ id: 'simon', name: 'Simon', description: 'Bleu tech moderne' },
		{ id: 'caroline', name: 'Caroline', description: 'Tons chauds apaisants' },
		{ id: 'kids', name: 'Enfants', description: 'Coloré et amusant' },
		{ id: 'kiosk', name: 'Kiosk', description: 'Optimisé tablette murale' }
	];

	function selectTheme(id: ThemeId) {
		theme.setTheme(id);
	}
</script>

<div class="space-y-3">
	<h3 class="text-sm font-medium text-[var(--color-text-muted)]">Thème</h3>
	<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
		{#each themeList as t}
			{@const colors = themes[t.id === 'system' ? 'light' : t.id].colors}
			<button
				onclick={() => selectTheme(t.id)}
				class="relative flex flex-col items-start rounded-xl border-2 p-3 transition-all {currentTheme === t.id ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-primary)] ring-opacity-20' : 'border-[var(--color-border)]'}"
			>
				<!-- Color preview -->
				<div class="mb-2 flex gap-1">
					<div
						class="h-6 w-6 rounded-full border border-black/10"
						style="background-color: {colors.primary}"
					></div>
					<div
						class="h-6 w-6 rounded-full border border-black/10"
						style="background-color: {colors.bg}"
					></div>
					<div
						class="h-6 w-6 rounded-full border border-black/10"
						style="background-color: {colors.surface}"
					></div>
				</div>

				<!-- Label -->
				<span class="font-medium text-[var(--color-text)]">{t.name}</span>
				<span class="text-xs text-[var(--color-text-muted)]">{t.description}</span>

				<!-- Selected indicator -->
				{#if currentTheme === t.id}
					<div
						class="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-[var(--color-primary)]"
					>
						<svg class="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"
							></path>
						</svg>
					</div>
				{/if}
			</button>
		{/each}
	</div>
</div>
