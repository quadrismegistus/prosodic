<script>
	import TextInput from '$lib/components/TextInput.svelte';
	import ParseResults from '$lib/components/ParseResults.svelte';
	import CorpusSelect from '$lib/components/CorpusSelect.svelte';
	import { parseStream } from '$lib/api.js';
	import { inputText, meterConfig, constraintWeights, zoneWeights, maxentConfig, parseLoading, selectedLine, goTab, settings } from '$lib/stores.js';

	let error = $state('');
	let progress = $state('');
	let rows = $state([]);
	let elapsed = $state(0);
	let numLines = $state(0);

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
			<button class="meter-link" onclick={() => goTab('meter')}>Meter settings</button>
		</div>
	</aside>

	<section class="results-col">
		{#if error}
			<div class="error">{error}</div>
		{/if}
		{#if rows.length > 0}
			<ParseResults {rows} {elapsed} {numLines} onLineClick={handleLineClick} />
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
	.meter-link {
		display: block;
		width: 100%;
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
