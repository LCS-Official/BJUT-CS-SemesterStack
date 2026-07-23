from pathlib import Path
from docx import Document


for name in ["计网课设实验报告-LC.docx", "计算机网络课程设计要求.docx"]:
    print(f"===== {name} =====")
    doc = Document(name)
    for i, p in enumerate(doc.paragraphs[:260]):
        text = p.text.strip()
        if not text:
            continue
        style = p.style.name if p.style else ""
        print(f"{i:03d} [{style}] {text[:160]}")
    print()
