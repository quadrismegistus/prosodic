<script>
	import { onMount } from 'svelte';
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import BottomNav from '$lib/components/BottomNav.svelte';
	import ParseTab from '$lib/components/ParseTab.svelte';
	import MeterTab from '$lib/components/MeterTab.svelte';
	import MaxEntTab from '$lib/components/MaxEntTab.svelte';
	import LineViewTab from '$lib/components/LineViewTab.svelte';
	import SettingsTab from '$lib/components/SettingsTab.svelte';
	import { getMeterDefaults } from '$lib/api.js';
	import { meterConfig, allConstraints, constraintDescriptions, defaultConstraints, constraintWeights, activeTab } from '$lib/stores.js';

	// Save/restore scroll position per tab
	const scrollPositions = { parse: 0, meter: 0, maxent: 0, line: 0, settings: 0 };
	let prevTab = $state($activeTab);

	$effect(() => {
		const tab = $activeTab;
		if (tab !== prevTab) {
			scrollPositions[prevTab] = window.scrollY;
			prevTab = tab;
			requestAnimationFrame(() => window.scrollTo(0, scrollPositions[tab]));
		}
	});

	onMount(async () => {
		try {
			const data = await getMeterDefaults();
			allConstraints.set(data.all_constraints);
			constraintDescriptions.set(data.constraint_descriptions);
			defaultConstraints.set(data.defaults.constraints);
			meterConfig.update(c => {
				if (c.constraints.length === 0) {
					return {
						...c,
						constraints: data.defaults.constraints,
						max_s: data.defaults.max_s,
						max_w: data.defaults.max_w,
						resolve_optionality: data.defaults.resolve_optionality
					};
				}
				return c;
			});
			constraintWeights.update(w => {
				const updated = { ...w };
				for (const c of data.all_constraints) {
					if (!(c in updated)) updated[c] = 1.0;
				}
				return updated;
			});
		} catch (e) {
			console.error('Failed to load meter defaults:', e);
		}
	});
</script>

<div class="app">
	<Header />
	<nav class="top-nav">
		<button class:active={$activeTab === 'parse'} onclick={() => $activeTab = 'parse'}>Parse</button>
		<button class:active={$activeTab === 'line'} onclick={() => $activeTab = 'line'}>Line</button>
		<button class:active={$activeTab === 'meter'} onclick={() => $activeTab = 'meter'}>Meter</button>
		<button class:active={$activeTab === 'maxent'} onclick={() => $activeTab = 'maxent'}>MaxEnt</button>
		<span class="spacer"></span>
		<button class:active={$activeTab === 'settings'} onclick={() => $activeTab = 'settings'}>Settings</button>
	</nav>
	<main>
		<div class="tab-panel" class:hidden={$activeTab !== 'parse'}>
			<ParseTab />
		</div>
		<div class="tab-panel" class:hidden={$activeTab !== 'line'}>
			<LineViewTab />
		</div>
		<div class="tab-panel" class:hidden={$activeTab !== 'meter'}>
			<MeterTab />
		</div>
		<div class="tab-panel" class:hidden={$activeTab !== 'maxent'}>
			<MaxEntTab />
		</div>
		<div class="tab-panel" class:hidden={$activeTab !== 'settings'}>
			<SettingsTab />
		</div>
	</main>
	<BottomNav />
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}
	.top-nav {
		display: none;
		gap: 0;
		border-bottom: 2px solid var(--border);
		background: #fff;
		padding: 0 1rem;
	}
	.top-nav button {
		padding: 0.6rem 1.2rem;
		font-size: 1rem;
		color: var(--text-dim);
		border: none;
		border-bottom: 2px solid transparent;
		margin-bottom: -2px;
		transition: color 0.15s;
		background: none;
		cursor: pointer;
		font-family: var(--font);
	}
	.top-nav button.active {
		color: var(--text);
		border-bottom-color: var(--accent);
	}
	.spacer {
		flex: 1;
	}
	main {
		flex: 1;
		max-width: 960px;
		width: 100%;
		margin: 0 auto;
		padding: 1rem;
	}
	.tab-panel.hidden {
		display: none;
	}

	@media (min-width: 769px) {
		.top-nav { display: flex; }
	}
	@media (max-width: 768px) {
		main {
			padding: 0.75rem;
			padding-bottom: calc(var(--bottom-nav-height) + 1rem);
		}
	}
</style>
