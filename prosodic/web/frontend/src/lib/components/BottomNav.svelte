<script>
	import { activeTab } from '$lib/stores.js';
</script>

<nav>
	<button class:active={$activeTab === 'parse'} onclick={() => $activeTab = 'parse'}>
		<span class="icon">⏑</span>
		<span class="label">Parse</span>
	</button>
	<button class:active={$activeTab === 'line'} onclick={() => $activeTab = 'line'}>
		<span class="icon">⌇</span>
		<span class="label">Line</span>
	</button>
	<button class:active={$activeTab === 'meter'} onclick={() => $activeTab = 'meter'}>
		<span class="icon">♩</span>
		<span class="label">Meter</span>
	</button>
	<button class:active={$activeTab === 'maxent'} onclick={() => $activeTab = 'maxent'}>
		<span class="icon">λ</span>
		<span class="label">MaxEnt</span>
	</button>
	<button class:active={$activeTab === 'settings'} onclick={() => $activeTab = 'settings'}>
		<svg class="icon-svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd"/></svg>
		<span class="label">Settings</span>
	</button>
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
		gap: 0.15rem;
		color: var(--text-dim);
		font-size: 0.75rem;
		text-decoration: none;
		transition: color 0.15s;
		background: none;
		border: none;
		cursor: pointer;
	}
	button.active {
		color: var(--accent);
	}
	.icon {
		font-size: 1.3rem;
		line-height: 1;
	}
	.icon-svg {
		width: 1.3rem;
		height: 1.3rem;
	}
	.label {
		font-family: var(--font);
	}

	@media (min-width: 769px) {
		nav { display: none; }
	}
</style>
