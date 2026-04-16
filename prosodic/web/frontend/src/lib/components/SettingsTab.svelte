<script>
	import { settings } from '$lib/stores.js';

	function reset() {
		settings.set({
			syntax: false,
			syntax_model: 'en_core_web_sm',
			lang: 'en',
			max_syll: 18,
			parse_timeout: 30,
		});
	}
</script>

<div class="page">
	<h2 class="page-title">Settings</h2>
	<p class="page-desc">Global options for parsing and analysis.</p>

	<section class="section">
		<h3 class="section-title">Syntax</h3>
		<label class="config-row">
			<div>
				<span>Enable phrasal stress</span>
				<span class="desc">Compute phrasal prominence via spaCy dependency parsing (Liberman & Prince 1977). Enables w_prom and s_demoted constraints.</span>
			</div>
			<input type="checkbox" bind:checked={$settings.syntax} />
		</label>
		<label class="config-row">
			<div>
				<span>spaCy model</span>
				<span class="desc">Dependency parse model for phrasal stress</span>
			</div>
			<select bind:value={$settings.syntax_model}>
				<option value="en_core_web_sm">en_core_web_sm</option>
				<option value="en_core_web_md">en_core_web_md</option>
				<option value="en_core_web_lg">en_core_web_lg</option>
				<option value="en_core_web_trf">en_core_web_trf</option>
			</select>
		</label>
	</section>

	<section class="section">
		<h3 class="section-title">Language</h3>
		<label class="config-row">
			<div>
				<span>Default language</span>
				<span class="desc">Language for tokenization and pronunciation lookup</span>
			</div>
			<select bind:value={$settings.lang}>
				<option value="en">English</option>
				<option value="fi">Finnish</option>
			</select>
		</label>
	</section>

	<section class="section">
		<h3 class="section-title">Performance</h3>
		<label class="config-row">
			<div>
				<span>Max syllables per parse unit</span>
				<span class="desc">Lines longer than this are skipped (exponential complexity). Default 14.</span>
			</div>
			<input type="number" class="num-input" bind:value={$settings.max_syll} min="6" max="30" step="1" />
		</label>
		<label class="config-row">
			<div>
				<span>Parse timeout (seconds)</span>
				<span class="desc">Maximum time per line before giving up</span>
			</div>
			<input type="number" class="num-input" bind:value={$settings.parse_timeout} min="5" max="300" step="5" />
		</label>
	</section>

	<div class="actions">
		<button class="btn" onclick={reset}>Reset to Defaults</button>
	</div>
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
		margin-bottom: 1.5rem;
	}
	.section-title {
		font-size: 0.92rem;
		font-weight: normal;
		color: var(--text-muted);
		border-bottom: 1px solid var(--border);
		padding-bottom: 0.3rem;
		margin-bottom: 0.4rem;
	}
	.config-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid var(--border-light);
		font-size: 0.88rem;
		cursor: pointer;
		gap: 1rem;
	}
	.config-row div {
		flex: 1;
	}
	.desc {
		display: block;
		font-size: 0.7rem;
		color: var(--text-dim);
		margin-top: 0.1rem;
	}
	.config-row select {
		font-size: 0.82rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		min-width: 100px;
	}
	.num-input {
		font-size: 0.82rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		width: 80px;
		text-align: right;
	}
	.actions {
		margin-top: 1rem;
	}
	.btn {
		padding: 0.4rem 0.8rem;
		font-size: 0.82rem;
		border: 1px solid var(--border);
		border-radius: 5px;
		background: #fff;
		color: var(--text);
	}
	.btn:hover {
		background: var(--bg-alt);
	}
</style>
