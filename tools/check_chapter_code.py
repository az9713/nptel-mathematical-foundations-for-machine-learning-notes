"""Execute all authored Python listings and compare their displayed stdout."""
from __future__ import annotations

import hashlib
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup
import pycodestyle

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.private' / 'code-checks'


def check(path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    article = soup.select_one('#chapter-content') or soup
    blocks = article.select('pre > code.language-python, pre > code.python')
    if not blocks:
        return {'file': path.name, 'status': 'FAIL', 'error': 'No marked Python listings'}
    scripts = []
    for index, block in enumerate(blocks, 1):
        source = block.get_text()
        lint_output = io.StringIO()
        with contextlib.redirect_stdout(lint_output):
            lint_errors = pycodestyle.Checker(lines=source.splitlines(keepends=True)).check_all()
        if lint_errors:
            return {'file': path.name, 'status': 'FAIL', 'block': index,
                    'error': 'PEP8 formatting', 'details': lint_output.getvalue()}
        scripts.append(source)
        script = WORK / f'{path.stem}-{index:02d}.py'
        # Listings within one chapter may share earlier definitions.
        combined = '\n\n'.join(scripts)
        script.write_text(combined, encoding='utf-8')
        result = subprocess.run([sys.executable, '-X', 'utf8', '-I', str(script)],
                                cwd=WORK, capture_output=True, text=True,
                                timeout=90, encoding='utf-8',
                                env={**os.environ, 'OPENBLAS_NUM_THREADS': '1',
                                     'OMP_NUM_THREADS': '1'})
        if result.returncode:
            return {'file': path.name, 'status': 'FAIL', 'block': index,
                    'stderr': result.stderr, 'stdout': result.stdout}
    expected_blocks = article.select('pre.output')
    expected = '\n'.join(block.get_text().strip() for block in expected_blocks)
    actual = result.stdout.strip()
    record = {'file': path.name, 'listing_count': len(blocks),
              'checked_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'listing_sha256': hashlib.sha256(combined.encode('utf-8')).hexdigest(),
              'pep8': 'PASS',
              'status': 'PASS' if actual == expected else 'FAIL',
              'stdout': actual, 'displayed_stdout_matches': actual == expected}
    if actual != expected:
        record['expected_stdout'] = expected
    return record


if __name__ == '__main__':
    WORK.mkdir(parents=True, exist_ok=True)
    paths = ([ROOT / name for name in sys.argv[1:]] if len(sys.argv) > 1
             else sorted(ROOT.glob('chapter-[0-9][0-9]-*.html')))
    records = []
    if len(sys.argv) > 1 and (ROOT / 'chapter-code-validation.json').exists():
        previous = json.loads((ROOT / 'chapter-code-validation.json').read_text(encoding='utf-8'))
        selected = {p.name for p in paths}
        records = [r for r in previous['records'] if r['file'] not in selected]
    for path in paths:
        try:
            record = check(path)
        except Exception as exc:
            record = {'file': path.name, 'status': 'FAIL', 'error': str(exc)}
        records.append(record)
        print(path.name, record['status'], flush=True)
    records.sort(key=lambda r: r['file'])
    report = {'scope': 'Actual isolated execution of every marked Python listing; displayed stdout comparison.',
              'binding': 'LF-normalized executable-listing hashes bind execution; reader wrapping and prose-only edits do not change the checked programs.',
              'limitations': 'Teaching implementation checks, not formal proof verification or real-world validation.',
              'records': records}
    (ROOT / 'chapter-code-validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    sys.exit(0 if all(r['status'] == 'PASS' for r in records) else 1)
