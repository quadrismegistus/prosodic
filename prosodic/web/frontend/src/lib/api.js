// In Tauri, the sidecar runs on a dynamic port; in browser, proxy handles it
function getBase() {
	if (typeof window !== 'undefined' && window.__PROSODIC_PORT__) {
		return `http://127.0.0.1:${window.__PROSODIC_PORT__}`;
	}
	return '';
}

async function request(method, path, body) {
	const opts = {
		method,
		headers: body instanceof FormData ? {} : { 'Content-Type': 'application/json' },
	};
	if (body) {
		opts.body = body instanceof FormData ? body : JSON.stringify(body);
	}
	const res = await fetch(`${getBase()}${path}`, opts);
	if (!res.ok) {
		const detail = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(detail.detail || res.statusText);
	}
	return res.json();
}

export function getMeterDefaults() {
	return request('GET', '/api/meter/defaults');
}

/**
 * Parse with SSE streaming. Rows arrive in batches.
 * onProgress(msg) — status text updates
 * onRows(rows) — batch of result rows (append to table)
 * Returns { elapsed, num_lines } when done.
 */
export async function parseStream(data, { onProgress, onRows }) {
	const res = await fetch(`${getBase()}/api/parse/stream`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data),
	});
	if (!res.ok) {
		const detail = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(detail.detail || res.statusText);
	}
	const reader = res.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	let meta = null;

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		buffer += decoder.decode(value, { stream: true });
		const lines = buffer.split('\n');
		buffer = lines.pop() || '';
		for (const line of lines) {
			if (!line.startsWith('data: ')) continue;
			const event = JSON.parse(line.slice(6));
			if (event.phase === 'progress' && onProgress) {
				onProgress(event.message);
			} else if (event.phase === 'rows' && onRows) {
				onRows(event.rows);
			} else if (event.phase === 'done') {
				meta = { elapsed: event.elapsed, num_lines: event.num_lines, constraints: event.constraints || [] };
			}
		}
	}
	return meta;
}

export async function parseExport(data, format = 'csv') {
	const res = await fetch(`${getBase()}/api/parse/export`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ ...data, format }),
	});
	if (!res.ok) {
		const detail = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(detail.detail || res.statusText);
	}
	const blob = await res.blob();
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `prosodic-parse.${format}`;
	document.body.appendChild(a);
	a.click();
	a.remove();
	URL.revokeObjectURL(url);
}

export function parseLine(data) {
	return request('POST', '/api/parse/line', data);
}

export function maxentFit(data) {
	return request('POST', '/api/maxent/fit', data);
}

export function maxentFitAnnotations(file, config) {
	const form = new FormData();
	form.append('annotations_file', file);
	if (config.constraints) form.append('constraints', config.constraints.join(','));
	form.append('max_s', config.max_s);
	form.append('max_w', config.max_w);
	form.append('resolve_optionality', config.resolve_optionality);
	form.append('zones', String(config.zones ?? '3'));
	form.append('regularization', config.regularization);
	form.append('syntax', config.syntax);
	return request('POST', '/api/maxent/fit-annotations', form);
}

export function maxentReparse(data) {
	return request('POST', '/api/maxent/reparse', data);
}

export function listCorpora() {
	return request('GET', '/api/corpora');
}

export function readCorpus(path) {
	return request('GET', `/api/corpora/read?path=${encodeURIComponent(path)}`);
}
