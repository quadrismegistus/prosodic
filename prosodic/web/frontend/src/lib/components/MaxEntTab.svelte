<script>
	import MaxEntResults from '$lib/components/MaxEntResults.svelte';
	import CorpusSelect from '$lib/components/CorpusSelect.svelte';
	import { maxentFit, maxentFitAnnotations } from '$lib/api.js';
	import {
		inputText, meterConfig, constraintWeights, zoneWeights,
		maxentWeights, maxentLoading, maxentConfig
	} from '$lib/stores.js';

	let error = $state('');
	let phase = $state('');
	let fileInput = $state(null);
	let textFileInput = $state(null);
	let corpusText = $state('');
	let corpusName = $state('');

	function handleCorpusLoad(text, name) {
		corpusText = text;
		corpusName = name;
		if (textFileInput) textFileInput.value = '';
	}

	function buildConstraintList() {
		return $meterConfig.constraints.map(c => {
			const w = $constraintWeights[c];
			return (w != null && w !== 1.0) ? `${c}/${w}` : c;
		});
	}

	function applyLearnedWeights(result) {
		if (!result || !result.weights) return;
		const zw = {};
		for (const w of result.weights) {
			zw[w.name] = w.weight;
		}
		$zoneWeights = zw;
	}

	async function handleFitText() {
		const file = textFileInput?.files?.[0];
		let text = corpusText;
		if (file) {
			text = await file.text();
		}
		if (!text) {
			error = 'Select a corpus or upload a text file';
			return;
		}
		error = '';
		$maxentLoading = true;
		$maxentWeights = null;
		phase = 'Training weights...';
		try {
			const res = await maxentFit({
				text,
				constraints: buildConstraintList(),
				max_s: $meterConfig.max_s,
				max_w: $meterConfig.max_w,
				resolve_optionality: $meterConfig.resolve_optionality,
				target_scansion: $maxentConfig.target_scansion,
				zones: $maxentConfig.zones,
				regularization: $maxentConfig.regularization,
				syntax: $maxentConfig.syntax
			});
			$maxentWeights = res;
			applyLearnedWeights(res);
		} catch (e) {
			error = e.message;
		} finally {
			$maxentLoading = false;
			phase = '';
		}
	}

	async function handleFitAnnotations() {
		const file = fileInput?.files?.[0];
		if (!file) {
			error = 'Please select an annotations file';
			return;
		}
		error = '';
		$maxentLoading = true;
		$maxentWeights = null;
		phase = 'Training from annotations...';
		try {
			const res = await maxentFitAnnotations(file, {
				constraints: buildConstraintList(),
				max_s: $meterConfig.max_s,
				max_w: $meterConfig.max_w,
				resolve_optionality: $meterConfig.resolve_optionality,
				zones: $maxentConfig.zones,
				regularization: $maxentConfig.regularization,
				syntax: $maxentConfig.syntax
			});
			$maxentWeights = res;
			applyLearnedWeights(res);
		} catch (e) {
			error = e.message;
		} finally {
			$maxentLoading = false;
			phase = '';
		}
	}
</script>

<div class="page">
	<h2 class="page-title">MaxEnt Weight Learning</h2>
	<p class="page-desc">Train constraint weights from a text corpus or annotated scansion data. Learned weights are saved to Meter config.</p>

	<section class="section">
		<h3 class="section-title">Train from Text + Target Scansion</h3>
		<CorpusSelect onLoad={handleCorpusLoad} />
		{#if corpusName}
			<div class="corpus-badge">Using: {corpusName}</div>
		{/if}
		<div class="field">
			<label>Or upload a file <span class="desc">Plain text, one line of verse per line</span></label>
			<input type="file" accept=".txt" bind:this={textFileInput}
				onchange={() => { corpusText = ''; corpusName = ''; }} />
		</div>
		<div class="field">
			<label>Target scansion <span class="desc">e.g. wswswswsws for iambic pentameter</span></label>
			<input type="text" class="text-input" bind:value={$maxentConfig.target_scansion} />
		</div>
		<button class="action-btn" onclick={handleFitText} disabled={$maxentLoading}>
			{#if $maxentLoading && phase.includes('Training w')}
				<span class="spinner"></span> {phase}
			{:else}
				Train from Text
			{/if}
		</button>
	</section>

	<section class="section">
		<h3 class="section-title">Train from Annotations</h3>
		<div class="field">
			<label>Annotations file <span class="desc">TSV with columns: text, scansion, frequency</span></label>
			<input type="file" accept=".tsv,.csv,.txt" bind:this={fileInput} />
		</div>
		<button class="action-btn secondary" onclick={handleFitAnnotations} disabled={$maxentLoading}>
			{#if $maxentLoading && phase.includes('annotation')}
				<span class="spinner"></span> {phase}
			{:else}
				Train from Annotations
			{/if}
		</button>
	</section>

	<section class="section">
		<h3 class="section-title">Training Parameters</h3>
		<label class="config-row">
			<span>Zones <span class="desc">Positional zone splitting</span></span>
			<select bind:value={$maxentConfig.zones}>
				<option value={null}>None</option>
				<option value={2}>2</option>
				<option value={3}>3</option>
				<option value="initial">Initial</option>
				<option value="foot">Foot</option>
			</select>
		</label>
		<label class="config-row">
			<span>Regularization <span class="desc">L2 penalty (higher = more conservative)</span></span>
			<input type="number" class="num-input" bind:value={$maxentConfig.regularization} step="10" min="1" />
		</label>
		<label class="config-row">
			<span>Syntax <span class="desc">Add phrasal stress via spaCy</span></span>
			<input type="checkbox" bind:checked={$maxentConfig.syntax} />
		</label>
	</section>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	<MaxEntResults result={$maxentWeights} />
</div>

<style>
	.page {
		max-width: 640px;
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
	.section {
		margin-bottom: 1.25rem;
	}
	.section-title {
		font-size: 0.92rem;
		font-weight: normal;
		color: var(--text-muted);
		border-bottom: 1px solid var(--border);
		padding-bottom: 0.3rem;
		margin-bottom: 0.5rem;
	}
	.field {
		margin-bottom: 0.5rem;
	}
	.field label {
		display: block;
		font-size: 0.85rem;
		margin-bottom: 0.2rem;
	}
	.field input[type="file"] {
		font-size: 0.82rem;
	}
	.desc {
		font-size: 0.7rem;
		color: var(--text-dim);
		display: block;
	}
	.text-input {
		width: 100%;
		max-width: 220px;
		padding: 0.3rem 0.5rem;
		font-size: 0.85rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		font-family: var(--font-mono);
	}
	.action-btn {
		width: 100%;
		padding: 0.65rem;
		font-size: 1rem;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 6px;
		margin-top: 0.25rem;
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
	.action-btn.secondary {
		background: #666;
		font-size: 0.92rem;
	}
	.config-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.35rem 0;
		border-bottom: 1px solid var(--border-light);
		font-size: 0.85rem;
		cursor: pointer;
	}
	.config-row select,
	.num-input {
		font-size: 0.82rem;
		padding: 0.15rem 0.3rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		width: 100px;
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
	.corpus-badge {
		font-size: 0.78rem;
		color: var(--text-muted);
		background: var(--bg-alt);
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		margin-bottom: 0.4rem;
		font-family: var(--font-mono);
	}
	.error {
		color: var(--violation);
		font-size: 0.88rem;
		padding: 0.5rem 0;
	}
</style>
