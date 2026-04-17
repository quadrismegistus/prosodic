<script>
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import BottomNav from '$lib/components/BottomNav.svelte';
	import ParseTab from '$lib/components/ParseTab.svelte';
	import MeterTab from '$lib/components/MeterTab.svelte';
	import MaxEntTab from '$lib/components/MaxEntTab.svelte';
	import LineViewTab from '$lib/components/LineViewTab.svelte';
	import SettingsTab from '$lib/components/SettingsTab.svelte';
	import { getMeterDefaults } from '$lib/api.js';
	import { meterConfig, allConstraints, constraintDescriptions, defaultConstraints, constraintWeights, activeTab, goTab } from '$lib/stores.js';
	import { AlignLeft, FileText, Music, Sigma, Settings as SettingsIcon } from 'lucide-svelte';

	const tabs = [
		{ id: 'parse', label: 'Parse', icon: FileText },
		{ id: 'line', label: 'Line', icon: AlignLeft },
		{ id: 'meter', label: 'Meter', icon: Music },
		{ id: 'maxent', label: 'MaxEnt', icon: Sigma }
	];
	const settingsTab = { id: 'settings', label: 'Settings', icon: SettingsIcon };

	const VALID_TABS = ['parse', 'line', 'meter', 'maxent', 'settings'];

	// Save/restore scroll position per tab
	const scrollPositions = { parse: 0, meter: 0, maxent: 0, line: 0, settings: 0 };
	let prevTab = $state($activeTab);
	let syncingFromUrl = false;

	function tabFromPath(pathname) {
		const seg = pathname.replace(/^\/+/, '').split('/')[0];
		return VALID_TABS.includes(seg) ? seg : 'parse';
	}

	$effect(() => {
		const tab = $activeTab;
		if (tab !== prevTab) {
			scrollPositions[prevTab] = window.scrollY;
			prevTab = tab;
			requestAnimationFrame(() => window.scrollTo(0, scrollPositions[tab]));
		}
	});

	onMount(async () => {
		// Sync initial tab from URL, not localStorage
		const urlTab = tabFromPath(window.location.pathname);
		$activeTab = urlTab;
		prevTab = urlTab;
		// Replace current history entry so back doesn't go to blank
		history.replaceState({ tab: urlTab }, '', window.location.pathname);

		window.addEventListener('popstate', () => {
			syncingFromUrl = true;
			$activeTab = tabFromPath(window.location.pathname);
			syncingFromUrl = false;
		});

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
		{#each tabs as t (t.id)}
			<button class:active={$activeTab === t.id} onclick={() => goTab(t.id)}>
				<t.icon size={16} strokeWidth={1.75} />
				<span>{t.label}</span>
			</button>
		{/each}
		<span class="spacer"></span>
		<button class:active={$activeTab === settingsTab.id} onclick={() => goTab(settingsTab.id)}>
			<settingsTab.icon size={16} strokeWidth={1.75} />
			<span>{settingsTab.label}</span>
		</button>
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
		padding: 0 1.5rem;
	}
	.top-nav button {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.65rem 1rem;
		font-size: 0.95rem;
		color: var(--text-dim);
		border: none;
		border-bottom: 2px solid transparent;
		margin-bottom: -2px;
		transition: color 0.15s;
		background: none;
		cursor: pointer;
		font-family: var(--font);
	}
	.top-nav button:hover {
		color: var(--text);
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
		width: 100%;
		padding: 1rem 1.5rem;
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
			max-width: 100%;
		}
	}
</style>
