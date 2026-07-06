<script>
	// rows: grid_data() JSON from /api/parse/line (txt, meter, height, level,
	// color, phrasal, viol). palette/levelNames: LEVEL_PALETTE/LEVEL_NAMES,
	// index h-1 = color/name for height h — boxes stack bottom-up from level
	// 1 to each syllable's height.
	let { rows = [], palette = [], levelNames = [] } = $props();

	const boxSize = 18;
	const gap = 2;
	const maxHeight = $derived(rows.length ? Math.max(...rows.map((r) => r.height)) : 0);
	const stackHeight = $derived(maxHeight * boxSize + Math.max(maxHeight - 1, 0) * gap);

	function levelsOf(row) {
		return Array.from({ length: row.height }, (_, i) => row.height - i);
	}
</script>

{#if rows.length > 0}
	<div class="metrical-grid">
		{#each rows as row}
			<div class="col">
				<div class="boxes" style="height: {stackHeight}px; gap: {gap}px">
					{#each levelsOf(row) as level}
						<div
							class="box"
							style="height: {boxSize}px; background: {palette[level - 1] ?? row.color}"
							title="{row.level}{row.phrasal != null ? ` (phrasal ${row.phrasal.toFixed(2)})` : ''}"
						></div>
					{/each}
				</div>
				<div class="txt">{row.txt}</div>
				<div class="meter" class:viol={row.viol}>{row.meter}{row.viol ? '*' : ''}</div>
			</div>
		{/each}
	</div>
	{#if palette.length > 0 && levelNames.length === palette.length}
		<div class="legend">
			{#each levelNames as name, i}
				<span class="legend-item">
					<span class="swatch" style="background: {palette[i]}"></span>{name}
				</span>
			{/each}
		</div>
	{/if}
{/if}

<style>
	.metrical-grid {
		display: flex;
		align-items: flex-end;
		gap: 0.4rem;
		padding: 0.75rem 0;
		overflow-x: auto;
	}
	.col {
		display: flex;
		flex-direction: column;
		align-items: center;
		flex: 0 0 auto;
	}
	.boxes {
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		width: 20px;
	}
	.box {
		width: 100%;
		border-radius: 2px;
	}
	.txt {
		font-size: 0.85rem;
		white-space: nowrap;
		margin-top: 0.3rem;
		color: var(--text);
	}
	.meter {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-dim);
		margin-top: 0.1rem;
	}
	.meter.viol {
		color: var(--violation);
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		font-size: 0.72rem;
		color: var(--text-dim);
		padding-bottom: 0.5rem;
	}
	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
	}
	.swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
	}
</style>
