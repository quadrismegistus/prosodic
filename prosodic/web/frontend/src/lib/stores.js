import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export const DEFAULT_TEXT = `From fairest creatures we desire increase,
That thereby beauty's rose might never die,
But as the riper should by time decease,
His tender heir might bear his memory:
But thou, contracted to thine own bright eyes,
Feed'st thy light'st flame with self-substantial fuel,
Making a famine where abundance lies,
Thyself thy foe, to thy sweet self too cruel.
Thou that art now the world's fresh ornament
And only herald to the gaudy spring,
Within thine own bud buriest thy content
And, tender churl, makest waste in niggarding.
Pity the world, or else this glutton be,
To eat the world's due, by the grave and thee.`;

// localStorage helpers
function loadJSON(key, fallback) {
	if (!browser) return fallback;
	try {
		const v = localStorage.getItem(key);
		return v ? JSON.parse(v) : fallback;
	} catch { return fallback; }
}

function persisted(key, fallback) {
	const store = writable(loadJSON(key, fallback));
	if (browser) {
		store.subscribe(v => {
			localStorage.setItem(key, JSON.stringify(v));
		});
	}
	return store;
}

// --- Persisted stores ---

export const inputText = persisted('prosodic:text', DEFAULT_TEXT);

export const meterConfig = persisted('prosodic:meter', {
	constraints: [],
	max_s: 2,
	max_w: 2,
	resolve_optionality: true
});

// Per-constraint weights: { constraint_name: weight }
// Default is 1.0 for all. MaxEnt training overwrites these.
export const constraintWeights = persisted('prosodic:weights', {});

// Zone weights from MaxEnt (zone-expanded names → weights)
export const zoneWeights = persisted('prosodic:zoneWeights', null);

export const maxentConfig = persisted('prosodic:maxent', {
	target_scansion: 'wswswswsws',
	zones: 3,
	regularization: 100,
	syntax: false
});

// Active tab (persisted so refresh stays on same tab)
export const activeTab = persisted('prosodic:tab', 'parse');

// Switch tab + sync URL (use instead of setting activeTab directly when you
// want back/forward to work and the URL to reflect the tab).
export function goTab(id) {
	if (browser) {
		const path = id === 'parse' ? '/' : `/${id}`;
		if (window.location.pathname !== path) {
			history.pushState({ tab: id }, '', path);
		}
	}
	activeTab.set(id);
}

// --- Non-persisted stores ---

export const allConstraints = writable([]);
export const constraintDescriptions = writable({});
export const defaultConstraints = writable([]);

export const parseLoading = writable(false);

export const maxentWeights = writable(null);
export const maxentLoading = writable(false);

export const reparseResults = writable(null);
export const reparseLoading = writable(false);

export const corporaList = writable([]);

// Selected line for LineView tab
export const selectedLine = writable(null);  // { line_num, line_text, rows }

// Global settings (Settings tab)
export const settings = persisted('prosodic:settings', {
	syntax: false,
	syntax_model: 'en_core_web_sm',
	lang: 'en',
	max_syll: 18,
	parse_timeout: 30,
});
