// Shareable parse permalinks (F8).
//
// Wire format (interoperable with the backend api.py _decode_permalink):
//   base64url( optionally gzip-compressed UTF-8 JSON )
// gzip is detected on decode by its magic bytes (0x1f 0x8b), so no flag byte is
// needed. Uses only built-ins (btoa/atob + TextEncoder/TextDecoder) plus the
// optional CompressionStream API — no new bundle dependencies.

function b64urlFromBytes(bytes) {
	let bin = '';
	// Chunk to avoid blowing the call stack on large inputs.
	const CHUNK = 0x8000;
	for (let i = 0; i < bytes.length; i += CHUNK) {
		bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
	}
	return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function bytesFromB64url(s) {
	s = s.replace(/-/g, '+').replace(/_/g, '/');
	while (s.length % 4) s += '=';
	const bin = atob(s);
	const bytes = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
	return bytes;
}

async function streamTransform(bytes, Ctor) {
	const cs = new Ctor('gzip');
	const writer = cs.writable.getWriter();
	writer.write(bytes);
	writer.close();
	const buf = await new Response(cs.readable).arrayBuffer();
	return new Uint8Array(buf);
}

async function maybeGzip(bytes) {
	if (typeof CompressionStream === 'undefined') return null;
	try {
		return await streamTransform(bytes, CompressionStream);
	} catch {
		return null;
	}
}

async function gunzip(bytes) {
	if (typeof DecompressionStream === 'undefined') {
		throw new Error('gzip permalink not supported in this browser');
	}
	return streamTransform(bytes, DecompressionStream);
}

// Encode a share payload object → URL-safe string. Gzips when it actually
// helps (long text) and the browser supports CompressionStream.
export async function encodePermalink(payload) {
	const json = JSON.stringify(payload);
	const bytes = new TextEncoder().encode(json);
	let out = bytes;
	const gz = await maybeGzip(bytes);
	if (gz && gz.length < bytes.length) out = gz;
	return b64urlFromBytes(out);
}

// Decode a URL-safe string → share payload object.
export async function decodePermalink(data) {
	let bytes = bytesFromB64url(data);
	if (bytes.length >= 2 && bytes[0] === 0x1f && bytes[1] === 0x8b) {
		bytes = await gunzip(bytes);
	}
	const json = new TextDecoder().decode(bytes);
	return JSON.parse(json);
}
