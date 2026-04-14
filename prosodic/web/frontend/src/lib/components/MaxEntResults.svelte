<script>
	let { result } = $props();

	function maxWeight(weights) {
		if (!weights || weights.length === 0) return 1;
		return weights[0].weight;
	}
</script>

{#if result}
	<div class="stats">
		<div class="stat-row">
			<span class="stat-label">Trained on</span>
			<span class="stat-value">{result.num_lines} lines</span>
		</div>
		{#if result.accuracy != null}
			<div class="stat-row accent">
				<span class="stat-label">Accuracy</span>
				<span class="stat-value">{(result.accuracy * 100).toFixed(1)}%
					<span class="detail">({result.num_matched}/{result.num_lines} correct)</span>
				</span>
			</div>
		{/if}
		{#if result.log_likelihood != null}
			<div class="stat-row">
				<span class="stat-label">Log-likelihood</span>
				<span class="stat-value">{result.log_likelihood.toFixed(2)}</span>
			</div>
		{/if}
		<div class="stat-row">
			<span class="stat-label">Config</span>
			<span class="stat-value detail">
				{result.config.target !== '(from annotations)'
					? `target: ${result.config.target}`
					: 'from annotations'},
				zones: {result.config.zones},
				reg: {result.config.regularization}
			</span>
		</div>
		<div class="stat-row">
			<span class="stat-label">Time</span>
			<span class="stat-value">{result.elapsed.toFixed(2)}s</span>
		</div>
	</div>

	{#if result.weights.length > 0}
		<h3 class="weights-title">Learned Weights</h3>
		<table>
			<thead>
				<tr><th>Constraint</th><th>Weight</th><th></th></tr>
			</thead>
			<tbody>
				{#each result.weights as w}
					<tr>
						<td>{w.name}</td>
						<td class="mono">{w.weight.toFixed(3)}</td>
						<td class="bar-cell">
							<div class="bar" style="width: {(w.weight / maxWeight(result.weights) * 100).toFixed(0)}%"></div>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<div class="empty">No weights learned (all zero)</div>
	{/if}
{/if}

<style>
	.stats {
		background: var(--bg-alt);
		border-radius: 6px;
		padding: 0.6rem 0.8rem;
		margin-bottom: 0.75rem;
	}
	.stat-row {
		display: flex;
		justify-content: space-between;
		padding: 0.2rem 0;
		font-size: 0.82rem;
	}
	.stat-row.accent {
		font-weight: 600;
		font-size: 0.9rem;
		padding: 0.3rem 0;
	}
	.stat-label {
		color: var(--text-muted);
	}
	.stat-value {
		font-family: var(--font-mono);
		color: var(--text);
	}
	.detail {
		font-weight: normal;
		font-size: 0.75rem;
		color: var(--text-dim);
	}
	.weights-title {
		font-size: 0.85rem;
		font-weight: normal;
		color: var(--text-muted);
		margin-bottom: 0.3rem;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.88rem;
	}
	th {
		text-align: left;
		padding: 0.4rem 0.5rem;
		border-bottom: 2px solid var(--border);
		font-weight: normal;
		font-size: 0.78rem;
		color: var(--text-muted);
	}
	td {
		padding: 0.3rem 0.5rem;
		border-bottom: 1px solid var(--border-light);
	}
	.mono {
		font-family: var(--font-mono);
		font-size: 0.82rem;
	}
	.bar-cell {
		width: 40%;
	}
	.bar {
		background: var(--bar);
		height: 14px;
		border-radius: 3px;
		min-width: 2px;
	}
	.empty {
		color: var(--text-dim);
		text-align: center;
		padding: 2rem;
		font-style: italic;
	}
</style>
