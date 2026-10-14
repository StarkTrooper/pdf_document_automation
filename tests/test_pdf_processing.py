"""Synthetic PDF smoke tests; no real documents or identifiers."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pdf_content_replacement as replacement
import pdf_selective_redaction as redaction


class PDFProcessingTests(unittest.TestCase):
    def test_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.pdf'
            out = Path(directory) / 'modified.pdf'
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((40, 100), 'Shipping address', fontsize=8)
            page.insert_text((40, 120), 'Old address', fontsize=8)
            page.insert_text((40, 145), 'Reference number', fontsize=8)
            doc.save(path)
            doc.close()
            cfg = json.loads((ROOT / 'examples/replacement_config.json').read_text())
            self.assertEqual(replacement.process(path, out, cfg), 1)
            with fitz.open(out) as check:
                text = check[0].get_text()
                self.assertIn('Example Street 123', text)
                self.assertNotIn('Old address', text)

    def test_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.pdf'
            out = Path(directory) / 'modified.pdf'
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((40, 80), 'Sample invoice')
            page.insert_text((40, 110), 'Item: notebook')
            page.insert_text((40, 140), 'Price: $25.00')
            page.insert_text((40, 180), 'Amount in words')
            page.insert_text((40, 195), 'Twenty five dollars')
            doc.save(path)
            doc.close()
            cfg = json.loads((ROOT / 'examples/redaction_config.json').read_text())
            self.assertGreater(redaction.process(path, out, cfg), 0)
            with fitz.open(out) as check:
                text = check[0].get_text()
                self.assertIn('Item: notebook', text)
                self.assertNotIn('$25.00', text)
                self.assertNotIn('Twenty five dollars', text)


if __name__ == '__main__':
    unittest.main()
