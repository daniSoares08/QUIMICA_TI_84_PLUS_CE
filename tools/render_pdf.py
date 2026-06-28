#!/usr/bin/env python
"""Render PDFs to PNG and extract text for CIRCVIE3 exercise intake."""

import argparse
import shutil
from pathlib import Path


def parse_page_spec(spec):
    if not spec:
        return None

    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start < 1 or end < start:
                raise ValueError("invalid page range: {}".format(part))
            pages.update(range(start, end + 1))
        else:
            page = int(part)
            if page < 1:
                raise ValueError("invalid page: {}".format(part))
            pages.add(page)
    return sorted(pages)


def should_process(page_number, selected_pages):
    return selected_pages is None or page_number in selected_pages


def render_pages(pdf_path, out_dir, scale, selected_pages):
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    rendered = []
    for index, page in enumerate(pdf, 1):
        if not should_process(index, selected_pages):
            continue
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        target = out_dir / "{}_p{:03d}.png".format(pdf_path.stem, index)
        image.save(target)
        rendered.append(target)
    return rendered


def extract_text(pdf_path, out_dir, selected_pages):
    import pdfplumber

    target = out_dir / "{}_text.txt".format(pdf_path.stem)
    with pdfplumber.open(str(pdf_path)) as pdf:
        with target.open("w", encoding="utf-8") as handle:
            for index, page in enumerate(pdf.pages, 1):
                if not should_process(index, selected_pages):
                    continue
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                handle.write("==== PAGE {} ====\n".format(index))
                handle.write(text)
                handle.write("\n\n")
    return target


def maybe_ocr(images, out_dir, enabled):
    if not enabled:
        return None
    if not shutil.which("tesseract"):
        print("OCR skipped: tesseract executable was not found in PATH.")
        return None

    import pytesseract
    from PIL import Image

    target = out_dir / "ocr_text.txt"
    with target.open("w", encoding="utf-8") as handle:
        for image_path in images:
            handle.write("==== {} ====\n".format(image_path.name))
            handle.write(pytesseract.image_to_string(Image.open(image_path)))
            handle.write("\n\n")
    return target


def write_manifest(pdf_path, out_dir, images, text_file, ocr_file):
    manifest = out_dir / "{}_manifest.md".format(pdf_path.stem)
    with manifest.open("w", encoding="utf-8") as handle:
        handle.write("# {}\n\n".format(pdf_path.name))
        handle.write("## Rendered pages\n\n")
        for image in images:
            handle.write("- `{}`\n".format(image.name))
        handle.write("\n## Extracted text\n\n")
        handle.write("- `{}`\n".format(text_file.name))
        if ocr_file:
            handle.write("- `{}`\n".format(ocr_file.name))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdfs", nargs="+", help="PDF files to process")
    parser.add_argument(
        "--out",
        default="sources/rendered",
        help="Output directory for PNG/text files",
    )
    parser.add_argument(
        "--pages",
        help="1-based pages or ranges, for example 12,48,50-52",
    )
    parser.add_argument("--scale", type=float, default=2.5)
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    try:
        selected_pages = parse_page_spec(args.pages)
    except ValueError as exc:
        raise SystemExit(str(exc))

    for pdf_name in args.pdfs:
        pdf_path = Path(pdf_name)
        if not pdf_path.exists():
            raise SystemExit("PDF not found: {}".format(pdf_path))
        pdf_out = out_root / pdf_path.stem
        pdf_out.mkdir(parents=True, exist_ok=True)
        images = render_pages(pdf_path, pdf_out, args.scale, selected_pages)
        text_file = extract_text(pdf_path, pdf_out, selected_pages)
        ocr_file = maybe_ocr(images, pdf_out, args.ocr)
        manifest = write_manifest(pdf_path, pdf_out, images, text_file, ocr_file)
        print("processed {}".format(pdf_path))
        print("manifest {}".format(manifest))


if __name__ == "__main__":
    main()
