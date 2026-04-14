<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { activeTab } from '$lib/stores.js';

	onMount(() => {
		$activeTab = 'line';
		goto('/', { replaceState: true });
	});
</script>
