<script>
	import { onMount } from 'svelte';
	import { listCorpora, readCorpus } from '$lib/api.js';
	import { inputText, corporaList } from '$lib/stores.js';

	let { onLoad = null } = $props();
	let loading = $state(false);

	onMount(async () => {
		if ($corporaList.length === 0) {
			try {
				const data = await listCorpora();
				$corporaList = data.files;
			} catch (e) {
				console.error('Failed to load corpora:', e);
			}
		}
	});

	async function handleSelect(e) {
		const path = e.target.value;
		if (!path) return;
		loading = true;
		try {
			const data = await readCorpus(path);
			if (onLoad) {
				onLoad(data.text, data.name);
			} else {
				$inputText = data.text;
			}
		} catch (e) {
			console.error('Failed to read corpus:', e);
		} finally {
			loading = false;
			e.target.value = '';
		}
	}
</script>

{#if $corporaList.length > 0}
	<select class="corpus-select" onchange={handleSelect} disabled={loading}>
		<option value="">{loading ? 'Loading...' : 'Load from corpus...'}</option>
		{#each $corporaList as file}
			<option value={file.path}>
				{file.name} ({file.num_lines} lines)
			</option>
		{/each}
	</select>
{/if}

<style>
	.corpus-select {
		width: 100%;
		padding: 0.45rem 0.5rem;
		font-family: var(--font);
		font-size: 0.85rem;
		border: 1px solid var(--border);
		border-radius: 5px;
		background: #fff;
		color: var(--text-muted);
		margin-bottom: 0.5rem;
		cursor: pointer;
	}
	.corpus-select:focus {
		outline: none;
		border-color: var(--accent);
		color: var(--text);
	}
</style>
