"""Prosodic remote client.

Provides the same interface as local prosodic (Text, .lines, .parse(), etc.)
but delegates parsing to a remote server or local desktop app via HTTP API.

No prosodic dependencies required beyond `requests` — no numpy, espeak, etc.

Usage:
    import prosodic
    prosodic.set_server("https://prosodic.app")  # or localhost:8181

    t = prosodic.Text("From fairest creatures we desire increase")
    t.parse()

    for line in t.lines:
        bp = line.best_parse
        print(f"{bp.meter_str}  {bp.score:.2f}  {line.txt}")
        for p in line.parses.unbounded:
            print(f"  {p.meter_str}  {p.score:.2f}")

Or use directly:
    from prosodic.client import RemoteText

    t = RemoteText("From fairest creatures...", server="https://prosodic.app")
    t.parse()
"""
import requests


# Global server URL or client — set via set_server()
_server = None


def set_server(server):
    """Set the remote server for all subsequent Text() calls.

    Args:
        server: Server URL string (e.g. "https://prosodic.app"),
                a FastAPI TestClient instance, or None to revert to local.
    """
    global _server
    if isinstance(server, str):
        _server = server.rstrip('/')
    else:
        _server = server  # TestClient or None


def get_server():
    """Get the current remote server (URL string or TestClient), or None."""
    return _server


