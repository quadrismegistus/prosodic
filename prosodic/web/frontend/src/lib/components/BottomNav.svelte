<script>
	import { page } from '$app/state';
</script>

<nav>
	<a href="/" class:active={page.url.pathname === '/'}>
		<span class="icon">⏑</span>
		<span class="label">Parse</span>
	</a>
	<a href="/meter" class:active={page.url.pathname === '/meter'}>
		<span class="icon">♩</span>
		<span class="label">Meter</span>
	</a>
	<a href="/maxent" class:active={page.url.pathname === '/maxent'}>
		<span class="icon">λ</span>
		<span class="label">MaxEnt</span>
	</a>
</nav>

<style>
	nav {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		display: flex;
		background: #fff;
		border-top: 1px solid var(--border);
		z-index: 100;
		height: var(--bottom-nav-height);
	}
	a {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.15rem;
		color: var(--text-dim);
		font-size: 0.75rem;
		text-decoration: none;
		transition: color 0.15s;
	}
	a.active {
		color: var(--accent);
	}
	.icon {
		font-size: 1.3rem;
		line-height: 1;
	}
	.label {
		font-family: var(--font);
	}

	@media (min-width: 769px) {
		nav { display: none; }
	}
</style>
