<script>
	// Combined Liberman & Prince (1977)-style figure: metrical grid above the
	// words, phrasal/syntax tree hanging below (root at the bottom, leaves
	// pinned to the word row) — one shared x-axis. Grid columns are
	// per-syllable; tree leaves are per-word, so a multi-syllable word's leaf
	// is centered over (and can span) its own syllable columns via word_num.
	//
	// rows: grid_data() JSON (txt, meter, height, level, color, phrasal,
	// viol, word_num). palette/levelNames: LEVEL_PALETTE/LEVEL_NAMES. tree:
	// optional tree_to_dict() JSON — when absent, only the grid renders.
	let { rows = [], palette = [], levelNames = [], tree = null } = $props();

	const xSpacing = 46;
	const boxSize = 16;
	const boxGap = 2;
	const wordRowH = 22;
	const meterRowH = 16;
	const tagRowH = 22;
	const treeRowH = 34;
	const margin = 16;

	function hexToRgb(hex) {
		const n = parseInt(hex.slice(1), 16);
		return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
	}
	function rgbToHex([r, g, b]) {
		return '#' + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
	}
	function tstressColor(stops, t) {
		if (!stops.length) return '#94a3b8';
		if (t == null) return '#e2e8f0';
		const clamped = Math.max(0, Math.min(1, t));
		const pos = clamped * (stops.length - 1);
		const i = Math.floor(pos);
		const frac = pos - i;
		const a = hexToRgb(stops[i]);
		const b = hexToRgb(stops[Math.min(i + 1, stops.length - 1)]);
		return rgbToHex(a.map((v, k) => v + (b[k] - v) * frac));
	}

	function levelsOf(row) {
		return Array.from({ length: row.height }, (_, i) => row.height - i);
	}

	// One column per syllable, plus word groupings (contiguous same word_num
	// runs) so tree leaves can be centered over their word's syllable span.
	const scene = $derived.by(() => {
		const maxHeight = rows.length ? Math.max(...rows.map((r) => r.height)) : 0;
		const gridAreaH = maxHeight * boxSize + Math.max(maxHeight - 1, 0) * boxGap;

		const cols = rows.map((r, i) => ({ ...r, x: i * xSpacing }));

		const words = [];
		for (const c of cols) {
			const last = words[words.length - 1];
			if (last && last.word_num === c.word_num && c.word_num != null) {
				last.xEnd = c.x;
			} else {
				words.push({ word_num: c.word_num, xStart: c.x, xEnd: c.x });
			}
		}
		const wordSpans = new Map(
			words.map((w) => [w.word_num, { ...w, xCenter: (w.xStart + w.xEnd) / 2 }])
		);

		let treeScene = null;
		if (tree) {
			let maxDepth = 0;
			const nodes = [];
			const edges = [];
			let fallbackI = 0;

			function visit(node, depth) {
				maxDepth = Math.max(maxDepth, depth);
				const isLeaf = !node.children || node.children.length === 0;
				const rec = { tag: node.tag, tstress: node.tstress, isLeaf, depth };
				if (isLeaf) {
					const span = wordSpans.get(node.word_num);
					rec.x = span ? span.xCenter : fallbackI * xSpacing;
					fallbackI += 1;
					nodes.push(rec);
					return rec;
				}
				const childRecs = node.children.map((c) => visit(c, depth + 1));
				rec.x = childRecs.reduce((s, c) => s + c.x, 0) / childRecs.length;
				nodes.push(rec);
				for (const c of childRecs) edges.push({ parent: rec, child: c });
				return rec;
			}
			visit(tree, 0);

			// leaves pinned to the top of the tree area (row 0, right under
			// the word/tag rows); root sinks to the bottom — the L&P hang
			for (const n of nodes) {
				n.y = n.isLeaf ? 0 : (maxDepth - n.depth) * treeRowH;
			}
			treeScene = { nodes, edges, maxDepth, height: maxDepth * treeRowH + 8 };
		}

		const width = cols.length ? (cols.length - 1) * xSpacing + margin * 2 + xSpacing : margin * 2;
		const gridTop = margin;
		const wordY = gridTop + gridAreaH + 12;
		const meterY = wordY + meterRowH;
		const tagY = meterY + 8;
		const treeTop = tagY + tagRowH;
		const height = treeTop + (treeScene ? treeScene.height : 0) + margin;

		return { cols, wordSpans, gridAreaH, gridTop, wordY, meterY, tagY, treeTop, treeScene, width, height };
	});
