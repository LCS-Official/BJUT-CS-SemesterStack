from __future__ import annotations

import argparse
from pathlib import Path

import fitz
import win32com.client


WD_FORMAT_DOCX = 16
WD_EXPORT_PDF = 17


def render_pdf(pdf_path: Path, output_dir: Path, dpi: int = 150) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    with fitz.open(pdf_path) as pdf:
        for index, page in enumerate(pdf):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(output_dir / f"page-{index + 1}.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--docx", type=Path)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--png-dir", type=Path, required=True)
    parser.add_argument("--update-fields", action="store_true")
    args = parser.parse_args()

    input_path = args.input.resolve()
    pdf_path = args.pdf.resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if args.docx:
        args.docx.resolve().parent.mkdir(parents=True, exist_ok=True)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    document = None
    try:
        document = word.Documents.Open(
            str(input_path),
            ConfirmConversions=False,
            ReadOnly=not args.update_fields,
            AddToRecentFiles=False,
            Visible=False,
            OpenAndRepair=True,
        )
        if args.docx:
            document.SaveAs2(str(args.docx.resolve()), FileFormat=WD_FORMAT_DOCX)
        if args.update_fields:
            document.Fields.Update()
            for story_type in range(1, 18):
                try:
                    story = document.StoryRanges(story_type)
                except Exception:
                    continue
                while story is not None:
                    try:
                        story.Fields.Update()
                        story = story.NextStoryRange
                    except Exception:
                        break
            document.Save()
        document.ExportAsFixedFormat(str(pdf_path), WD_EXPORT_PDF)
    finally:
        if document is not None:
            document.Close(False)
        word.Quit()

    render_pdf(pdf_path, args.png_dir.resolve())
    print(f"PDF: {pdf_path}")
    print(f"PNG: {args.png_dir.resolve()}")
    if args.docx:
        print(f"DOCX: {args.docx.resolve()}")


if __name__ == "__main__":
    main()
