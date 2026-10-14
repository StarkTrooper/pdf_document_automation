"""Replace a block between two unique text anchors in structured PDFs.

Example:
 python scripts/pdf_content_replacement.py ./input --config examples/replacement_config.json

All output is written to a sibling directory; originals are never modified.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import fitz


def discover(root: Path, output_dir: str):
    return sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf'
                  and output_dir.casefold() not in (part.casefold() for part in p.relative_to(root).parts[:-1]))


def replace_page(page: fitz.Page, cfg: dict) -> None:
    top_hits = page.search_for(cfg['top_anchor'])
    bottom_hits = page.search_for(cfg['bottom_anchor'])
    if len(top_hits) != 1:
        raise ValueError(f"top anchor matches: {len(top_hits)}")
    top = top_hits[0]
    below = [r for r in bottom_hits if r.y0 > top.y1 and r.y0 - top.y1 <= cfg.get('max_anchor_gap', 90)]
    if len(below) != 1:
        raise ValueError(f"bottom anchor matches: {len(below)}")
    bottom = below[0]
    keep_bottom = cfg.get('keep_bottom_anchor', False)
    erase_bottom = bottom.y0 - 1 if keep_bottom else bottom.y1 + 1
    erase = fitz.Rect(max(0, top.x0 - 1), top.y1 + 1,
                      min(page.rect.width, top.x0 + cfg.get('erase_width', 270)), erase_bottom)
    if erase.is_empty:
        raise ValueError('empty redaction area')
    lines = cfg['replacement_lines']
    if not lines or not all(isinstance(line, str) and line.strip() for line in lines):
        raise ValueError('replacement_lines must contain nonempty strings')
    font_size = float(cfg.get('font_size', 8))
    spacing = float(cfg.get('line_spacing', 11))
    start_y = top.y1 + float(cfg.get('first_line_offset', 12))
    if start_y + (len(lines) - 1) * spacing + 2 > erase.y1:
        raise ValueError('replacement would extend outside cleared region')
    for line in lines:
        if fitz.get_text_length(line, fontname='helv', fontsize=font_size) > page.rect.width - top.x0 - 8:
            raise ValueError('replacement line is wider than page; shorten it')
    page.add_redact_annot(erase, fill=(1, 1, 1), cross_out=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=0)
    if cfg.get('append_colon', False):
        page.insert_text((top.x1 + 0.7, top.y1 - 1), ':', fontname='hebo', fontsize=font_size)
    for idx, line in enumerate(lines):
        page.insert_text((top.x0, start_y + idx * spacing), line,
                         fontname='helv', fontsize=font_size)


def process(source: Path, target: Path, cfg: dict) -> int:
    with fitz.open(source) as doc:
        pages = len(doc)
        for idx, page in enumerate(doc):
            try:
                replace_page(page, cfg)
            except Exception as exc:
                raise ValueError(f'page {idx + 1}: {exc}') from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.stem + '.pending.pdf')
        try:
            doc.save(tmp, garbage=4, deflate=True)
            with fitz.open(tmp) as check:
                if len(check) != pages:
                    raise ValueError('page count changed')
                for page in check:
                    text = page.get_text()
                    if not all(line in text for line in cfg['replacement_lines']):
                        raise ValueError('replacement not found in output')
                    if not cfg.get('keep_bottom_anchor', False) and cfg['bottom_anchor'] in text:
                        raise ValueError('bottom anchor remains in output')
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
    return pages


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
            pages = process(source, dest, cfg)
            print(f'[OK] {source} ({pages} pages)')
        except Exception as exc:
            failures += 1
            print(f'[REVIEW] {source}: {exc}')
    return int(failures > 0)


if __name__ == '__main__':
    sys.exit(main())
