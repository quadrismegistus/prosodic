<script>
	import {
		meterConfig, allConstraints, constraintDescriptions,
		defaultConstraints, constraintWeights, zoneWeights
	} from '$lib/stores.js';

	function toggleConstraint(name) {
		meterConfig.update(c => {
			const idx = c.constraints.indexOf(name);
			if (idx >= 0) {
				c.constraints = c.constraints.filter(n => n !== name);
			} else {
				c.constraints = [...c.constraints, name];
			}
			return c;
		});
	}

	function setWeight(name, val) {
		constraintWeights.update(w => ({ ...w, [name]: parseFloat(val) || 0 }));
	}

	function resetConstraints() {
		meterConfig.update(c => ({
			...c,
			constraints: [...$defaultConstraints],
			max_s: 2,
			max_w: 2,
			resolve_optionality: true
		}));
	}

	function resetWeights() {
		constraintWeights.update(w => {
			const reset = {};
			for (const k of Object.keys(w)) reset[k] = 1.0;
			return reset;
		});
		$zoneWeights = null;
	}

	let hasZoneWeights = $derived($zoneWeights != null);
	let maxWeight = $derived.by(() => {
		if (!$zoneWeights) return 1;
		const vals = Object.values($zoneWeights);
		return vals.length ? Math.max(...vals) : 1;
	});
	let sortedWeightEntries = $derived.by(() => {
		if (!$zoneWeights) return [];
		return Object.entries($zoneWeights)
			.filter(([, w]) => w > 0.001)
			.sort((a, b) => b[1] - a[1]);
	});
</script>