</script>

{#if rows.length > 0}
	<div class="metrical-grid-tree">
		<svg width={scene.width} height={scene.height}>
			<g transform="translate({margin}, 0)">
				<!-- grid boxes -->
				{#each scene.cols as col}
					{#each levelsOf(col) as level, li}
						<rect
							x={col.x - boxSize / 2}
							y={scene.gridTop + scene.gridAreaH - (levelsOf(col).length - li) * (boxSize + boxGap)}
							width={boxSize}
							height={boxSize}
							rx="2"
							fill={palette[level - 1] ?? col.color}
						>
							<title>{col.level}{col.phrasal != null ? ` (phrasal ${col.phrasal.toFixed(2)})` : ''}</title>
						</rect>
					{/each}
					<!-- syllable text -->
					<text x={col.x} y={scene.wordY} class="syll-txt">{col.txt}</text>
					<!-- meter row -->
					<text x={col.x} y={scene.meterY} class="meter-txt" class:viol={col.viol}>
						{col.meter}{col.viol ? '*' : ''}
					</text>
				{/each}

				<!-- per-word tag row + tree, only when a tree is available -->
				{#if scene.treeScene}
					{#each scene.treeScene.nodes as n}
						{#if n.isLeaf}
							<g transform="translate({n.x}, {scene.tagY})">
								<rect x="-14" y="0" width="28" height="14" rx="3" fill={tstressColor(palette, n.tstress)} />
								<text x="0" y="10" class="tag-txt">{n.tag}</text>
							</g>
						{/if}
					{/each}
					<g transform="translate(0, {scene.treeTop})">
						{#each scene.treeScene.edges as e}
							<line
								x1={e.parent.x}
								y1={e.parent.y + (e.parent.depth === 0 ? 0 : 6)}
								x2={e.child.x}
								y2={e.child.y + (e.child.isLeaf ? 0 : -6)}
								class="edge"
							/>
						{/each}
						{#each scene.treeScene.nodes as n}
							{#if !n.isLeaf}
								<text x={n.x} y={n.y + (n.depth === 0 ? 10 : 4)} class="phrase-txt">{n.tag}</text>
							{/if}
						{/each}
					</g>
				{/if}
			</g>
		</svg>
		{#if palette.length > 0 && levelNames.length === palette.length}
			<div class="legend">
				{#each levelNames as name, i}
					<span class="legend-item"><span class="swatch" style="background: {palette[i]}"></span>{name}</span>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<style>
	.metrical-grid-tree {
		overflow-x: auto;
		padding: 0.5rem 0;
	}
	.syll-txt {
		font-family: var(--font);
		font-size: 12px;
		fill: var(--text);
		text-anchor: middle;
	}
	.meter-txt {
		font-family: var(--font-mono);
		font-size: 11px;
		fill: var(--text-dim);
		text-anchor: middle;
	}
	.meter-txt.viol {
		fill: var(--violation);
	}
	.tag-txt {
		font-family: var(--font-mono);
		font-size: 9px;
		fill: #fff;
		text-anchor: middle;
	}
	.phrase-txt {
		font-family: var(--font-mono);
		font-size: 11px;
		fill: var(--text-muted);
		text-anchor: middle;
	}
	.edge {
		stroke: var(--border);
		stroke-width: 1;
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		font-size: 0.72rem;
		color: var(--text-dim);
		padding: 0.25rem 0 0.5rem;
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
