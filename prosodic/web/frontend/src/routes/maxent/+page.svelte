<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { activeTab } from '$lib/stores.js';

	onMount(() => {
		$activeTab = 'maxent';
		goto('/', { replaceState: true });
	});
</script>
