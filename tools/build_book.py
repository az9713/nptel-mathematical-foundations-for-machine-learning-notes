"""Rebuild the offline reader from authored HTML and public source metadata."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- BOOK-CONTENT-START -->'
END = '<!-- BOOK-CONTENT-END -->'


def read(path):
    return path.read_bytes().decode('utf-8-sig')


def write(path, value):
    path.write_bytes(value.encode('utf-8'))


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def esc(value):
    return html.escape(str(value), quote=True)


def plain(value):
    return html.unescape(re.sub('<[^>]+>', '', value)).strip()


def body(document):
    if START in document:
        result = document.split(START, 1)[1].split(END, 1)[0]
        match = re.search(r'name="book-content-sha256" content="([a-f0-9]+)"', document)
        if match and digest(result) != match[1]:
            raise ValueError('Authored content changed after wrapping: inspect and rebind its digest.')
        return result
    match = re.search(r'<body\b[^>]*>([\s\S]*?)</body>', document, re.I)
    return match[1] if match else document


def page(title, content, course, chapter=False, previous=None, following=None):
    nav = [('index.html', 'Lectures'), ('book-overview.html', 'Study guide'),
           ('source-map.html', 'Source map'), ('references.html', 'References'),
           ('numerical-lab.html', 'Numerical lab')]
    links = ''.join(f'<a href="{url}">{label}</a>' for url, label in nav)
    turns = ''
    if chapter:
        back = (f'<a rel="prev" href="{esc(previous)}">Previous chapter</a>'
                if previous else '<span>First chapter</span>')
        ahead = (f'<a rel="next" href="{esc(following)}">Next chapter</a>'
                 if following else '<span>End of book</span>')
        turns = f'<nav class="page-turn" aria-label="Chapter navigation">{back}<a href="index.html">Lecture index</a>{ahead}</nav>'
    toc = '<aside class="toc" id="chapter-toc" aria-label="On this page"><h2>On this page</h2></aside>' if chapter else ''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light"><meta name="book-content-sha256" content="{digest(content)}">
<title>{esc(title)} · {esc(course['course'])}</title><link rel="stylesheet" href="assets/book.css">
<script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']],processEscapes:true}},svg:{{fontCache:'local'}},options:{{skipHtmlTags:['script','noscript','style','textarea','pre','code']}}}};</script>
<script defer src="assets/mathjax-tex-svg.js"></script><script defer src="assets/book.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="index.html">{esc(course['course'])} · NPTEL</a><nav class="course-nav" aria-label="Book">{links}</nav></header>
<div class="layout{'' if chapter else ' no-toc'}">{toc}<main id="main"><div class="reading-tools" aria-label="Reading controls"><button id="theme-toggle" aria-pressed="false">Light theme</button><button id="text-toggle" aria-pressed="false">Larger text</button><button id="solutions-toggle" aria-pressed="false">Expand solutions</button><button id="print-page">Print with solutions</button></div>
<article id="chapter-content">{START}{content}{END}</article>{turns}</main></div>
<footer class="site-footer">Independent educational edition of the NPTEL IISc Bangalore / NITK Surathkal course by Ashok Rao and Arulalan Rajan. Recordings supply the chronological topic sequence; original exposition, constructions, and external results are separately attributed. Source and validation records state the evidence and its limits.</footer></body></html>'''


def build(support_only=False):
    manifest = json.loads(read(ROOT / 'source-manifest.json'))
    chapters = manifest['chapters']
    complete = all(c.get('chapter_status') == 'reviewed and locally validated' for c in chapters)
    rows = []
    source_rows = []
    source_map = []
    for index, chapter in enumerate(chapters):
        path = ROOT / chapter['file']
        if not path.exists():
            raise FileNotFoundError(path.name)
        content = body(read(path))
        if not support_only:
            previous = chapters[index-1]['file'] if index else None
            following = chapters[index+1]['file'] if index+1 < len(chapters) else None
            write(path, page(f"{chapter['order']}. {chapter['title']}", content,
                             manifest, True, previous, following))
        recordings = [v for v in manifest['lectures'] if v['chapter_order'] == chapter['order']]
        labels = ', '.join('Introduction' if v['lecture_number'] == 0 else str(v['lecture_number']) for v in recordings)
        status = 'Complete chapter' if complete else esc(chapter.get('chapter_status', 'Draft'))
        rows.append(f'<li data-lecture><h2><a href="{esc(path.name)}">{chapter["order"]:02d}. {esc(chapter["title"])}</a></h2><div class="lecture-meta">Source lectures: {labels} · <span class="status">{status}</span></div></li>')
        for recording in recordings:
            source_rows.append(f'<tr><td>{"Introduction" if recording["lecture_number"] == 0 else recording["lecture_number"]}</td><td>{recording["playlist_position"]}</td><td><a href="{esc(recording["url"])}">{esc(recording["title"])}</a></td><td>{recording["duration_seconds"]//60}:{recording["duration_seconds"]%60:02d}</td><td><a href="{esc(path.name)}">Chapter {chapter["order"]}</a></td></tr>')
        sections = []
        for match in re.finditer(r'<h[23]\b([^>]*)>([\s\S]*?)</h[23]>', content):
            anchor = re.search(r'\bid=["\']([^"\']+)', match[1])
            timestamps = re.findall(r'href=["\'](https://www.youtube.com/[^"\']+)', match[2])
            if timestamps:
                sections.append({'heading': plain(match[2]), 'anchor': anchor[1] if anchor else None,
                                 'recording_urls': [html.unescape(u) for u in timestamps]})
        source_map.append({'chapter': chapter['order'], 'file': path.name,
                           'lectures': chapter['lecture_numbers'], 'sections': sections})
    intro = f'''<h1>Mathematical Foundations for Machine Learning</h1><p class="lead">From vector spaces and probability laws to optimization and learning algorithms: an independent textbook edition of all 70 numbered NPTEL lectures, with the course introduction included.</p>
<p>Ashok Rao · IISc Bangalore; Arulalan Rajan · NITK Surathkal. The <a href="{esc(manifest['playlist_url'])}">source playlist</a> is displayed in reverse order on YouTube. This edition follows ascending lecture numbers across 26 topic chapters.</p>
<p>{'Complete reading edition.' if complete else 'Edition in preparation; draft pages are not scientific acceptance.'} Derivations, original worked cases, executable examples, and fully worked exercises develop the lecture topics. <a href="book-overview.html">Choose a study route</a> or inspect the <a href="source-map.html">recording and timestamp map</a>.</p>
<label class="search-label" for="lecture-search">Find a chapter or topic</label><input id="lecture-search" type="search" placeholder="Try covariance, eigenvectors, or backpropagation"><p id="search-status" role="status">26 chapters shown</p><ul class="lecture-list">{''.join(rows)}</ul>'''
    write(ROOT / 'index.html', page('Lecture index', intro, manifest))
    ledger = '<h1>Recording and timestamp map</h1><p>All 71 playlist entries are assigned exactly once. Original playlist positions are preserved alongside ascending lecture numbers. A timestamp locates related lecture discussion; it does not attribute every added proof, example, or research extension to the instructors.</p><table><thead><tr><th>Lecture</th><th>Playlist position</th><th>Source recording</th><th>Duration</th><th>Chapter</th></tr></thead><tbody>' + ''.join(source_rows) + '</tbody></table>'
    for item in source_map:
        links = ''.join(f'<li><a href="{esc(item["file"])}#{esc(s["anchor"] or "")}">{esc(s["heading"])}</a></li>' for s in item['sections'])
        ledger += f'<h2 id="chapter-{item["chapter"]}">Chapter {item["chapter"]}</h2><ul>{links}</ul>'
    write(ROOT / 'source-map.html', page('Recording and timestamp map', ledger, manifest))
    write(ROOT / 'source-map.json', json.dumps(source_map, ensure_ascii=False, indent=2)+'\n')
    for name in ('book-overview.html', 'references.html', 'numerical-lab.html'):
        path = ROOT / name
        if path.exists():
            content = body(read(path))
            title = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', content)
            write(path, page(plain(title[1]) if title else path.stem, content, manifest))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--support-only', action='store_true', help='Do not wrap chapter drafts.')
    args = parser.parse_args()
    build(args.support_only)
