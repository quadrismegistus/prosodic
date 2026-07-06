<script>
	// tree: nested {tag, text, tstress, children} JSON from tree_to_dict()
	// (prosodic/texts/phrasal_stress.py). palette: grid_palette from
	// /api/parse/line, reused here as a continuous ramp over tstress so the
	// tree and the metrical grid read as the same prominence scale.
	let { tree = null, palette = [] } = $props();

	const rowHeight = 40;
	const xSpacing = 56;
	const margin = 24;

	function hexToRgb(hex) {
		const n = parseInt(hex.slice(1), 16);
		return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
	}
	function rgbToHex([r, g, b]) {
		return '#' + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
	}
	function interpolateColor(stops, t) {
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

	// Flatten the nested tree into a positioned node/edge list. Leaves are
	// pinned to a common bottom baseline (like nltk's pretty_print / svgling)
	// even when their true depth is shallower, so every word lines up —
	// internal nodes stay at their real depth and get a longer connector.
	function layout(root) {
		if (!root) return { nodes: [], edges: [], width: 0, height: 0 };

		let maxDepth = 0;
		let nextX = 0;
		const nodes = [];
		const edges = [];

		function visit(node, depth) {
			maxDepth = Math.max(maxDepth, depth);
			const isLeaf = !node.children || node.children.length === 0;
			const rec = { tag: node.tag, text: node.text, tstress: node.tstress, isLeaf, depth };
			if (isLeaf) {
				rec.x = nextX * xSpacing;
				nextX += 1;
				nodes.push(rec);
				return rec;
			}
			const childRecs = node.children.map((c) => visit(c, depth + 1));
			rec.x = childRecs.reduce((s, c) => s + c.x, 0) / childRecs.length;
			nodes.push(rec);
			for (const c of childRecs) edges.push({ parent: rec, child: c });
			return rec;
		}
		visit(root, 0);

		for (const n of nodes) {
			n.y = n.isLeaf ? maxDepth * rowHeight : n.depth * rowHeight;
		}

		const width = nextX > 0 ? (nextX - 1) * xSpacing + margin * 2 : margin * 2;
		const height = maxDepth * rowHeight + rowHeight + margin * 2;
		return { nodes, edges, width, height, xOffset: margin, yOffset: margin };
	}

	const scene = $derived(layout(tree));
</script>

{#if tree}
	<div class="syntax-tree">
		<svg width={scene.width} height={scene.height}>
			<g transform="translate({scene.xOffset}, {scene.yOffset})">
				{#each scene.edges as e}
					<line
						x1={e.parent.x}
						y1={e.parent.y + (e.parent.depth === 0 ? 8 : 8)}
						x2={e.child.x}
						y2={e.child.y - (e.child.isLeaf ? 20 : 8)}
						class="edge"
					/>
				{/each}
				{#each scene.nodes as n}
					{#if n.isLeaf}
						<g transform="translate({n.x}, {n.y})">
							<rect x="-16" y="-12" width="32" height="16" rx="3" fill={interpolateColor(palette, n.tstress)} />
							<text x="0" y="0" class="tag">{n.tag}</text>
							<text x="0" y="18" class="word">{n.text}</text>
						</g>
					{:else}
						<text x={n.x} y={n.depth === 0 ? 8 : n.y + 4} class="phrase">{n.tag}</text>
					{/if}
				{/each}
			</g>
		</svg>
	</div>
{/if}

<style>
	.syntax-tree {
		overflow-x: auto;
		padding: 0.5rem 0;
	}
	.edge {
		stroke: var(--border);
		stroke-width: 1;
	}
	.phrase {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		fill: var(--text-muted);
		text-anchor: middle;
	}
	.tag {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		fill: #fff;
		text-anchor: middle;
		dominant-baseline: middle;
	}
	.word {
		font-family: var(--font);
		font-size: 0.8rem;
		fill: var(--text);
		text-anchor: middle;
	}
</style>
