<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getUsers,
		createUser,
		updateUser,
		deleteUser,
		type User,
		type UserCreateInput,
		type UserUpdateInput
	} from '$lib/api/users';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let users = $state<User[]>([]);
	let notification = $state<{ message: string; type: 'success' | 'error' } | null>(null);

	// Modal state
	let showModal = $state(false);
	let modalMode = $state<'create' | 'edit'>('create');
	let editingUser = $state<User | null>(null);

	// Form state
	let formData = $state<{
		username: string;
		password: string;
		display_name: string;
		role: 'admin' | 'family_adult' | 'family_child' | 'kiosk';
	}>({
		username: '',
		password: '',
		display_name: '',
		role: 'family_adult'
	});

	const roleLabels: Record<string, string> = {
		admin: 'Administrateur',
		family_adult: 'Adulte',
		family_child: 'Enfant',
		kiosk: 'Kiosk'
	};

	const roleColors: Record<string, string> = {
		admin: 'bg-purple-600',
		family_adult: 'bg-blue-600',
		family_child: 'bg-green-600',
		kiosk: 'bg-gray-600'
	};

	onMount(async () => {
		await loadUsers();
	});

	async function loadUsers() {
		loading = true;
		error = null;
		try {
			const result = await getUsers();
			users = result.data;
		} catch (e) {
			console.error('Failed to load users:', e);
			error = 'Impossible de charger les utilisateurs';
		} finally {
			loading = false;
		}
	}

	function showNotification(message: string, type: 'success' | 'error') {
		notification = { message, type };
		setTimeout(() => {
			notification = null;
		}, 3000);
	}

	function openCreateModal() {
		modalMode = 'create';
		editingUser = null;
		formData = {
			username: '',
			password: '',
			display_name: '',
			role: 'family_adult'
		};
		showModal = true;
	}

	function openEditModal(user: User) {
		modalMode = 'edit';
		editingUser = user;
		formData = {
			username: user.username,
			password: '',
			display_name: user.display_name,
			role: user.role
		};
		showModal = true;
	}

	function closeModal() {
		showModal = false;
		editingUser = null;
	}

	async function handleSubmit() {
		try {
			if (modalMode === 'create') {
				const input: UserCreateInput = {
					username: formData.username,
					password: formData.password,
					display_name: formData.display_name,
					role: formData.role
				};
				await createUser(input);
				showNotification('Utilisateur créé', 'success');
			} else if (editingUser) {
				const updates: UserUpdateInput = {
					display_name: formData.display_name,
					role: formData.role
				};
				if (formData.password) {
					updates.password = formData.password;
				}
				await updateUser(editingUser.id, updates);
				showNotification('Utilisateur modifié', 'success');
			}
			closeModal();
			await loadUsers();
		} catch (e) {
			showNotification("Erreur lors de l'opération", 'error');
		}
	}

	async function handleToggleActive(user: User) {
		try {
			await updateUser(user.id, { is_active: !user.is_active });
			users = users.map((u) => (u.id === user.id ? { ...u, is_active: !u.is_active } : u));
			showNotification(`${user.display_name} ${!user.is_active ? 'activé' : 'désactivé'}`, 'success');
		} catch (e) {
			showNotification("Erreur lors de la mise à jour", 'error');
		}
	}

	async function handleDelete(user: User) {
		if (!confirm(`Supprimer l'utilisateur ${user.display_name} ?`)) return;

		try {
			await deleteUser(user.id);
			users = users.filter((u) => u.id !== user.id);
			showNotification('Utilisateur supprimé', 'success');
		} catch (e) {
			showNotification('Erreur lors de la suppression', 'error');
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return 'Jamais';
		return new Date(dateStr).toLocaleString('fr-CA', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<svelte:head>
	<title>Utilisateurs - Family Hub</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<!-- Header -->
	<header class="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
			<div class="flex items-center gap-3">
				<a
					href="/admin"
					class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
					aria-label="Retour à l'admin"
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
				<h1 class="text-lg font-semibold text-[var(--color-text)]">Gestion des utilisateurs</h1>
			</div>

			<button
				onclick={openCreateModal}
				class="flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm text-white hover:opacity-90"
			>
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"
					></path>
				</svg>
				Ajouter
			</button>
		</div>
	</header>

	<main class="mx-auto max-w-7xl px-4 py-6">
		<!-- Notification -->
		{#if notification}
			{#if notification.type === 'success'}
				<div
					class="mb-6 rounded-lg bg-green-100 p-4 text-green-700 dark:bg-green-900/30 dark:text-green-400"
				>
					{notification.message}
				</div>
			{:else}
				<div
					class="mb-6 rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900/30 dark:text-red-400"
				>
					{notification.message}
				</div>
			{/if}
		{/if}

		<!-- Error -->
		{#if error}
			<div
				class="mb-6 rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900/30 dark:text-red-400"
			>
				{error}
				<button onclick={() => (error = null)} class="ml-2 underline">Fermer</button>
			</div>
		{/if}

		<!-- Loading -->
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
			<!-- Users List -->
			<div class="space-y-3">
				{#each users as user}
					<div
						class="flex items-center justify-between rounded-xl bg-[var(--color-surface)] p-4"
						class:opacity-50={!user.is_active}
					>
						<div class="flex items-center gap-4">
							<div
								class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-primary)] text-white"
							>
								{user.display_name.charAt(0).toUpperCase()}
							</div>
							<div>
								<div class="flex items-center gap-2">
									<h3 class="font-medium text-[var(--color-text)]">{user.display_name}</h3>
									<span
										class="rounded px-2 py-0.5 text-xs text-white {roleColors[user.role]}"
									>
										{roleLabels[user.role]}
									</span>
									{#if !user.is_active}
										<span
											class="rounded bg-red-200 px-2 py-0.5 text-xs text-red-700 dark:bg-red-900/30 dark:text-red-400"
										>
											Désactivé
										</span>
									{/if}
								</div>
								<p class="text-sm text-[var(--color-text-muted)]">
									@{user.username} • Dernière connexion: {formatDate(user.last_login)}
								</p>
							</div>
						</div>

						<div class="flex items-center gap-2">
							<button
								onclick={() => openEditModal(user)}
								class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700"
								aria-label="Modifier {user.display_name}"
							>
								Modifier
							</button>
							<button
								onclick={() => handleToggleActive(user)}
								class="rounded-lg px-3 py-1.5 text-sm text-white"
								class:bg-green-600={!user.is_active}
								class:hover:bg-green-700={!user.is_active}
								class:bg-gray-500={user.is_active}
								class:hover:bg-gray-600={user.is_active}
								aria-label={user.is_active ? 'Désactiver' : 'Activer'}
							>
								{user.is_active ? 'Désactiver' : 'Activer'}
							</button>
							<button
								onclick={() => handleDelete(user)}
								class="rounded-lg bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700"
								aria-label="Supprimer {user.display_name}"
							>
								Supprimer
							</button>
						</div>
					</div>
				{/each}

				{#if users.length === 0}
					<div class="rounded-xl bg-[var(--color-surface)] p-6 text-center">
						<p class="text-[var(--color-text-muted)]">Aucun utilisateur trouvé</p>
					</div>
				{/if}
			</div>
		{/if}
	</main>

	<!-- Modal -->
	{#if showModal}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
			<div class="w-full max-w-md rounded-xl bg-[var(--color-surface)] p-6">
				<h2 class="mb-4 text-lg font-semibold text-[var(--color-text)]">
					{modalMode === 'create' ? 'Nouvel utilisateur' : 'Modifier utilisateur'}
				</h2>

				<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
					<div class="space-y-4">
						<div>
							<label for="username" class="mb-1 block text-sm text-[var(--color-text-muted)]"
								>Nom d'utilisateur</label
							>
							<input
								type="text"
								id="username"
								bind:value={formData.username}
								disabled={modalMode === 'edit'}
								required
								class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-[var(--color-text)] disabled:opacity-50"
							/>
						</div>

						<div>
							<label for="display_name" class="mb-1 block text-sm text-[var(--color-text-muted)]"
								>Nom affiché</label
							>
							<input
								type="text"
								id="display_name"
								bind:value={formData.display_name}
								required
								class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-[var(--color-text)]"
							/>
						</div>

						<div>
							<label for="password" class="mb-1 block text-sm text-[var(--color-text-muted)]">
								{modalMode === 'create' ? 'Mot de passe' : 'Nouveau mot de passe (laisser vide pour garder)'}
							</label>
							<input
								type="password"
								id="password"
								bind:value={formData.password}
								required={modalMode === 'create'}
								class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-[var(--color-text)]"
							/>
						</div>

						<div>
							<label for="role" class="mb-1 block text-sm text-[var(--color-text-muted)]"
								>Rôle</label
							>
							<select
								id="role"
								bind:value={formData.role}
								class="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-[var(--color-text)]"
							>
								<option value="admin">Administrateur</option>
								<option value="family_adult">Adulte</option>
								<option value="family_child">Enfant</option>
								<option value="kiosk">Kiosk</option>
							</select>
						</div>
					</div>

					<div class="mt-6 flex gap-3">
						<button
							type="button"
							onclick={closeModal}
							class="flex-1 rounded-lg border border-[var(--color-border)] px-4 py-2 text-[var(--color-text)] hover:bg-[var(--color-bg)]"
						>
							Annuler
						</button>
						<button
							type="submit"
							class="flex-1 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-white hover:opacity-90"
						>
							{modalMode === 'create' ? 'Créer' : 'Enregistrer'}
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}
</div>
