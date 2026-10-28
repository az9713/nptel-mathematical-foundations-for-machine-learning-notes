"""Check public source coverage, offline links, body digests, and the real reader."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def static_checks():
    manifest = json.loads((ROOT / 'source-manifest.json').read_text(encoding='utf-8'))
    videos = {v['video_id']: v for v in manifest['lectures']}
    errors = []
    if len(videos) != 71 or sorted(v['lecture_number'] for v in videos.values()) != list(range(71)):
        errors.append('Source coverage must include introduction and lectures 1–70 exactly once.')
    chapters = manifest['chapters']
    assigned = [number for c in chapters for number in c['lecture_numbers']]
    if sorted(assigned) != list(range(71)):
        errors.append('Chapter assignments overlap or omit recordings.')
    records = []
    for path in sorted(ROOT.glob('*.html')):
        text = path.read_text(encoding='utf-8')
        soup = BeautifulSoup(text, 'html.parser')
        ids = [tag['id'] for tag in soup.select('[id]')]
        local_errors = []
        if len(ids) != len(set(ids)):
            local_errors.append('Duplicate element IDs.')
        if '<!-- BOOK-CONTENT-START -->' not in text:
            local_errors.append('Reader wrapper missing.')
        else:
            content = text.split('<!-- BOOK-CONTENT-START -->', 1)[1].split('<!-- BOOK-CONTENT-END -->', 1)[0]
            expected = soup.find('meta', attrs={'name': 'book-content-sha256'})
            if not expected or expected.get('content') != hashlib.sha256(content.encode()).hexdigest():
                local_errors.append('Authored-body digest mismatch.')
        for tag in soup.select('[href], script[src], img[src]'):
            url = tag.get('href') or tag.get('src')
            parsed = urlparse(url)
            if parsed.scheme in ('http', 'https'):
                if parsed.netloc in ('www.youtube.com', 'youtube.com') and parsed.path == '/watch':
                    params = parse_qs(parsed.query)
                    vid = params.get('v', [''])[0]
                    if vid not in videos:
                        local_errors.append(f'Unknown source recording: {vid}')
                    elif params.get('t'):
                        raw = params['t'][0].rstrip('s')
                        try:
                            seconds = float(raw)
                            if not 0 <= seconds <= videos[vid]['duration_seconds'] + 2:
                                local_errors.append(f'Timestamp outside source duration: {url}')
                        except ValueError:
                            local_errors.append(f'Unsupported timestamp: {url}')
                continue
            if parsed.scheme or not parsed.path and not parsed.fragment:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(ROOT) or not target.exists():
                local_errors.append(f'Missing or out-of-root target: {url}')
                continue
            if parsed.fragment and target.suffix == '.html':
                target_soup = soup if target == path else BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser')
                if not target_soup.find(id=unquote(parsed.fragment)):
                    local_errors.append(f'Unresolved fragment: {url}')
        if path.name.startswith('chapter-'):
            article = soup.select_one('#chapter-content') or soup
            if len(article.select('details')) < 6:
                local_errors.append('Fewer than six worked-solution disclosures.')
            if not article.select('code.language-python, code.python'):
                local_errors.append('Executable Python listing missing.')
            if not article.select('h2 .timestamp'):
                local_errors.append('Major-section timestamps missing.')
        if re.search(r'[A-Za-z]:[\\/](?:Users|Temp)[\\/]|sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,}', text):
            local_errors.append('Private path or secret-shaped value.')
        records.append({'file': path.name, 'status': 'PASS' if not local_errors else 'FAIL',
                        'errors': local_errors})
        errors.extend(f'{path.name}: {error}' for error in local_errors)
    return {'status': 'PASS' if not errors else 'FAIL', 'records': records, 'errors': errors}


def browser_checks():
    from playwright.sync_api import sync_playwright

    records = []
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception as exc:
            if "Executable doesn't exist" not in str(exc):
                raise
            installed = (Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))
                         / 'Google/Chrome/Application/chrome.exe')
            browser = playwright.chromium.launch(headless=True, executable_path=str(installed))
        for width, height in ((1440, 1000), (390, 844)):
            context = browser.new_context(viewport={'width': width, 'height': height},
                                          reduced_motion='reduce')
            context.route('http://**/*', lambda route: route.abort())
            context.route('https://**/*', lambda route: route.abort())
            page = context.new_page()
            for path in sorted(ROOT.glob('*.html')):
                errors = []
                try:
                    page.goto(path.as_uri(), wait_until='load', timeout=60000)
                    page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise', timeout=30000)
                    page.evaluate('MathJax.startup.promise')
                    if page.locator('mjx-merror').count():
                        errors.append('MathJax error: '+page.locator('mjx-merror').all_text_contents().__repr__())
                    if page.evaluate('document.documentElement.scrollWidth > innerWidth + 2'):
                        errors.append('Horizontal document overflow.')
                    if page.locator('#chapter-content').count() != 1:
                        errors.append('Authored article missing.')
                    page.locator('#theme-toggle').click()
                    if not page.locator('body').evaluate('e=>e.classList.contains("light")'):
                        errors.append('Light-theme control failed.')
                    page.locator('#theme-toggle').click()
                    page.locator('#text-toggle').click()
                    if not page.locator('body').evaluate('e=>e.classList.contains("large-text")'):
                        errors.append('Larger-text control failed.')
                    page.locator('#text-toggle').click()
                    page.locator('#solutions-toggle').click()
                    if page.locator('article details:not([open])').count():
                        errors.append('Expand-solutions control failed.')
                    page.locator('#solutions-toggle').click()
                    if path.name.startswith('chapter-'):
                        if page.locator('#chapter-toc a').count() != page.locator('article h2').count():
                            errors.append('Generated chapter contents incomplete.')
                        if page.locator('pre code').count() != page.locator('.copy-code').count():
                            errors.append('Code-copy control missing.')
                    if path.name == 'index.html':
                        page.locator('#lecture-search').fill('covariance')
                        if page.locator('[data-lecture]:visible').count() < 1:
                            errors.append('Chapter search failed.')
                        page.locator('#lecture-search').fill('')
                        if page.locator('[data-lecture]:visible').count() != 26:
                            errors.append('Search reset failed.')
                        page.evaluate('window.scrollTo(0, 0)')
                        page.screenshot(path=str(ROOT / 'assets' / ('site-preview.png' if width == 1440 else 'preview-mobile.png')))
                    # The browser beforeprint handler must expand and restore disclosures.
                    before = page.locator('details[open]').count()
                    page.evaluate('window.dispatchEvent(new Event("beforeprint"))')
                    if page.locator('details:not([open])').count():
                        errors.append('Print expansion failed.')
                    page.evaluate('window.dispatchEvent(new Event("afterprint"))')
                    if page.locator('details[open]').count() != before:
                        errors.append('Print state restoration failed.')
                except Exception as exc:
                    errors.append(str(exc))
                record = {'file': path.name, 'viewport': [width, height],
                          'status': 'PASS' if not errors else 'FAIL', 'errors': errors}
                records.append(record)
                print(path.name, width, record['status'], flush=True)
            context.close()
        browser.close()
    return {'scope': 'Actual offline Chromium reader at desktop/mobile widths; reduced motion.',
            'limitations': 'Not human accessibility certification; clipboard text selection is not an operating-system clipboard guarantee.',
            'records': records,
            'status': 'PASS' if all(r['status'] == 'PASS' for r in records) else 'FAIL'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    args = parser.parse_args()
    static = static_checks()
    (ROOT / 'package-validation.json').write_text(json.dumps(static, indent=2)+'\n', encoding='utf-8')
    print('Static checks:', static['status'])
    status = static['status'] == 'PASS'
    if args.browser:
        browser = browser_checks()
        (ROOT / 'reader-validation.json').write_text(json.dumps(browser, indent=2)+'\n', encoding='utf-8')
        status = status and browser['status'] == 'PASS'
    raise SystemExit(0 if status else 1)
