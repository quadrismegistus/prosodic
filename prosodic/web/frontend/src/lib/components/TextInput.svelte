<script>
	import { inputText } from '$lib/stores.js';
</script>

<div class="text-input">
	<textarea bind:value={$inputText} placeholder="Paste poetry here..."></textarea>
</div>

<style>
	.text-input {
		margin-bottom: 0.75rem;
	}
	textarea {
		width: 100%;
		min-height: 180px;
		font-family: var(--font);
		font-size: 15px;
		line-height: 1.6;
		padding: 0.75rem;
		border: 1px solid var(--border);
		border-radius: 6px;
		resize: vertical;
		background: #fff;
		color: var(--text);
	}
	textarea:focus {
		outline: none;
		border-color: var(--accent);
	}
</style>
