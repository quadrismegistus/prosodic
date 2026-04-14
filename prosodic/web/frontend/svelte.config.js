import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			pages: '../static_build',
			assets: '../static_build',
			fallback: 'index.html',
			precompress: false,
			strict: false
		})
	}
};

export default config;
