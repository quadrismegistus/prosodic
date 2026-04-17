<script>
	import { parseExport } from '$lib/api.js';
	import { inputText, meterConfig, constraintWeights, zoneWeights, maxentConfig, settings } from '$lib/stores.js';
	import { Download } from 'lucide-svelte';

	let { rows = [], elapsed = 0, numLines = 0, constraints = [], onLineClick = null } = $props();
	let viewMode = $state('best');
	let sortCol = $state(null);
	let sortAsc = $state(true);
	let currentPage = $state(1);
	let pageSize = $state(100);
	let exporting = $state(false);
	let exportMenuOpen = $state(false);
	let normalize = $state(false);

	function fmt(val, row) {
		if (val == null) return '';
		if (!normalize || !row.num_sylls) return val;
		return (val * 10 / row.num_sylls).toFixed(1);
	}

	function violVal(row, c) {
		if (!row.viols) return 0;
		return row.viols[c] || 0;
	}

	function sortKey(row, col) {
		if (col === 'num_sylls' || col === 'num_viols' || col === 'score' || col === 'num_unbounded') {
			return row[col] ?? 0;
		}
		if (col.startsWith('*')) {
			return violVal(row, col.slice(1));
		}
		return row[col];
	}

	function buildPayload() {
		const constraints = $zoneWeights
			? $meterConfig.constraints
			: $meterConfig.constraints.map(c => {
				const w = $constraintWeights[c];
				return (w != null && w !== 1.0) ? `${c}/${w}` : c;
			});
		const payload = {
			text: $inputText,
			constraints,
			max_s: $meterConfig.max_s,
			max_w: $meterConfig.max_w,
			resolve_optionality: $meterConfig.resolve_optionality,
			syntax: $settings.syntax,
			syntax_model: $settings.syntax_model,
		};
		if ($zoneWeights) {
			payload.zone_weights = $zoneWeights;
			payload.zones = $maxentConfig.zones;
		}
		return payload;
	}

	async function doExport(format) {
		exportMenuOpen = false;
		exporting = true;
		try {
			await parseExport(buildPayload(), format);
		} catch (e) {
			alert(`Export failed: ${e.message}`);
		} finally {
			exporting = false;
		}
	}

	function downloadWeights() {
		exportMenuOpen = false;
		const lines = ['constraint,zone,weight'];

		if ($zoneWeights) {
			// Zone weights active: export per-zone + mean per constraint
			const byBase = {};
			const entries = [];
			for (const [k, w] of Object.entries($zoneWeights)) {
				const match = k.match(/^(.+?)_(z\d+)$/);
				if (match) {
					const [, base, zone] = match;
					entries.push({ constraint: base, zone, weight: w });
					if (!byBase[base]) byBase[base] = [];
					byBase[base].push(w);
				} else {
					entries.push({ constraint: k, zone: '', weight: w });
				}
			}
			for (const [base, vals] of Object.entries(byBase)) {
				const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
				entries.push({ constraint: base, zone: 'mean', weight: parseFloat(mean.toFixed(4)) });
			}
			entries.sort((a, b) => b.weight - a.weight);
			for (const e of entries) {
				lines.push(`${e.constraint},${e.zone},${e.weight}`);
			}
		} else {
			const entries = $meterConfig.constraints.map(c => ({
				constraint: c, weight: $constraintWeights[c] ?? 1.0
			}));
			entries.sort((a, b) => b.weight - a.weight);
			for (const e of entries) {
				lines.push(`${e.constraint},,${e.weight}`);
			}
		}

		const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'prosodic-weights.csv';
		document.body.appendChild(a);
		a.click();
		a.remove();
		URL.revokeObjectURL(url);
	}

	function toggleSort(col) {
		if (sortCol === col) {
			sortAsc = !sortAsc;
		} else {
			sortCol = col;
			sortAsc = true;
		}
		currentPage = 1;
	}

	let filteredRows = $derived.by(() => {
		let filtered = viewMode === 'best'
			? rows.filter(r => r.rank === 1)
			: rows;
		if (sortCol) {
			filtered = [...filtered].sort((a, b) => {
				let va = sortKey(a, sortCol), vb = sortKey(b, sortCol);
				if (typeof va === 'string') {
					return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
				}
				return sortAsc ? (va - vb) : (vb - va);
			});
		}
		return filtered;
	});

	let totalPages = $derived(Math.max(1, Math.ceil(filteredRows.length / pageSize)));
	let pagedRows = $derived(filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize));

	// Reset page when rows change
	$effect(() => {
		rows;
		currentPage = 1;
	});

	function sortIndicator(col) {
		if (sortCol !== col) return '';
		return sortAsc ? ' \u25B2' : ' \u25BC';
	}

	function goPage(p) {
		currentPage = Math.max(1, Math.min(p, totalPages));
	}
