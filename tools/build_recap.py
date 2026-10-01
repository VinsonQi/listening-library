#!/usr/bin/env python3
"""Build an A4 Listening Library recap from one self-contained lesson directory.

Usage:
    python build_recap_reusable.py path/to/lesson
    python build_recap_reusable.py path/to/lesson --check
    python build_recap_reusable.py path/to/lesson --output /tmp/preview.pdf

Inputs: lesson.json + transcript.txt; metadata.json + script.txt are fallbacks.
Required metadata: title; source.title + source.url; vocabulary entries with
term + definition. All original lesson metadata fields are supported. Optional
fields include summary, level, language_name, topics/category/tags, word_count
(or words), collection_name, lesson_number, footer_text, created_date,
source.{authors,publication_date,year,journal,volume,article_number,doi,doi_url,
license,license_url,accessed_on}, checked_on, attribution, scope_note, and
additional_sources. Vocabulary examples and highlight_forms are optional.
No source facts, source year, check date, lesson number, or topic is hard-coded.
The narration is never rewritten. An optional script_sha256/transcript_sha256
is enforced. Existing PDF files are protected unless --force is given.

Requirements: Python >=3.10 and ReportLab >=4.0,<5 (tested with Python 3.12.14,
ReportLab 4.4.9). Install with: python -m pip install 'reportlab>=4.0,<5'.
Fonts: Liberation Serif Regular/Bold/Italic and Liberation Sans Regular/Bold
TTFs. On Debian/Ubuntu these are supplied by fonts-liberation or
fonts-liberation2. Use --font-dir or LISTENING_PDF_FONT_DIR for another location.
Output verification: Poppler pdftoppm/pdfinfo; optional pypdf >=5 and pdfplumber
>=0.11 for text/link QA (tested with pypdf 6.10.0 and pdfplumber 0.11.8).
Always render and inspect the finished PDF before publishing it. This helper
performs no upload, sharing, network request, or Site operation.
"""
from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph

FONT_FILES = {
    'Text': 'LiberationSerif-Regular.ttf', 'TextBold': 'LiberationSerif-Bold.ttf',
    'TextItalic': 'LiberationSerif-Italic.ttf', 'Sans': 'LiberationSans-Regular.ttf',
    'SansBold': 'LiberationSans-Bold.ttf',
}
W, H = A4
LEFT = RIGHT = 54
TOP, BOTTOM = 51, 54
GRAY = colors.HexColor('#59645F')


def text(value) -> str:
    """Escape metadata for ReportLab markup without interpreting its contents."""
    return escape(str(value))


def date_label(value) -> str:
    """Format an ISO date; retain other date precision/format without guessing."""
    raw = str(value or '').strip()
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        return raw
    months = ('January February March April May June July August September '
              'October November December').split()
    return f'{parsed.day} {months[parsed.month - 1]} {parsed.year}'


def publication_year(source: dict) -> str:
    value = source.get('year') or source.get('publication_date', '')
    match = re.match(r'^\d{4}', str(value))
    return match.group() if match else ''


def joined_names(names) -> str:
    if isinstance(names, str):
        return names
    names = [str(name) for name in (names or []) if str(name).strip()]
    if len(names) < 2:
        return ''.join(names)
    if len(names) == 2:
        return ' and '.join(names)
    return ', '.join(names[:-1]) + ', and ' + names[-1]


def safe_url(value) -> str:
    value = str(value or '').strip()
    parsed = urlparse(value)
    if parsed.scheme not in ('https', 'http') or not parsed.netloc:
        raise ValueError(f'Expected an absolute http(s) source URL, got {value!r}')
    return value


def link(url, label) -> str:
    return f'<a href="{escape(safe_url(url), quote=True)}" color="#245C49"><u>{text(label)}</u></a>'


def register_fonts(requested: str | None) -> Path:
    candidates = [requested, os.environ.get('LISTENING_PDF_FONT_DIR'),
                  '/usr/share/fonts/truetype/liberation',
                  '/usr/share/fonts/truetype/liberation2']
    for candidate in candidates:
        if candidate and all((Path(candidate) / f).is_file() for f in FONT_FILES.values()):
            folder = Path(candidate)
            break
    else:
        raise ValueError('Liberation fonts not found. Supply --font-dir containing: ' + ', '.join(FONT_FILES.values()))
    for name, filename in FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(name, str(folder / filename)))
    pdfmetrics.registerFontFamily('Text', normal='Text', bold='TextBold', italic='TextItalic', boldItalic='TextBold')
    pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='SansBold', italic='Sans', boldItalic='SansBold')
    return folder