class _HttpTransport:
    """Wraps either requests (URL string) or FastAPI TestClient."""

    def __init__(self, server):
        self._server = server
        self._is_test_client = not isinstance(server, str)

    def get(self, path, **kwargs):
        timeout = kwargs.pop('timeout', 120)
        if self._is_test_client:
            resp = self._server.get(path, **kwargs)
        else:
            resp = requests.get(f"{self._server}{path}", timeout=timeout, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def post(self, path, json=None, **kwargs):
        timeout = kwargs.pop('timeout', 120)
        if self._is_test_client:
            resp = self._server.post(path, json=json, **kwargs)
        else:
            resp = requests.post(f"{self._server}{path}", json=json, timeout=timeout, **kwargs)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Lightweight proxy objects that duck-type the real prosodic classes
# ---------------------------------------------------------------------------

class RemoteParse:
    """Duck-types prosodic.parsing.parses.Parse."""

    def __init__(self, data):
        self._data = data
        self.rank = data.get('rank', 0)
        self.meter_str = data.get('meter_str', '')
        self.score = data.get('score', 0.0)
        self.is_bounded = data.get('is_bounded', False)
        self.parse_html = data.get('parse_html', '')
        self.num_viols = data.get('num_viols', 0)
        self.viol_summary = data.get('viol_summary', {})
        self.positions = [RemotePosition(p) for p in data.get('positions', [])]

    @property
    def violset(self):
        return set(self.viol_summary.keys())

    def render(self, as_str=True, **kwargs):
        return self.parse_html

    def __repr__(self):
        bounded = ' [bounded]' if self.is_bounded else ''
        return f"Parse({self.meter_str}, score={self.score}{bounded})"

    def __lt__(self, other):
        return self.score < other.score


class RemotePosition:
    """Duck-types a metrical position."""

    def __init__(self, data):
        self.mtr = data.get('mtr', 'w')
        self.is_prom = self.mtr == 's'
        self.meter_val = self.mtr
        self.slots = [RemoteSlot(s) for s in data.get('slots', [])]
        self.children = self.slots


class RemoteSlot:
    """Duck-types a parse slot."""

    def __init__(self, data):
        self.txt = data.get('text', '')
        self.is_stressed = data.get('is_stressed', False)
        self.is_prom = data.get('is_prom', False)
        self.violations = data.get('violations', [])
        self.violset = set(self.violations)

    @property
    def unit(self):
        return self


class RemoteParseList:
    """Duck-types prosodic.parsing.parselists.ParseList / LazyParseList."""

    def __init__(self, parses):
        self._parses = parses
        self._unbounded = [p for p in parses if not p.is_bounded]
        self._bounded = [p for p in parses if p.is_bounded]

    @property
    def best_parse(self):
        if not self._unbounded:
            return None
        return min(self._unbounded, key=lambda p: p.score)

    @property
    def unbounded(self):
        return sorted(self._unbounded, key=lambda p: p.score)

    @property
    def bounded(self):
        return sorted(self._bounded, key=lambda p: p.score)

    @property
    def num_unbounded(self):
        return len(self._unbounded)

    @property
    def num_parses(self):
        return len(self._unbounded)

    def __len__(self):
        return len(self._parses)

    def __iter__(self):
        return iter(sorted(self._parses, key=lambda p: p.score))

    def __bool__(self):
        return len(self._parses) > 0

    def __repr__(self):
        return f"ParseList({len(self._unbounded)} unbounded, {len(self._bounded)} bounded)"


class RemoteWeights:
    """Result of MaxEnt training."""

    def __init__(self, data):
        self._data = data
        self.weights = {w['name']: w['weight'] for w in data.get('weights', [])}
        self.elapsed = data.get('elapsed', 0)
        self.accuracy = data.get('accuracy', 0)
        self.num_lines = data.get('num_lines', 0)
        self.num_matched = data.get('num_matched', 0)
        self.log_likelihood = data.get('log_likelihood', 0)
        self.config = data.get('config', {})

    def __repr__(self):
        return f"RemoteWeights({len(self.weights)} weights, accuracy={self.accuracy:.3f})"


class RemoteLine:
    """Duck-types prosodic.texts.lines.Line."""

    def __init__(self, line_num, txt, transport=None):
        self.num = line_num
        self._num = line_num
        self.txt = txt
        self._txt = txt
        self._parses = None
        self._transport = transport

    @property
    def best_parse(self):
        if self._parses:
            return self._parses.best_parse
        return None

    @property
    def parses(self):
        return self._parses

    def parse(self, server=None, **kwargs):
        """Fetch all scansions for this line from the server."""
        transport = self._transport
        if transport is None:
            srv = server or _server
            if not srv:
                raise RuntimeError("No server configured. Call prosodic.set_server() first.")
            transport = _HttpTransport(srv)
        data = transport.post('/api/parse/line', json={'text': self.txt, **kwargs})
        parses = [RemoteParse(p) for p in data.get('parses', [])]
        self._parses = RemoteParseList(parses)
        return self._parses

    def __repr__(self):
        return f"Line({self.num}: {self.txt[:50]}{'...' if len(self.txt) > 50 else ''})"


class RemoteText:
    """Duck-types prosodic.texts.texts.TextModel.

    Sends text to a remote prosodic server for parsing. The interface is
    identical to the local TextModel: .lines, .parse(), .best_parse, etc.
    """

    is_text = True
    prefix = "text"

    def __init__(self, txt="", fn=None, server=None, **kwargs):
        if fn:
            with open(fn) as f:
                txt = f.read()
        self._txt = txt.strip()
        self.txt = self._txt
        srv = server or _server
        if not srv:
            raise RuntimeError(
                "No server configured. Either pass server= or call prosodic.set_server() first."
            )
        self._transport = _HttpTransport(srv)
        self._lines = None
        self._parsed = False
        self._parse_kwargs = kwargs
        self._rows = []

    @property
    def lines(self):
        if self._lines is None:
            self._lines = []
            for i, line_txt in enumerate(self._txt.split('\n'), 1):
                line_txt = line_txt.strip()
                if line_txt:
                    self._lines.append(RemoteLine(i, line_txt, transport=self._transport))
        return self._lines

    def parse(self, **kwargs):
        """Parse all lines via the remote server."""
        merged = {**self._parse_kwargs, **kwargs}
        data = self._transport.post('/api/parse', json={'text': self._txt, **merged})
        self._rows = data.get('rows', [])
        self._parsed = True

        # Group rows by line_num and attach to line objects
        from collections import defaultdict
        by_line = defaultdict(list)
        for row in self._rows:
            by_line[row['line_num']].append(row)

        # Build line objects with parse results
        self._lines = []
        for line_num in sorted(by_line.keys()):
            rows = by_line[line_num]
            line_txt = rows[0].get('line_text', '')
            line = RemoteLine(line_num, line_txt, transport=self._transport)
            parses = []
            for row in sorted(rows, key=lambda r: r['score']):
                parses.append(RemoteParse({
                    'rank': row['rank'],
                    'meter_str': row['meter_str'],
                    'score': row['score'],
                    'parse_html': row['parse_html'],
                    'is_bounded': False,
                    'positions': [],
                    'num_viols': 0,
                    'viol_summary': {},
                }))
            line._parses = RemoteParseList(parses)
            self._lines.append(line)

        return self

    def parse_lines(self, **kwargs):
        """Parse each line individually (gets all scansions including bounded)."""
        for line in self.lines:
            line.parse(**kwargs)
        self._parsed = True
        return self

    def fit(self, target_scansion='wswswswsws', zones=3, regularization=100,
            constraints=None, max_s=2, max_w=2, resolve_optionality=True,
            syntax=False):
        """Train MaxEnt weights on this text via the remote server.

        Returns RemoteWeights with .weights dict, .accuracy, etc.
        """
        payload = {
            'text': self._txt,
            'target_scansion': target_scansion,
            'zones': zones,
            'regularization': regularization,
            'max_s': max_s,
            'max_w': max_w,
            'resolve_optionality': resolve_optionality,
            'syntax': syntax,
        }
        if constraints:
            payload['constraints'] = constraints
        data = self._transport.post('/api/maxent/fit', json=payload)
        return RemoteWeights(data)

    @property
    def parsed(self):
        return self._parsed

    @property
    def best_parses(self):
        if not self._parsed:
            self.parse()
        return [line.best_parse for line in self.lines if line.best_parse]

    def render(self, **kwargs):
        if not self._parsed:
            self.parse()
        parts = []
        for line in self.lines:
            bp = line.best_parse
            if bp:
                parts.append(bp.parse_html)
        return '<br>'.join(parts)

    def meter_defaults(self):
        """Get available constraints and default meter config."""
        return self._transport.get('/api/meter/defaults')

    def corpora(self):
        """List available corpora."""
        return self._transport.get('/api/corpora')

    def save(self, path):
        """Save parse results to a directory. Loads back with RemoteText.load().

        Saves as JSON (no pandas/pyarrow required). If pandas is available,
        also saves a parsed.parquet compatible with TextModel.load().

        Args:
            path: directory to save into (created if needed)

        Returns:
            str: path to the saved directory
        """
        import json as _json
        import os as _os
        _os.makedirs(path, exist_ok=True)

        if not self._parsed:
            self.parse()

        # Serialize lines + parse data
        lines_data = []
        for line in self.lines:
            line_d = {'num': line.num, 'txt': line.txt, 'parses': []}
            if line._parses:
                for p in line._parses._parses:
                    line_d['parses'].append(p._data)
            lines_data.append(line_d)

        data = {
            'txt': self._txt,
            'lines': lines_data,
        }
        with open(_os.path.join(path, 'remote_parse.json'), 'w') as f:
            _json.dump(data, f)

        # Also save parsed.parquet if pandas available (for interop with local TextModel)
        try:
            import pandas as pd
            rows = []
            for line in self.lines:
                bp = line.best_parse
                if not bp:
                    continue
                for pos in bp.positions:
                    for slot in pos.slots:
                        rows.append({
                            'line_num': line.num,
                            'syll_txt': slot.txt,
                            'meter_val': pos.mtr,
                            'is_stressed': slot.is_stressed,
                            'is_prom': slot.is_prom,
                            'score': bp.score,
                        })
            if rows:
                pd.DataFrame(rows).to_parquet(_os.path.join(path, 'parsed.parquet'))
        except ImportError:
            pass

        return path

    @classmethod
    def load(cls, path, server=None):
        """Load saved remote parse results.

        Args:
            path: directory containing remote_parse.json
            server: optional server for further operations (parse_lines, fit)

        Returns:
            RemoteText with parse results pre-loaded (no server call needed)
        """
        import json as _json
        import os as _os

        with open(_os.path.join(path, 'remote_parse.json')) as f:
            data = _json.load(f)

        # Build without requiring a server
        obj = cls.__new__(cls)
        obj._txt = data['txt']
        obj.txt = obj._txt
        obj._transport = _HttpTransport(server) if server else None
        obj._parsed = True
        obj._parse_kwargs = {}
        obj._rows = []

        # Reconstruct lines + parses
        obj._lines = []
        for ld in data['lines']:
            line = RemoteLine(ld['num'], ld['txt'], transport=obj._transport)
            parses = [RemoteParse(p) for p in ld.get('parses', [])]
            if parses:
                line._parses = RemoteParseList(parses)
            obj._lines.append(line)

        return obj

    def __repr__(self):
        n = len(self.txt.split('\n'))
        if self._transport:
            server = self._transport._server if isinstance(self._transport._server, str) else 'TestClient'
        else:
            server = 'loaded'
        return f"RemoteText({n} lines, server={server})"
