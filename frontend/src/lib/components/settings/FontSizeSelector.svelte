<script lang="ts">
	import { theme, fontSizes, type FontSize } from '$lib/stores/theme';

	let currentSize = $derived($theme.fontSize);

	const sizes: { id: FontSize; name: string; preview: string }[] = [
		{ id: 'small', name: 'Petit', preview: 'Aa' },
		{ id: 'medium', name: 'Normal', preview: 'Aa' },
		{ id: 'large', name: 'Grand', preview: 'Aa' },
		{ id: 'xlarge', name: 'Très grand', preview: 'Aa' }
	];

	function selectSize(id: FontSize) {
		theme.setFontSize(id);
	}
</script>

<div class="space-y-3">
	<h3 class="text-sm font-medium text-[var(--color-text-muted)]">Taille du texte</h3>
	<div class="flex gap-2">
		{#each sizes as s}
			{@const config = fontSizes[s.id]}
			<button
				onclick={() => selectSize(s.id)}
				class="flex flex-1 flex-col items-center rounded-xl border-2 px-3 py-2 transition-all {currentSize === s.id ? 'border-[var(--color-primary)] bg-[var(--color-primary)] bg-opacity-10' : 'border-[var(--color-border)]'}"
			>
				<span
					class="font-medium text-[var(--color-text)]"
					style="font-size: {config.base}"
				>
					{s.preview}
				</span>
				<span class="mt-1 text-xs text-[var(--color-text-muted)]">{s.name}</span>
			</button>
		{/each}
	</div>
</div>
