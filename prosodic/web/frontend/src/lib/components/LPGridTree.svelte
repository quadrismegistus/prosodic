<script>
	// Faithful Liberman & Prince (1977) figure: the metrical grid above the
	// syllables, the BINARY metrical tree hanging below to the root R, every
	// edge labelled s/w. This is the genuine L&P object the dep-projection
	// view can't be — the tree is binary, so relative prominence (s vs w) is
	// defined on each pair of sisters. Data from /api/parse/lp (lp_line_data):
	//   { grid: [{txt, height, is_function, nuclear}], tree, nuclear, max_height }
	let { data = null } = $props();

	const xSpacing = 42;
	const boxSize = 15;
	const boxGap = 2;
	const treeRowH = 32;
	const margin = 18;

	const RAMP = ['#cbd5e1', '#93c5fd', '#3b82f6', '#f59e0b', '#dc2626'];

	function hexToRgb(h) {
		const n = parseInt(h.slice(1), 16);
		return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
	}
	function rampColor(level, maxh) {
		if (maxh <= 1) return RAMP[0];
		const t = Math.max(0, Math.min(1, (level - 1) / (maxh - 1)));
		const pos = t * (RAMP.length - 1);
		const i = Math.floor(pos), frac = pos - i;
		const a = hexToRgb(RAMP[i]), b = hexToRgb(RAMP[Math.min(i + 1, RAMP.length - 1)]);
		const c = a.map((v, k) => Math.round(v + (b[k] - v) * frac));
		return `rgb(${c[0]},${c[1]},${c[2]})`;
	}

	const scene = $derived.by(() => {
		if (!data || !data.tree || !data.grid) return null;
		const grid = data.grid;
		const maxh = data.max_height || Math.max(1, ...grid.map((g) => g.height));

		let leafI = 0, maxDepth = 0;
		const nodes = [], edges = [];
		function visit(node, depth) {
			maxDepth = Math.max(maxDepth, depth);
			const isLeaf = !node.children || node.children.length === 0;
			const rec = {
				role: node.role, isLeaf, depth,
				text: node.text, height: node.height, is_function: node.is_function,
			};
			if (isLeaf) {
				rec.x = leafI * xSpacing;
				rec.leafI = leafI;
				leafI += 1;
				nodes.push(rec);
				return rec;
			}
			const kids = node.children.map((c) => visit(c, depth + 1));
			rec.x = kids.reduce((s, k) => s + k.x, 0) / kids.length;
			nodes.push(rec);
			for (const k of kids) edges.push({ parent: rec, child: k });
			return rec;
		}
		const root = visit(data.tree, 0);
		const nLeaves = leafI;

		const gridAreaH = maxh * (boxSize + boxGap);
		const gridTop = margin;
		const labelY = gridTop + gridAreaH + 14;
		const treeTop = labelY + 10;
		for (const n of nodes) n.y = n.isLeaf ? 0 : (maxDepth - n.depth) * treeRowH;
		const treeH = maxDepth * treeRowH;

		const width = nLeaves > 0 ? (nLeaves - 1) * xSpacing + margin * 2 + xSpacing : margin * 2;
		const height = treeTop + treeH + margin + 12;
		return { grid, maxh, nodes, edges, root, nLeaves, gridTop, gridAreaH, labelY, treeTop, treeH, width, height };
	});
</script>

{#if scene}
	<div class="lp-grid-tree">
		<svg width={scene.width} height={scene.height}>
			<g transform="translate({margin}, 0)">
				<!-- grid: stacked boxes per syllable, coloured by level -->
				{#each scene.grid as g, i}
					{#each Array.from({ length: g.height }, (_, k) => k + 1) as level}
						<rect
							x={i * xSpacing - boxSize / 2}
							y={scene.gridTop + scene.gridAreaH - level * (boxSize + boxGap)}
							width={boxSize} height={boxSize} rx="2"
							fill={rampColor(level, scene.maxh)}
						>
							<title>{g.txt}: level {g.height}{g.nuclear ? ' (nuclear)' : ''}</title>
						</rect>
					{/each}
					<text x={i * xSpacing} y={scene.labelY}
						class="syll" class:func={g.is_function} class:nuc={g.nuclear}>{g.txt}</text>
				{/each}

				<!-- binary tree hanging down to R, s/w on every edge -->
				<g transform="translate(0, {scene.treeTop})">
					{#each scene.edges as e}
						<line x1={e.parent.x} y1={e.parent.y} x2={e.child.x}
							y2={e.child.y - (e.child.isLeaf ? 0 : 6)} class="edge" />
						<text x={(e.parent.x + e.child.x) / 2 + (e.child.role === 's' ? -1 : 1)}
							y={(e.parent.y + e.child.y) / 2}
							class="role" class:strong={e.child.role === 's'}>{e.child.role}</text>
					{/each}
					{#each scene.nodes as n}
						{#if !n.isLeaf && n.depth === 0}
							<text x={n.x} y={n.y + 14} class="root">R</text>
						{/if}
					{/each}
				</g>
			</g>
		</svg>
		<div class="caption">
			Faithful Liberman &amp; Prince (1977): Stanza constituency → NSR/CSR binary tree →
			within-word feet → RPPR grid. Nuclear stress: <b>{data.nuclear}</b>.
		</div>
	</div>
{/if}

<style>
	.lp-grid-tree { overflow-x: auto; padding: 0.5rem 0; }
	.syll {
		font-family: var(--font); font-size: 12px; fill: var(--text);
		text-anchor: middle;
	}
	.syll.func { fill: var(--text-dim); font-style: italic; }
	.syll.nuc { font-weight: 700; }
	.edge { stroke: var(--border); stroke-width: 1; }
	.role {
		font-family: var(--font-mono); font-size: 9px; fill: var(--text-dim);
		text-anchor: middle; dominant-baseline: middle;
	}
	.role.strong { fill: var(--accent); font-weight: 700; }
	.root {
		font-family: var(--font-mono); font-size: 12px; fill: var(--text-muted);
		text-anchor: middle; font-weight: 700;
	}
	.caption {
		font-size: 0.72rem; color: var(--text-dim); padding-top: 0.5rem;
		max-width: 40rem;
	}
</style>
