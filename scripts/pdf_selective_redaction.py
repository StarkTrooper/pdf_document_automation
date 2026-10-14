"""Rule-driven selective redaction of structured PDFs.

Example:
 python scripts/pdf_selective_redaction.py ./input --config examples/redaction_config.json

Rules are intentionally template-specific. Do not treat a successful run as a
privacy certification; inspect output and use an independent visual check.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import fitz


def discover(root: Path, output_dir: str):
    return sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf'
                  and output_dir.casefold() not in (part.casefold() for part in p.relative_to(root).parts[:-1]))


def match_page(page: fitz.Page, cfg: dict) -> bool:
    signature = cfg.get('page_contains')
    return not signature or signature.casefold() in page.get_text().casefold()


def collect(page: fitz.Page, cfg: dict):
    """Return rectangles and text fragments expected to disappear."""
    words = [(fitz.Rect(w[:4]), w[4]) for w in page.get_text('words')]
    regions = [fitz.Rect(v) for v in cfg.get('regions', [])]
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in cfg.get('word_patterns', [])]
    targets = []
    for rect, word in words:
        if regexes and any(pattern.fullmatch(word) for pattern in regexes):
            targets.append((rect + (-0.5, -0.5, 0.5, 0.5), word))
        elif regions and any(region.contains(rect) for region in regions):
            targets.append((rect + (-0.5, -0.5, 0.5, 0.5), word))
    for rule in cfg.get('below_anchor', []):
        anchors = page.search_for(rule['text'])
        if len(anchors) != 1:
            raise ValueError(f"expected one anchor '{rule['text']}', found {len(anchors)}")
        anchor = anchors[0]
        area = fitz.Rect(max(0, anchor.x0 + rule.get('left_offset', 0)),
                         anchor.y1 + rule.get('top_offset', 0),
                         min(page.rect.width, anchor.x0 + rule.get('width', 350)),
                         anchor.y1 + rule.get('height', 16))
        if area.is_empty:
            raise ValueError('empty below_anchor region')
        matches = [(rect, word) for rect, word in words if area.contains(rect)]
        if rule.get('required', True) and not matches:
            raise ValueError(f"no words below '{rule['text']}'")
        targets.extend((rect + (-0.4, -0.4, 0.4, 0.4), word) for rect, word in matches)
    # Image removal is opt-in, scoped to explicit rectangles.
    for box in cfg.get('image_regions', []):
        area = fitz.Rect(box)
        images = [fitz.Rect(i['bbox']) for i in page.get_image_info() if area.contains(fitz.Rect(i['bbox']))]
        if not images and cfg.get('require_images', False):
            raise ValueError('expected image not found in image_regions')
        targets.extend((rect, None) for rect in images)
    return targets


def process(source: Path, target: Path, cfg: dict) -> int:
    with fitz.open(source) as doc:
        pages = len(doc)
        expected = []
        matched_pages = 0
        for index, page in enumerate(doc):
            if not match_page(page, cfg):
                expected.append([])
                continue
            matched_pages += 1
            try:
                targets = collect(page, cfg)
            except Exception as exc:
                raise ValueError(f'page {index + 1}: {exc}') from exc
            expected.append(targets)
            for rect, _ in targets:
                page.add_redact_annot(rect, fill=(1, 1, 1), cross_out=False)
            if targets:
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS,
                                      graphics=0, text=fitz.PDF_REDACT_TEXT_REMOVE)
        if not matched_pages or not any(expected):
            raise ValueError('no targets detected; output not generated')
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.stem + '.pending.pdf')
        try:
            doc.save(tmp, garbage=4, deflate=True)
            with fitz.open(tmp) as check:
                if len(check) != pages:
                    raise ValueError('page count changed')
                for idx, targets in enumerate(expected):
                    remaining = [(fitz.Rect(w[:4]), w[4]) for w in check[idx].get_text('words')]
                    for rect, word in targets:
                        if word is not None and any(word == value and rect.intersects(box) for box, value in remaining):
                            raise ValueError(f'page {idx + 1}: targeted text remains')
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
    return sum(map(len, expected))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output-dir', default='modified_pdfs')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('root must be a directory')
    cfg = json.loads(args.config.read_text(encoding='utf-8'))
    failures = 0
    for source in discover(args.root, args.output_dir):
        dest = source.parent / args.output_dir / source.name
        if dest.exists() and not args.overwrite:
            print(f'[SKIP] {source}: output exists')
            continue
        if args.dry_run:
            print(f'[DRY_RUN] {source} -> {dest}')
            continue
        try:
            count = process(source, dest, cfg)
            print(f'[OK] {source}: {count} targets')
        except Exception as exc:
            failures += 1
            print(f'[REVIEW] {source}: {exc}')
    return int(failures > 0)


if __name__ == '__main__':
    sys.exit(main())
