<script>
	import TextInput from '$lib/components/TextInput.svelte';
	import ParseResults from '$lib/components/ParseResults.svelte';
	import CorpusSelect from '$lib/components/CorpusSelect.svelte';
	import { parseStream } from '$lib/api.js';
	import { inputText, meterConfig, constraintWeights, zoneWeights, maxentConfig, parseLoading } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let error = $state('');
	let progress = $state('');
	let rows = $state([]);
	let elapsed = $state(0);
	let numLines = $state(0);

	function buildConstraintList() {
		// When zone weights are active, just send constraint names (zone weights handle scoring)
		// Otherwise, send "name/weight" format for manual weights
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
				resolve_optionality: $meterConfig.resolve_optionality
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

	onMount(() => {
		if ($inputText && rows.length === 0) {
			setTimeout(handleParse, 400);
		}
	});
</script>

<div class="page">
	<section class="input-section">
		<CorpusSelect />
		<TextInput />
		<button class="action-btn" onclick={handleParse} disabled={$parseLoading}>
			{#if $parseLoading}
				<span class="spinner"></span> {progress || 'Parsing...'}
			{:else}
				Parse
			{/if}
		</button>
		<a href="/meter" class="meter-link">Meter settings</a>
	</section>

	<section class="results-section">
		{#if error}
			<div class="error">{error}</div>
		{/if}
		{#if rows.length > 0}
			<ParseResults {rows} {elapsed} {numLines} />
		{:else if !$parseLoading}
			<div class="empty">Paste text and hit Parse</div>
		{/if}
	</section>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	.action-btn {
		width: 100%;
		padding: 0.7rem;
		font-size: 1.05rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 6px;
		margin-bottom: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}
	.action-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}
	.action-btn:disabled {
		opacity: 0.7;
	}
	.meter-link {
		display: block;
		text-align: center;
		font-size: 0.78rem;
		color: var(--text-dim);
		text-decoration: underline;
		margin-bottom: 0.5rem;
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
</style>