def styles() -> dict:
    values = {
        'eyebrow': ('SansBold', 9, 12, '#59645F', 11),
        'title': ('SansBold', 25, 29, '#161B1C', 11),
        'summary': ('Text', 12.5, 17.5, '#1E2423', 10),
        'meta': ('Sans', 9.5, 14, '#59645F', 11),
        'h1': ('SansBold', 17, 22, '#161B1C', 12),
        'h2': ('SansBold', 11.3, 15, '#161B1C', 7),
        'body': ('Text', 12.1, 17.2, '#1E2423', 9),
        'note': ('Sans', 9.5, 14, '#59645F', 12),
        'gloss': ('Text', 11.8, 16.2, '#1E2423', 3),
        'example': ('TextItalic', 11, 15, '#59645F', 15),
        'source': ('Text', 11.5, 16.3, '#1E2423', 10),
        'link': ('Sans', 9.5, 14, '#245C49', 12),
    }
    result = {}
    for name, (font, size, leading, color, after) in values.items():
        result[name] = ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                                      textColor=colors.HexColor(color), spaceAfter=after,
                                      allowWidows=0, allowOrphans=0)
    for name in ('h1', 'h2'):
        result[name].spaceBefore = 8
        result[name].keepWithNext = True
    result['link'].wordWrap = 'CJK'
    return result


def load_lesson(folder: Path) -> tuple[dict, str, Path, Path]:
    metadata_path = next((folder / f for f in ('lesson.json', 'metadata.json') if (folder / f).is_file()), None)
    transcript_path = next((folder / f for f in ('transcript.txt', 'script.txt') if (folder / f).is_file()), None)
    if not metadata_path or not transcript_path:
        raise ValueError('The lesson directory needs lesson.json + transcript.txt (or metadata.json + script.txt).')
    meta = json.loads(metadata_path.read_text(encoding='utf-8'))
    if not isinstance(meta, dict) or not str(meta.get('title', '')).strip():
        raise ValueError('Metadata must be an object with a nonempty title.')
    source = meta.get('source')
    if not isinstance(source, dict) or not source.get('title') or not source.get('url'):
        raise ValueError('Metadata needs source.title and source.url.')
    safe_url(source['url'])
    raw_bytes = transcript_path.read_bytes()
    expected = meta.get('transcript_sha256') or meta.get('script_sha256')
    if expected and sha256(raw_bytes).hexdigest() != expected:
        raise ValueError(f'Transcript SHA-256 differs from metadata: {transcript_path}')
    script = raw_bytes.decode('utf-8')
    if not script.strip():
        raise ValueError('The transcript is empty.')
    vocabulary = meta.get('vocabulary', [])
    if not isinstance(vocabulary, list):
        raise ValueError('vocabulary must be an array.')
    seen = set()
    for item in vocabulary:
        if not isinstance(item, dict) or not item.get('term') or not item.get('definition'):
            raise ValueError('Each vocabulary entry needs term and definition.')
        term = str(item['term']).casefold()
        if term in seen:
            raise ValueError(f'Duplicate vocabulary term: {item["term"]}')
        seen.add(term)
    return meta, script, metadata_path, transcript_path


class Highlighter:
    def __init__(self, vocabulary):
        self.patterns = []
        self.seen = set()
        self.hits = []
        for entry in vocabulary:
            term = str(entry['term'])
            forms = entry.get('highlight_forms') or [term]
            if isinstance(forms, str):
                forms = [forms]
            # Accept an ordinary plural for terms introduced as simulations/pores.
            escaped = [re.escape(str(form)) for form in forms]
            if not entry.get('highlight_forms') and not term.endswith('s'):
                escaped.append(re.escape(term) + 's')
            pattern = re.compile(r'(?<!\w)(?:' + '|'.join(sorted(escaped, key=len, reverse=True)) + r')(?!\w)', re.I)
            self.patterns.append((term, pattern))

    def render(self, raw):
        candidates = [(m.start(), m.end(), term) for term, pattern in self.patterns
                      if term not in self.seen for m in pattern.finditer(raw)]
        candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        cursor, pieces = 0, []
        for start, end, term in candidates:
            if start < cursor or term in self.seen:
                continue
            pieces += [text(raw[cursor:start]), '<font backColor="#E6F1EA" color="#245C49"><b>' + text(raw[start:end]) + '</b></font>']
            cursor = end
            self.seen.add(term)
            self.hits.append({'term': term, 'shown': raw[start:end]})
        pieces.append(text(raw[cursor:]))
        return ''.join(pieces)


