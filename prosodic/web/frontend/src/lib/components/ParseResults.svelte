<script>
	let { rows = [], elapsed = 0, numLines = 0, onLineClick = null } = $props();
	let viewMode = $state('best');
	let sortCol = $state(null);
	let sortAsc = $state(true);
	let currentPage = $state(1);
	let pageSize = $state(100);

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
				let va = a[sortCol], vb = b[sortCol];
				if (typeof va === 'string') {
					return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
				}
				return sortAsc ? va - vb : vb - va;
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
					<th class="sortable" onclick={() => toggleSort('score')}>Score{sortIndicator('score')}</th>
					<th class="sortable" onclick={() => toggleSort('num_unbounded')}>Ambig{sortIndicator('num_unbounded')}</th>
				</tr>
			</thead>
			<tbody>
				{#each pagedRows as row (row.line_num + '-' + row.rank)}
					<tr class:best={row.rank === 1} class:other={row.rank !== 1} class:clickable={row.rank === 1 && onLineClick}
						onclick={() => row.rank === 1 && onLineClick && onLineClick(row)}>
						<td>{row.line_num}</td>
						<td class="parse-text">{@html row.parse_html}</td>
						<td class="stat">{row.meter_str}</td>
						<td class="stat">{row.score}</td>
						<td class="stat">{row.rank === 1 ? row.num_unbounded : ''}</td>
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
	.legend {
		font-size: 0.78rem;
		color: var(--text-dim);
		margin-left: auto;
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

	/* Parse rendering styles (server-rendered HTML) */
	.parse-text {
		line-height: 2.2em;
		white-space: nowrap;
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
