<script>
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import BottomNav from '$lib/components/BottomNav.svelte';
	import { getMeterDefaults } from '$lib/api.js';
	import { meterConfig, allConstraints, constraintDescriptions, defaultConstraints, constraintWeights } from '$lib/stores.js';

	let { children } = $props();

	onMount(async () => {
		try {
			const data = await getMeterDefaults();
			allConstraints.set(data.all_constraints);
			constraintDescriptions.set(data.constraint_descriptions);
			defaultConstraints.set(data.defaults.constraints);
			// Only initialize meter config if constraints are empty (first load)
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
			// Initialize weights for any constraint that doesn't have one
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
		<a href="/" class:active={page.url.pathname === '/'}>Parse</a>
		<a href="/meter" class:active={page.url.pathname === '/meter'}>Meter</a>
		<a href="/maxent" class:active={page.url.pathname === '/maxent'}>MaxEnt</a>
	</nav>
	<main>
		{@render children()}
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
	.top-nav a {
		padding: 0.6rem 1.2rem;
		font-size: 1rem;
		color: var(--text-dim);
		border-bottom: 2px solid transparent;
		margin-bottom: -2px;
		transition: color 0.15s;
	}
	.top-nav a.active {
		color: var(--text);
		border-bottom-color: var(--accent);
	}
	main {
		flex: 1;
		max-width: 960px;
		width: 100%;
		margin: 0 auto;
		padding: 1rem;
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
