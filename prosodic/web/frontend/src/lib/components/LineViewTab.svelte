<script>
	import { parseLine } from '$lib/api.js';
	import { selectedLine, meterConfig, constraintWeights, zoneWeights, maxentConfig } from '$lib/stores.js';

	let lineInput = $state('');
	let parses = $state([]);
	let parts = $state([]);
	let lineText = $state('');
	let loading = $state(false);
	let error = $state('');
	let elapsed = $state(0);
	let numUnbounded = $state(0);

	// When selectedLine changes, auto-parse it
	$effect(() => {
		const sel = $selectedLine;
		if (sel && sel.line_text) {
			lineInput = sel.line_text;
			handleParse(sel.line_text);
		}
	});

	function buildConstraintList() {
		if ($zoneWeights) {
			return $meterConfig.constraints;
		}
		return $meterConfig.constraints.map(c => {
			const w = $constraintWeights[c];
			return (w != null && w !== 1.0) ? `${c}/${w}` : c;
		});
	}

	async function handleParse(text) {
		const t = (text || lineInput).trim();
		if (!t) return;
		loading = true;
		error = '';
		parses = [];
		try {
			const payload = {
				text: t,
				constraints: buildConstraintList(),
				max_s: $meterConfig.max_s,
				max_w: $meterConfig.max_w,
				resolve_optionality: $meterConfig.resolve_optionality
			};
			if ($zoneWeights) {
				payload.zone_weights = $zoneWeights;
				payload.zones = $maxentConfig.zones;
			}
			const res = await parseLine(payload);
			parses = res.parses || [];
			parts = res.parts || [];
			lineText = res.line_text || t;
			elapsed = res.elapsed || 0;
			numUnbounded = res.num_unbounded || 0;
		} catch (e) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	function handleKeydown(e) {
		if (e.key === 'Enter') {
			$selectedLine = null;
			handleParse();
		}
	}
</script>

<div class="page">
	<h2 class="page-title">Line View</h2>
	<p class="page-desc">Detailed analysis of a single line. Click a line in Parse results or type one below.</p>

	<div class="input-row">
		<input
			type="text"
			class="line-input"
			placeholder="Enter a line of verse..."
			bind:value={lineInput}
			onkeydown={handleKeydown}
		/>
		<button class="parse-btn" onclick={() => { $selectedLine = null; handleParse(); }} disabled={loading}>
			{loading ? 'Parsing...' : 'Parse'}
		</button>
	</div>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	{#if parses.length > 0}
		<div class="line-header">
			<span class="line-text">{lineText}</span>
			<span class="meta">{numUnbounded} unbounded, {parses.length - numUnbounded} bounded ({parses.length} total) in {elapsed.toFixed(2)}s</span>
		</div>

		{@render parseTable(parses)}

	{:else if parts.length > 0}
		<div class="line-header">
			<span class="line-text">{lineText}</span>
			<span class="meta">{parts.length} parts, {elapsed.toFixed(2)}s</span>
		</div>

		{#each parts as part, pi}
			{#if part.parses.length > 0}
				<div class="part-header">
					<span class="part-label">Part {pi + 1}</span>
					<span class="part-text">{part.part_text}</span>
					<span class="meta">{part.num_sylls}σ, {part.num_unbounded} unbounded, {part.num_parses} total</span>
				</div>
				{@render parseTable(part.parses)}
			{:else if part.num_sylls > 0}
				<div class="part-header unparsed-part">
					<span class="part-label">Part {pi + 1}</span>
					<span class="part-text">{part.part_text}</span>
					<span class="meta">{part.num_sylls}σ — too long to parse exhaustively</span>
				</div>
			{/if}
		{/each}

	{:else if !loading && lineInput}
		<div class="empty">Press Enter or click Parse to analyze</div>
	{:else if !loading}
		<div class="empty">Click a line in Parse results or type a line above</div>
	{/if}

	{#snippet parseTable(items)}
		<div class="table-wrap">
			<table>
				<thead>
					<tr>
						<th class="rank-col">#</th>
						<th>Scansion</th>
						<th class="meter-col">Meter</th>
						<th class="score-col">Score</th>
						<th>Violations</th>
					</tr>
				</thead>
				<tbody>
					{#each items as p, i}
						<tr class:best={p.rank === 1} class:bounded={p.is_bounded}>
							<td class="rank-col">{p.rank}</td>
							<td class="parse-text">{@html p.parse_html}</td>
							<td class="meter-col mono">{p.meter_str}</td>
							<td class="score-col mono">{p.score}</td>
							<td class="viol-col">
								{#if Object.keys(p.viol_summary).length > 0}
									{#each Object.entries(p.viol_summary) as [name, count]}
										<span class="viol-badge">*{name}<span class="viol-count">{count}</span></span>
									{/each}
								{:else}
									<span class="no-viols">none</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/snippet}
</div>

<style>
	.page {
		max-width: 100%;
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
	.input-row {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	.line-input {
		flex: 1;
		padding: 0.5rem 0.75rem;
		font-size: 0.95rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		font-family: var(--font);
	}
	.line-input:focus {
		outline: none;
		border-color: var(--accent);
	}
	.parse-btn {
		padding: 0.5rem 1.2rem;
		font-size: 0.95rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 6px;
		white-space: nowrap;
	}
	.parse-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}
	.parse-btn:disabled {
		opacity: 0.7;
	}
	.line-header {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: 0.5rem;
		padding: 0.5rem 0;
		border-bottom: 1px solid var(--border);
	}
	.line-text {
		font-size: 1rem;
		font-style: italic;
		color: var(--text);
	}
	.meta {
		font-size: 0.75rem;
		color: var(--text-dim);
		font-family: var(--font-mono);
	}
	.error {
		color: var(--violation);
		font-size: 0.88rem;
		padding: 0.5rem 0;
	}
	.empty {
		color: var(--text-dim);
		text-align: center;
		padding: 3rem;
		font-style: italic;
	}
	.table-wrap {
		overflow-x: auto;
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
		font-size: 0.75rem;
		color: var(--text-muted);
		white-space: nowrap;
	}
	td {
		padding: 0.35rem 0.5rem;
		border-bottom: 1px solid var(--border-light);
		vertical-align: top;
	}
	.rank-col { width: 36px; text-align: center; }
	.meter-col { white-space: nowrap; }
	.score-col { width: 60px; text-align: right; }
	.mono {
		font-family: var(--font-mono);
		font-size: 0.82rem;
		color: var(--text-dim);
	}
	tr.best td {
		background: #f8fdf8;
	}
	tr.best .rank-col {
		font-weight: 600;
		color: var(--accent);
	}
	tr.bounded td {
		opacity: 0.3;
	}
	tr.bounded:hover td {
		opacity: 0.7;
	}

	/* Parse rendering */
	.parse-text {
		line-height: 2.2em;
		white-space: nowrap;
	}
	:global(.mtr_s) { text-decoration: overline; }
	:global(.str_s) { font-weight: 600; }
	:global(.viol_y) {
		color: var(--violation);
		text-decoration-color: var(--violation);
	}

	/* Violation badges */
	.viol-col {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}
	.viol-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.15rem;
		font-size: 0.72rem;
		font-family: var(--font-mono);
		color: var(--violation);
		background: #fff5f5;
		padding: 0.1rem 0.35rem;
		border-radius: 3px;
		border: 1px solid #fdd;
	}
	.viol-count {
		font-size: 0.65rem;
		background: var(--violation);
		color: #fff;
		padding: 0 0.25rem;
		border-radius: 2px;
		min-width: 14px;
		text-align: center;
	}
	.no-viols {
		font-size: 0.72rem;
		color: var(--text-dim);
		font-style: italic;
	}
	.part-header {
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
		padding: 0.5rem 0 0.25rem;
		border-bottom: 1px solid var(--border-light);
		margin-top: 1rem;
	}
	.part-label {
		font-size: 0.72rem;
		font-weight: 600;
		color: var(--accent);
		text-transform: uppercase;
	}
	.part-text {
		font-style: italic;
		font-size: 0.92rem;
	}
	.unparsed-part {
		opacity: 0.5;
	}
</style>