def short_line(value, font, size, width):
    """Avoid header/footer collisions without shrinking readable type."""
    value = str(value).replace('\n', ' ')
    if pdfmetrics.stringWidth(value, font, size) <= width:
        return value
    while value and pdfmetrics.stringWidth(value + '...', font, size) > width:
        value = value[:-1]
    return value.rstrip() + '...'


class RecapDoc(BaseDocTemplate):
    def __init__(self, path, meta, footer):
        self.lesson_title = str(meta['title'])
        self.footer = footer
        super().__init__(str(path), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
                         topMargin=TOP, bottomMargin=BOTTOM, title=self.lesson_title,
                         author=str(meta.get('collection_name') or 'Listening Library'),
                         subject='Complete listening script, glossary, and research sources', pageCompression=1)
        frame = Frame(LEFT, BOTTOM, W-LEFT-RIGHT, H-TOP-BOTTOM, id='body',
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='main', frames=[frame], onPage=self.decorate))

    def afterFlowable(self, flowable):
        if hasattr(flowable, 'section_key'):
            self.canv.bookmarkPage(flowable.section_key)
            self.canv.addOutlineEntry(flowable.getPlainText(), flowable.section_key, 0, False)

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(GRAY)
        if doc.page > 1:
            canvas.setFont('Sans', 8.3)
            canvas.drawString(LEFT, H-30, short_line(self.lesson_title, 'Sans', 8.3, W-LEFT-RIGHT))
        canvas.setFont('Sans', 8.2)
        canvas.drawString(LEFT, 29, short_line(self.footer, 'Sans', 8.2, W-LEFT-RIGHT-35))
        canvas.drawRightString(W-RIGHT, 29, str(doc.page))
        canvas.restoreState()


