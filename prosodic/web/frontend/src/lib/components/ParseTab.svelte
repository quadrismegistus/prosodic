<script>
	import { onMount } from 'svelte';
	import TextInput from '$lib/components/TextInput.svelte';
	import ParseResults from '$lib/components/ParseResults.svelte';
	import CorpusSelect from '$lib/components/CorpusSelect.svelte';
	import { parseStream } from '$lib/api.js';
	import { encodePermalink, decodePermalink } from '$lib/permalink.js';
	import { inputText, meterConfig, constraintWeights, zoneWeights, maxentConfig, parseLoading, selectedLine, goTab, settings } from '$lib/stores.js';

	let error = $state('');
	let progress = $state('');
	let rows = $state([]);
	let elapsed = $state(0);
	let numLines = $state(0);
	let activeConstraints = $state([]);
	let shareMsg = $state('');

	// A permalink URL longer than this is unwieldy / risks server URL limits; we
	// disable copying and tell the user instead of producing a broken link.
	const MAX_SHARE_URL = 15000;

	function buildConstraintList() {
		if ($zoneWeights) {
			return $meterConfig.constraints;
		}
		return $meterConfig.constraints.map(c => {
			const w = $constraintWeights[c];
			return (w != null && w !== 1.0) ? `${c}/${w}` : c;
		});
	}

	async function handleParse() {
		error = '';
		rows = [];
		elapsed = 0;
		numLines = 0;
		$parseLoading = true;
		progress = 'Starting...';
		try {
			const payload = {
				text: $inputText,
				constraints: buildConstraintList(),
				max_s: $meterConfig.max_s,
				max_w: $meterConfig.max_w,
				resolve_optionality: $meterConfig.resolve_optionality,
				syntax: $settings.syntax,
				syntax_model: $settings.syntax_model,
				parse_timeout: $settings.parse_timeout,
			};
			if ($zoneWeights) {
				payload.zone_weights = $zoneWeights;
				payload.zones = $maxentConfig.zones;
			}
			const meta = await parseStream(payload, {
				onProgress: (msg) => { progress = msg; },
				onRows: (batch) => { rows = [...rows, ...batch]; }
			});
			if (meta) {
				elapsed = meta.elapsed;
				numLines = meta.num_lines;
				activeConstraints = meta.constraints || [];
			}
		} catch (e) {
			error = e.message;
		} finally {
			$parseLoading = false;
			progress = '';
		}
	}

	function handleLineClick(row) {
		$selectedLine = { line_num: row.line_num, line_text: row.line_text };
		goTab('line');
	}

	// --- Shareable permalinks (F8) ---

	// Snapshot the shareable state. Only non-default weights are stored to keep
	// the URL lean; the raw meter config is preserved so the UI can be restored.
	function buildShare() {
		const weights = {};
		for (const c of $meterConfig.constraints) {
			const w = $constraintWeights[c];
			if (w != null && w !== 1.0) weights[c] = w;
		}
		return {
			v: 1,
			text: $inputText,
			meter: {
				constraints: $meterConfig.constraints,
				max_s: $meterConfig.max_s,
				max_w: $meterConfig.max_w,
				resolve_optionality: $meterConfig.resolve_optionality,
			},
			weights,
			zoneWeights: $zoneWeights ?? null,
			zones: $maxentConfig.zones,
			syntax: $settings.syntax,
			syntax_model: $settings.syntax_model,
		};
	}

	function flashShareMsg(msg, ms = 2500) {
		shareMsg = msg;
		setTimeout(() => { if (shareMsg === msg) shareMsg = ''; }, ms);
	}

	async function handleShare() {
		try {
			const enc = await encodePermalink(buildShare());
			const url = `${window.location.origin}/?p=${enc}`;
			if (url.length > MAX_SHARE_URL) {
				flashShareMsg('Text too long to share as a link', 3500);
				return;
			}
			if (navigator.clipboard && navigator.clipboard.writeText) {
				await navigator.clipboard.writeText(url);
				flashShareMsg('Link copied!');
			} else {
				// Non-secure context (no clipboard API): drop it in the URL bar
				// so the user can copy manually.
				history.replaceState(history.state, '', url);
				flashShareMsg('Link is in the address bar');
			}
		} catch (e) {
			flashShareMsg('Copy failed — see console', 3500);
			console.error('permalink share failed:', e);
		}
	}

	// Apply a decoded share payload to the persisted stores. All values flow
	// through the same stores/escaping as normal input — no new sink.
	function applyShare(s) {
		if (typeof s.text === 'string') $inputText = s.text;
		if (s.meter && typeof s.meter === 'object') {
			$meterConfig = {
				constraints: Array.isArray(s.meter.constraints) ? s.meter.constraints : $meterConfig.constraints,
				max_s: s.meter.max_s ?? $meterConfig.max_s,
				max_w: s.meter.max_w ?? $meterConfig.max_w,
				resolve_optionality: s.meter.resolve_optionality ?? $meterConfig.resolve_optionality,
			};
		}
		if (s.weights && typeof s.weights === 'object') {
			constraintWeights.update(w => ({ ...w, ...s.weights }));
		}
		zoneWeights.set(s.zoneWeights ?? null);
		if (s.zones != null) maxentConfig.update(m => ({ ...m, zones: s.zones }));
		settings.update(st => ({
			...st,
			syntax: s.syntax != null ? !!s.syntax : st.syntax,
			syntax_model: s.syntax_model || st.syntax_model,
		}));
	}

	onMount(async () => {
		// Capture the permalink param synchronously before the layout can strip
		// the query string.
		const params = new URLSearchParams(window.location.search);
		const p = params.get('p');
		if (!p) return;
		try {
			const share = await decodePermalink(p);
			applyShare(share);
			// Strip ?p= so the URL reflects live (editable) state; keep the tab
			// history state intact.
			history.replaceState(history.state, '', window.location.pathname);
			await handleParse();
		} catch (e) {
			error = 'Could not load shared parse: ' + e.message;
			console.error('permalink decode failed:', e);
		}
	});
