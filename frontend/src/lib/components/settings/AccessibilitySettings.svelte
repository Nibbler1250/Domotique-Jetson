<script lang="ts">
	import { theme } from '$lib/stores/theme';

	let reduceMotion = $derived($theme.reduceMotion);
	let highContrast = $derived($theme.highContrast);
	let largeTouchTargets = $derived($theme.largeTouchTargets);

	function toggleReduceMotion() {
		theme.setAccessibility({ reduceMotion: !reduceMotion });
	}

	function toggleHighContrast() {
		theme.setAccessibility({ highContrast: !highContrast });
	}

	function toggleLargeTouchTargets() {
		theme.setAccessibility({ largeTouchTargets: !largeTouchTargets });
	}
</script>

<div class="space-y-3">
	<h3 class="text-sm font-medium text-[var(--color-text-muted)]">Accessibilité</h3>
	<div class="space-y-2">
		<!-- Reduce Motion -->
		<button
			onclick={toggleReduceMotion}
			class="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
		>
			<div class="text-left">
				<p class="font-medium text-[var(--color-text)]">Réduire les animations</p>
				<p class="text-sm text-[var(--color-text-muted)]">Désactive les transitions et animations</p>
			</div>
			<div
				class="relative h-6 w-11 rounded-full transition-colors"
				class:bg-[var(--color-primary)]={reduceMotion}
				class:bg-gray-300={!reduceMotion}
			>
				<div
					class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform"
					class:translate-x-5={reduceMotion}
					class:translate-x-0.5={!reduceMotion}
				></div>
			</div>
		</button>

		<!-- High Contrast -->
		<button
			onclick={toggleHighContrast}
			class="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
		>
			<div class="text-left">
				<p class="font-medium text-[var(--color-text)]">Contraste élevé</p>
				<p class="text-sm text-[var(--color-text-muted)]">Augmente le contraste des couleurs</p>
			</div>
			<div
				class="relative h-6 w-11 rounded-full transition-colors"
				class:bg-[var(--color-primary)]={highContrast}
				class:bg-gray-300={!highContrast}
			>
				<div
					class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform"
					class:translate-x-5={highContrast}
					class:translate-x-0.5={!highContrast}
				></div>
			</div>
		</button>

		<!-- Large Touch Targets -->
		<button
			onclick={toggleLargeTouchTargets}
			class="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
		>
			<div class="text-left">
				<p class="font-medium text-[var(--color-text)]">Grandes zones tactiles</p>
				<p class="text-sm text-[var(--color-text-muted)]">Boutons plus grands et faciles à toucher</p>
			</div>
			<div
				class="relative h-6 w-11 rounded-full transition-colors"
				class:bg-[var(--color-primary)]={largeTouchTargets}
				class:bg-gray-300={!largeTouchTargets}
			>
				<div
					class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform"
					class:translate-x-5={largeTouchTargets}
					class:translate-x-0.5={!largeTouchTargets}
				></div>
			</div>
		</button>
	</div>
</div>
