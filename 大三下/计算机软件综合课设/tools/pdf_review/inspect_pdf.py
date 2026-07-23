from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz


def main() -> None:
    source = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    pages_dir = output / "pages"
    pages_dir.mkdir(exist_ok=True)

    document = fitz.open(source)
    report = {
        "path": str(source),
        "page_count": document.page_count,
        "metadata": document.metadata,
        "toc": document.get_toc(),
        "embedded_files": document.embfile_names(),
        "pages": [],
    }
    all_text = []
    for number, page in enumerate(document, start=1):
        text = page.get_text("text")
        all_text.append(f"\n\n===== PAGE {number} =====\n{text}")
        annotations = []
        annotation = page.first_annot
        while annotation:
            annotations.append(
                {
                    "type": annotation.type,
                    "content": annotation.info.get("content", ""),
                    "title": annotation.info.get("title", ""),
                    "subject": annotation.info.get("subject", ""),
                }
            )
            annotation = annotation.next
        report["pages"].append(
            {
                "number": number,
                "width": page.rect.width,
                "height": page.rect.height,
                "rotation": page.rotation,
                "text_chars": len(text),
                "images": len(page.get_images(full=True)),
                "links": len(page.get_links()),
                "annotations": annotations,
                "widgets": sum(1 for _ in (page.widgets() or [])),
            }
        )
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        pixmap.save(pages_dir / f"page-{number:02d}.png")

    (output / "document.txt").write_text("".join(all_text), encoding="utf-8")
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
