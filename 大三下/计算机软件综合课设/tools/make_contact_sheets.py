import sys
from pathlib import Path

from PIL import Image, ImageDraw


source = Path(sys.argv[1])
output = Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=True)
pages = sorted(source.glob("page-*.png"), key=lambda path: int(path.stem.split("-")[-1]))

for offset in range(0, len(pages), 4):
    batch = pages[offset : offset + 4]
    opened = [Image.open(path).convert("RGB") for path in batch]
    width = max(image.width for image in opened)
    height = max(image.height for image in opened)
    sheet = Image.new("RGB", (width * 2 + 30, (height + 30) * 2 + 30), "#666666")
    draw = ImageDraw.Draw(sheet)
    for index, (path, page) in enumerate(zip(batch, opened)):
        x = (index % 2) * (width + 30)
        y = (index // 2) * (height + 30) + 30
        draw.text((x + 6, y - 24), f"Page {path.stem.split('-')[-1]}", fill="white")
        sheet.paste(page, (x, y))
    sheet.save(output / f"sheet-{offset // 4 + 1:02d}.jpg", quality=90)

print(len(pages), "pages ->", (len(pages) + 3) // 4, "sheets")