<div class="page">
	<h2 class="page-title">Meter Configuration</h2>
	<p class="page-desc">Configure constraints and weights used by the parser. MaxEnt training will update weights automatically.</p>

	<div class="actions">
		<button class="btn" onclick={resetConstraints}>Reset Constraints</button>
		<button class="btn" onclick={resetWeights}>Reset Weights</button>
	</div>

	<section class="section">
		<h3 class="section-title">Constraints</h3>
		{#if hasZoneWeights}
			<p class="override-note">Manual weights are overridden by MaxEnt zone weights below. Reset weights to use manual values.</p>
		{/if}
		<div class="constraint-header">
			<span class="ch-name">Constraint</span>
			<span class="ch-weight">Weight</span>
			<span class="ch-on">On</span>
		</div>
		{#each $allConstraints as cname}
			{@const active = $meterConfig.constraints.includes(cname)}
			<div class="constraint-row" class:inactive={!active} class:overridden={hasZoneWeights}>
				<div class="c-info">
					<span class="c-name">*{cname}</span>
					{#if $constraintDescriptions[cname]}
						<span class="c-desc">{$constraintDescriptions[cname]}</span>
					{/if}
				</div>
				<input class="c-weight"
					type="number" step="0.1" min="0"
					value={$constraintWeights[cname] ?? 1.0}
					oninput={(e) => setWeight(cname, e.target.value)}
					disabled={!active || hasZoneWeights} />
				<input class="c-check" type="checkbox"
					checked={active}
					onchange={() => toggleConstraint(cname)} />
			</div>
		{/each}
	</section>

	{#if hasZoneWeights}
		<section class="section">
			<h3 class="section-title">
				Constraint Weights <span class="badge">from MaxEnt</span>
			</h3>
			<p class="zone-note">Learned by MaxEnt training and used for scoring. Reset to clear.</p>
			<div class="zone-list">
				{#each sortedWeightEntries as [name, weight]}
					<div class="zone-row">
						<span class="z-name">{name}</span>
						<span class="z-weight">{weight.toFixed(3)}</span>
						<div class="z-bar" style="width: {(weight / maxWeight * 100).toFixed(1)}%"></div>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	<section class="section">
		<h3 class="section-title">Position Sizes</h3>
		<label class="config-row">
			<span>max_w <span class="c-desc">Max syllables in weak position</span></span>
			<select bind:value={$meterConfig.max_w}>
				{#each [1,2,3,4,5] as n}
					<option value={n}>{n}</option>
				{/each}
			</select>
		</label>
		<label class="config-row">
			<span>max_s <span class="c-desc">Max syllables in strong position</span></span>
			<select bind:value={$meterConfig.max_s}>
				{#each [1,2,3,4,5] as n}
					<option value={n}>{n}</option>
				{/each}
			</select>
		</label>
		<label class="config-row">
			<span>resolve_optionality</span>
			<input type="checkbox" bind:checked={$meterConfig.resolve_optionality} />
		</label>
	</section>
</div>

<style>
	.page {
		max-width: 640px;
	}
	.page-title {
		font-size: 1.1rem;
		font-weight: normal;
		margin-bottom: 0.2rem;
	}
	.page-desc {
		font-size: 0.82rem;
		color: var(--text-muted);
		margin-bottom: 1rem;
	}
	.actions {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	.btn {
		padding: 0.4rem 0.8rem;
		font-size: 0.82rem;
		border: 1px solid var(--border);
		border-radius: 5px;
		background: #fff;
		color: var(--text);
	}
	.btn:hover {
		background: var(--bg-alt);
	}
	.section {
		margin-bottom: 1.5rem;
	}
	.section-title {
		font-size: 0.92rem;
		font-weight: normal;
		color: var(--text-muted);
		border-bottom: 1px solid var(--border);
		padding-bottom: 0.3rem;
		margin-bottom: 0.4rem;
	}
	.badge {
		font-size: 0.7rem;
		background: var(--bar);
		color: #fff;
		padding: 0.1rem 0.4rem;
		border-radius: 3px;
		vertical-align: middle;
	}

	/* Constraint table */
	.constraint-header {
		display: flex;
		align-items: center;
		padding: 0.25rem 0;
		font-size: 0.72rem;
		color: var(--text-dim);
		border-bottom: 1px solid var(--border-light);
	}
	.ch-name { flex: 1; }
	.ch-weight { width: 70px; text-align: center; }
	.ch-on { width: 36px; text-align: center; }

	.constraint-row {
		display: flex;
		align-items: center;
		padding: 0.3rem 0;
		border-bottom: 1px solid var(--border-light);
		font-size: 0.85rem;
	}
	.constraint-row.inactive {
		opacity: 0.4;
	}
	.constraint-row.overridden .c-weight {
		opacity: 0.35;
	}
	.override-note {
		font-size: 0.75rem;
		color: var(--bar);
		font-style: italic;
		margin-bottom: 0.4rem;
		padding: 0.3rem 0.5rem;
		background: #eef4ff;
		border-radius: 4px;
	}
	.c-info {
		flex: 1;
		min-width: 0;
	}
	.c-name {
		font-family: var(--font-mono);
		font-size: 0.82rem;
	}
	.c-desc {
		display: block;
		font-size: 0.7rem;
		color: var(--text-dim);
	}
	.c-weight {
		width: 70px;
		text-align: center;
		font-size: 0.8rem;
		font-family: var(--font-mono);
		padding: 0.15rem 0.25rem;
		border: 1px solid var(--border);
		border-radius: 3px;
		margin: 0 0.3rem;
	}
	.c-weight:disabled {
		background: var(--bg-alt);
		color: var(--text-dim);
	}
	.c-check {
		width: 36px;
		text-align: center;
	}

	/* Zone weights */
	.zone-note {
		font-size: 0.75rem;
		color: var(--text-dim);
		margin-bottom: 0.5rem;
	}
	.zone-row {
		display: flex;
		align-items: center;
		padding: 0.2rem 0;
		font-size: 0.82rem;
		gap: 0.5rem;
	}
	.z-name {
		width: 180px;
		font-family: var(--font-mono);
		font-size: 0.78rem;
	}
	.z-weight {
		width: 60px;
		font-family: var(--font-mono);
		font-size: 0.78rem;
		text-align: right;
	}
	.z-bar {
		flex: 1;
		height: 12px;
		background: var(--bar);
		border-radius: 2px;
		min-width: 2px;
	}

	/* Position sizes */
	.config-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.35rem 0;
		border-bottom: 1px solid var(--border-light);
		font-size: 0.88rem;
		cursor: pointer;
	}
	.config-row select {
		font-size: 0.85rem;
		padding: 0.15rem 0.3rem;
		border: 1px solid var(--border);
		border-radius: 4px;
	}
</style>
