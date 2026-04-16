<script>
	import { activeTab } from '$lib/stores.js';
	import { AlignLeft, FileText, Music, Sigma, Settings as SettingsIcon } from 'lucide-svelte';

	const tabs = [
		{ id: 'parse', label: 'Parse', icon: FileText },
		{ id: 'line', label: 'Line', icon: AlignLeft },
		{ id: 'meter', label: 'Meter', icon: Music },
		{ id: 'maxent', label: 'MaxEnt', icon: Sigma },
		{ id: 'settings', label: 'Settings', icon: SettingsIcon }
	];
</script>

<nav>
	{#each tabs as t (t.id)}
		<button class:active={$activeTab === t.id} onclick={() => $activeTab = t.id}>
			<t.icon size={20} strokeWidth={1.75} />
			<span class="label">{t.label}</span>
		</button>
	{/each}
</nav>

<style>
	nav {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		display: flex;
		background: #fff;
		border-top: 1px solid var(--border);
		z-index: 100;
		height: var(--bottom-nav-height);
	}
	button {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.2rem;
		color: var(--text-dim);
		font-size: 0.72rem;
		background: none;
		border: none;
		cursor: pointer;
	}
	button.active {
		color: var(--accent);
	}
	.label {
		font-family: var(--font);
	}

	@media (min-width: 769px) {
		nav { display: none; }
	}
</style>