</script>

{#if rows.length > 0}
	<div class="header-row">
		<span class="stat">Parsed {numLines} lines in {elapsed.toFixed(2)}s ({rows.filter(r => r.rank === 1).length} best, {rows.length} total)</span>
		<div class="toggle-row">
			<button class="toggle-btn" class:active={viewMode === 'best'}
				onclick={() => { viewMode = 'best'; currentPage = 1; }}>Best only</button>
			<button class="toggle-btn" class:active={viewMode === 'unbounded'}
				onclick={() => { viewMode = 'unbounded'; currentPage = 1; }}>All unbounded</button>
		</div>
		<div class="export-wrap">
			<button class="export-btn" onclick={() => exportMenuOpen = !exportMenuOpen} disabled={exporting} title="Export all unbounded parses">
				<Download size={14} strokeWidth={1.75} />
				{exporting ? 'Exporting…' : 'Export'}
			</button>
			{#if exportMenuOpen}
				<div class="export-menu" role="menu">
					<button onclick={() => doExport('csv')}>Parses (CSV)</button>
					<button onclick={() => doExport('tsv')}>Parses (TSV)</button>
					<button onclick={() => doExport('json')}>Parses (JSON)</button>
					<hr />
					<button onclick={downloadWeights}>Weights (CSV)</button>
				</div>
			{/if}
		</div>
		<label class="norm-toggle" title="Normalize counts per 10 syllables">
			<input type="checkbox" bind:checked={normalize} />
			<span>per 10σ</span>
		</label>
		<span class="legend">
			<span class="mtr_s">over</span>line = strong &nbsp;
			<span class="str_s">bold</span> = stressed &nbsp;
			<span class="viol_y">red</span> = violation
		</span>
	</div>

	{#if totalPages > 1}
		<div class="pagination">
			<button class="pg-btn" disabled={currentPage <= 1} onclick={() => goPage(1)}>&laquo;</button>
			<button class="pg-btn" disabled={currentPage <= 1} onclick={() => goPage(currentPage - 1)}>&lsaquo;</button>
			<span class="pg-info">Page {currentPage} of {totalPages}
				<span class="pg-detail">({filteredRows.length} rows, {pageSize}/page)</span>
			</span>
			<button class="pg-btn" disabled={currentPage >= totalPages} onclick={() => goPage(currentPage + 1)}>&rsaquo;</button>
			<button class="pg-btn" disabled={currentPage >= totalPages} onclick={() => goPage(totalPages)}>&raquo;</button>
			<select class="pg-size" bind:value={pageSize} onchange={() => currentPage = 1}>
				<option value={50}>50</option>
				<option value={100}>100</option>
				<option value={250}>250</option>
				<option value={500}>500</option>
			</select>
		</div>
	{/if}

	<div class="table-wrap">
		<table>
			<thead>
				<tr>
					<th class="sortable" onclick={() => toggleSort('line_num')}>Line{sortIndicator('line_num')}</th>
					<th>Parse</th>
					<th class="sortable" onclick={() => toggleSort('meter_str')}>Meter{sortIndicator('meter_str')}</th>
					<th class="sortable num-col" onclick={() => toggleSort('num_sylls')}>σ{sortIndicator('num_sylls')}</th>
					<th class="sortable num-col" onclick={() => toggleSort('score')}>Score{sortIndicator('score')}</th>
					<th class="sortable num-col" onclick={() => toggleSort('num_viols')}>Viols{sortIndicator('num_viols')}</th>
					<th class="sortable num-col" onclick={() => toggleSort('num_unbounded')}>Ambig{sortIndicator('num_unbounded')}</th>
					{#each constraints as c}
						<th class="sortable num-col constraint-col" onclick={() => toggleSort('*' + c)} title={c}>*{c}{sortIndicator('*' + c)}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each pagedRows as row (row.line_num + '-' + row.rank)}
					<tr class:best={row.rank === 1} class:other={row.rank !== 1} class:clickable={row.rank === 1 && onLineClick}
						onclick={() => row.rank === 1 && onLineClick && onLineClick(row)}>
						<td>
							{row.line_num}
							{#if row.num_parts && row.num_parts > 1}
								<span class="parts-badge" title="Line parsed as {row.num_parts} lineparts">·{row.num_parts}</span>
							{/if}
						</td>
						<td class="parse-text">{@html row.parse_html}</td>
						<td class="stat meter-cell">{@html row.meter_str}</td>
						<td class="stat num-col">{row.num_sylls || ''}</td>
						<td class="stat num-col">{fmt(row.score, row)}</td>
						<td class="stat num-col">{fmt(row.num_viols, row)}</td>
						<td class="stat num-col">{row.rank === 1 ? row.num_unbounded : ''}</td>
						{#each constraints as c}
							<td class="stat num-col constraint-col">{#if row.viols}{fmt(violVal(row, c), row)}{/if}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	{#if totalPages > 1}
		<div class="pagination bottom">
			<button class="pg-btn" disabled={currentPage <= 1} onclick={() => goPage(1)}>&laquo;</button>
			<button class="pg-btn" disabled={currentPage <= 1} onclick={() => goPage(currentPage - 1)}>&lsaquo;</button>
			<span class="pg-info">Page {currentPage} of {totalPages}</span>
			<button class="pg-btn" disabled={currentPage >= totalPages} onclick={() => goPage(currentPage + 1)}>&rsaquo;</button>
			<button class="pg-btn" disabled={currentPage >= totalPages} onclick={() => goPage(totalPages)}>&raquo;</button>
		</div>
	{/if}
{/if}

<style>
	.header-row {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
		padding: 0.25rem 0;
	}
	.stat {
		font-size: 0.75rem;
		color: var(--text-dim);
		font-family: var(--font-mono);
	}
	.toggle-row {
		display: flex;
		gap: 0.3rem;
	}
	.toggle-btn {
		padding: 0.25rem 0.6rem;
		font-size: 0.78rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		background: #fff;
		color: var(--text);
	}
	.toggle-btn.active {
		background: var(--accent);
		color: #fff;
		border-color: var(--accent);
	}
	.norm-toggle {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.78rem;
		color: var(--text-dim);
		cursor: pointer;
		user-select: none;
	}
	.norm-toggle input { margin: 0; }
	.legend {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-left: auto;
	}
	.num-col {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.constraint-col {
		font-size: 0.7rem;
		max-width: 60px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.export-wrap {
		position: relative;
	}
	.export-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.25rem 0.6rem;
		font-size: 0.78rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		background: #fff;
		color: var(--text);
		cursor: pointer;
	}
	.export-btn:hover:not(:disabled) {
		background: var(--bg-alt);
	}
	.export-btn:disabled {
		opacity: 0.6;
		cursor: wait;
	}
	.export-menu {
		position: absolute;
		top: calc(100% + 4px);
		right: 0;
		background: #fff;
		border: 1px solid var(--border);
		border-radius: 4px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.08);
		z-index: 50;
		min-width: 80px;
		display: flex;
		flex-direction: column;
	}
	.export-menu button {
		padding: 0.4rem 0.75rem;
		font-size: 0.82rem;
		text-align: left;
		background: none;
		border: none;
		cursor: pointer;
		font-family: var(--font);
	}
	.export-menu button:hover {
		background: var(--bg-alt);
	}
	.export-menu hr {
		margin: 0.15rem 0;
		border: none;
		border-top: 1px solid var(--border-light);
	}
	.legend :global(.mtr_s) { text-decoration: overline; color: var(--text); }
	.legend .str_s { font-weight: 600; color: var(--text); }
	.legend .viol_y { color: var(--violation); }

	/* Pagination */
	.pagination {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.4rem 0;
		font-size: 0.82rem;
	}
	.pagination.bottom {
		border-top: 1px solid var(--border-light);
		margin-top: 0.25rem;
		padding-top: 0.5rem;
	}
	.pg-btn {
		padding: 0.2rem 0.5rem;
		border: 1px solid var(--border);
		border-radius: 3px;
		background: #fff;
		font-size: 0.85rem;
		color: var(--text);
		line-height: 1;
	}
	.pg-btn:hover:not(:disabled) {
		background: var(--bg-alt);
	}
	.pg-btn:disabled {
		opacity: 0.3;
		cursor: default;
	}
	.pg-info {
		font-family: var(--font-mono);
		font-size: 0.78rem;
		color: var(--text-muted);
		padding: 0 0.3rem;
	}
	.pg-detail {
		color: var(--text-dim);
		font-size: 0.7rem;
	}
	.pg-size {
		margin-left: auto;
		font-size: 0.78rem;
		padding: 0.15rem 0.3rem;
		border: 1px solid var(--border);
		border-radius: 3px;
		font-family: var(--font-mono);
	}

	.table-wrap {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.92rem;
	}
	th {
		text-align: left;
		padding: 0.5rem;
		border-bottom: 2px solid var(--border);
		font-weight: normal;
		font-size: 0.78rem;
		color: var(--text-muted);
		white-space: nowrap;
	}
	th.sortable {
		cursor: pointer;
		user-select: none;
	}
	th.sortable:hover {
		color: var(--text);
	}
	td {
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid var(--border-light);
		vertical-align: top;
	}
	tr.other td {
		opacity: 0.35;
	}
	tr.other:hover td {
		opacity: 0.8;
	}
	tr.clickable {
		cursor: pointer;
	}
	tr.clickable:hover td {
		background: #f0f7ff;
	}

	.parts-badge {
		display: inline-block;
		margin-left: 0.2rem;
		padding: 1px 5px;
		font-size: 0.65rem;
		color: var(--text-dim);
		background: var(--bg-alt);
		border-radius: 3px;
		vertical-align: middle;
	}
	:global(.part-sep) {
		color: var(--text-dim);
		font-weight: 300;
		padding: 0 0.3rem;
	}
	:global(.unparsed) {
		color: var(--text-dim);
		font-style: italic;
	}

	/* Parse rendering styles (server-rendered HTML) */
	.parse-text {
		line-height: 2.2em;
		white-space: normal;
		max-width: 700px;
		min-width: 320px;
	}
	.meter-cell {
		white-space: nowrap;
		vertical-align: top;
	}
	:global(.mtr_s) {
		text-decoration: overline;
	}
	:global(.str_s) {
		font-weight: 600;
	}
	:global(.viol_y) {
		color: var(--violation);
		text-decoration-color: var(--violation);
		cursor: pointer;
		position: relative;
	}
	:global(.viol_y .tip) {
		display: none;
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%);
		background: var(--accent);
		color: #fff;
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.72rem;
		white-space: nowrap;
		z-index: 10;
		font-weight: normal;
		font-family: var(--font-mono);
		pointer-events: none;
	}
	:global(.viol_y:hover .tip) {
		display: block;
	}

	@media (max-width: 768px) {
		.legend { display: none; }
	}
</style>