</script>

<div class="page">
	<aside class="input-col">
		<div class="input-sticky">
			<CorpusSelect />
			<TextInput />
			<button class="action-btn" onclick={handleParse} disabled={$parseLoading}>
				{#if $parseLoading}
					<span class="spinner"></span> {progress || 'Parsing...'}
				{:else}
					Parse
				{/if}
			</button>
			<div class="sub-actions">
				<button class="share-btn" onclick={handleShare} title="Copy a shareable link that reproduces this parse">
					{shareMsg || 'Share link'}
				</button>
				<button class="meter-link" onclick={() => goTab('meter')}>Meter settings</button>
			</div>
		</div>
	</aside>

	<section class="results-col">
		{#if error}
			<div class="error">{error}</div>
		{/if}
		{#if rows.length > 0}
			<ParseResults {rows} {elapsed} {numLines} constraints={activeConstraints} onLineClick={handleLineClick} />
		{:else if !$parseLoading}
			<div class="empty">Paste text and hit Parse</div>
		{/if}
	</section>
</div>

<style>
	.page {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1rem;
	}
	.input-col {
		display: flex;
		flex-direction: column;
	}
	.input-sticky {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.results-col {
		min-width: 0;
	}
	.action-btn {
		width: 100%;
		padding: 0.7rem;
		font-size: 1.05rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	.action-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}
	.action-btn:disabled {
		opacity: 0.7;
	}
	.sub-actions {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
	}
	.share-btn {
		flex: 1;
		text-align: center;
		font-size: 0.78rem;
		color: var(--text-dim);
		background: none;
		border: 1px solid var(--border);
		border-radius: 5px;
		cursor: pointer;
		padding: 0.3rem 0.5rem;
		font-family: var(--font);
	}
	.share-btn:hover {
		background: var(--bg-alt);
		color: var(--text);
	}
	.meter-link {
		flex: 1;
		display: block;
		text-align: center;
		font-size: 0.78rem;
		color: var(--text-dim);
		text-decoration: underline;
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.25rem 0;
	}
	.spinner {
		display: inline-block;
		width: 14px;
		height: 14px;
		border: 2px solid rgba(255,255,255,0.3);
		border-top-color: #fff;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	.error {
		color: var(--violation);
		font-size: 0.88rem;
		padding: 0.5rem;
	}
	.empty {
		color: var(--text-dim);
		text-align: center;
		padding: 3rem;
		font-style: italic;
	}

	@media (min-width: 1024px) {
		.page {
			grid-template-columns: minmax(320px, 380px) 1fr;
			gap: 1.5rem;
			align-items: start;
		}
		.input-sticky {
			position: sticky;
			top: 1rem;
		}
	}
</style>