def make_story(meta, script):
    st = styles()
    def paragraph(value, style='source'):
        return Paragraph(value, st[style])
    def heading(value, key):
        item = paragraph(text(value), 'h1')
        item.section_key = key
        return item

    collection = str(meta.get('collection_name') or 'Listening Library')
    number = meta.get('lesson_number')
    label = f'Lesson {number}' if number is not None else str(meta['title'])
    footer = str(meta.get('footer_text') or f'{collection}  |  {label}')
    eyebrow = collection + (f'  /  Lesson {number}' if number is not None else '')
    story = [paragraph(text(eyebrow.upper()), 'eyebrow'), paragraph(text(meta['title']), 'title')]
    if meta.get('summary'):
        story.append(paragraph(text(meta['summary']), 'summary'))
    metadata = []
    if meta.get('level'):
        language = meta.get('language_name') or ('English' if meta.get('language') == 'en' else '')
        metadata.append((str(meta['level']) + ' ' + language).strip())
    topics = meta.get('topics') or meta.get('category') or meta.get('tags')
    if topics:
        metadata.append(', '.join(str(v) for v in topics) if isinstance(topics, list) else str(topics))
    count = meta.get('word_count', meta.get('words'))
    if count is None:
        count = len(re.findall(r"\b\w+(?:['’-]\w+)*\b", script))
    metadata.append(f'{int(count):,} words')
    if meta.get('created_date'):
        metadata.append(date_label(meta['created_date']))
    story.append(paragraph('  |  '.join(text(value) for value in metadata), 'meta'))
    source = meta['source']
    year = publication_year(source)
    authors = joined_names(source.get('authors'))
    source_summary = (text(authors) + (f' ({year})' if year else '') + ', ') if authors else ''
    source_summary += '<i>' + text(source.get('journal') or source['title']) + '</i>. '
    story += [paragraph('Research source: ' + source_summary + link(source['url'], 'Read the original study') + '.', 'note'), heading('Full listening script', 'script')]
    vocabulary = meta.get('vocabulary', [])
    if vocabulary:
        story.append(paragraph('Highlighted words appear in the plain-English glossary after the script.', 'note'))
    highlighter = Highlighter(vocabulary)
    for raw in re.split(r'\r?\n\s*\r?\n', script.strip()):
        story.append(paragraph(highlighter.render(raw), 'body'))
    missing = [v['term'] for v in vocabulary if v['term'] not in highlighter.seen]
    if missing:
        raise ValueError('Glossary terms absent from the transcript; supply highlight_forms or fix metadata: ' + ', '.join(missing))

    if vocabulary:
        story += [PageBreak(), heading('Useful words', 'glossary'), paragraph('Plain-English meanings in the order supplied, with usage examples where available.', 'note')]
        # At most twelve entries per planned section avoids a sparse overflow page;
        # very long entries may still flow naturally and require visual QA.
        page_count = max(1, (len(vocabulary) + 11) // 12)
        per_page = (len(vocabulary) + page_count - 1) // page_count
        for index, entry in enumerate(vocabulary):
            if index and index % per_page == 0:
                story += [PageBreak(), heading('Useful words continued', f'glossary-{index}')]
            group = [paragraph('<b>' + text(entry['term']) + ':</b>  ' + text(entry['definition']), 'gloss')]
            if entry.get('example'):
                group.append(paragraph('Example: ' + text(entry['example']), 'example'))
            story.append(KeepTogether(group))

    citation = (text(authors) + (f' ({year})' if year else '') + '. ') if authors else (f'{year}. ' if year else '')
    citation += text(source['title']) + '. '
    if source.get('journal'):
        citation += '<i>' + text(source['journal']) + '</i>'
        if source.get('volume'):
            citation += ', ' + text(source['volume'])
        if source.get('article_number'):
            citation += ':' + text(source['article_number'])
        citation += '. '
    if source.get('publication_date'):
        citation += 'Published ' + text(date_label(source['publication_date'])) + '.'
    story += [PageBreak(), heading('Sources and attribution', 'sources'), paragraph('Original research', 'h2'), paragraph(citation)]
    if source.get('doi'):
        doi_url = source.get('doi_url') or 'https://doi.org/' + str(source['doi'])
        story.append(paragraph(link(doi_url, 'doi:' + str(source['doi'])), 'link'))
    story.append(paragraph(link(source['url'], source['url']), 'link'))
    if source.get('license'):
        license_text = link(source['license_url'], source['license']) if source.get('license_url') else text(source['license'])
        story.append(paragraph('Source license: ' + license_text + '.'))
    if meta.get('attribution'):
        story.append(paragraph(text(meta['attribution'])))
    if meta.get('scope_note'):
        story += [paragraph('How to read the evidence', 'h2'), paragraph(text(meta['scope_note']))]
    if meta.get('additional_sources') or meta.get('supporting_sources'):
        story.append(paragraph('Additional sources', 'h2'))
        for additional in meta.get('additional_sources') or meta.get('supporting_sources', []):
            value = link(additional['url'], additional['title'])
            if additional.get('purpose') or additional.get('role'):
                value += '<br/>' + text(additional.get('purpose') or additional['role']).rstrip('.') + '.'
            if additional.get('license'):
                label = link(additional['license_url'], additional['license']) if additional.get('license_url') else text(additional['license'])
                value += '<br/>License: ' + label + '.'
            story.append(paragraph(value))
    checked_on = meta.get('checked_on') or meta.get('source_checked_on') or source.get('accessed_on') or source.get('checked_on')
    if checked_on:
        story.append(paragraph('Sources checked on ' + text(date_label(checked_on)) + '.', 'note'))
    return story, footer, highlighter.hits


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('lesson_directory', type=Path)
    parser.add_argument('--output', type=Path, help='PDF destination (default: LESSON_DIRECTORY/recap.pdf)')
    parser.add_argument('--font-dir', help='Directory containing the five required Liberation TTFs')
    parser.add_argument('--force', action='store_true', help='Allow replacement of an existing PDF')
    parser.add_argument('--check', action='store_true', help='Validate inputs, fonts, and glossary without writing files')
    args = parser.parse_args(argv)
    try:
        folder = args.lesson_directory.expanduser().resolve()
        meta, script, metadata_path, transcript_path = load_lesson(folder)
        font_dir = register_fonts(args.font_dir)
        story, footer, highlights = make_story(meta, script)
        result = {'title': meta['title'], 'metadata': str(metadata_path), 'transcript': str(transcript_path),
                  'transcript_sha256': sha256(transcript_path.read_bytes()).hexdigest(),
                  'highlighted_terms': len(highlights), 'font_directory': str(font_dir)}
        if not args.check:
            output = (args.output or folder / 'recap.pdf').expanduser().resolve()
            if output.exists() and not args.force:
                raise ValueError(f'Output exists; choose --output or explicitly use --force: {output}')
            output.parent.mkdir(parents=True, exist_ok=True)
            # Build beside the destination and replace only after successful completion.
            temporary = output.with_name(output.name + '.building')
            try:
                document = RecapDoc(temporary, meta, footer)
                document.build(story)
                temporary.replace(output)
            finally:
                temporary.unlink(missing_ok=True)
            result.update(output=str(output), page_count=document.page, bytes=output.stat().st_size)
        result['status'] = 'validated' if args.check else 'created; render and inspect before publication'
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
