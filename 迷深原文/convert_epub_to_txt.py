# -*- coding: utf-8 -*-
"""Convert EPUB to plain text using ebooklib."""
import os
import re
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

EPUB_PATH = Path(__file__).parent / "异世界迷宫最深部为目标 - 割内@タリサ.epub"
OUTPUT_DIR = Path(__file__).parent

# Volume 1 & 2 spine order from content.opf / toc.ncx
VOL1_FILES = [
    "text/第一卷.html",
    "text/第一章-异世界迷宫.html",
    "text/第二章-迷宫联合国.html",
    "text/第三章-梦的奴隶，奴隶的梦.html",
    "text/第四章-二十层阶处，魍魉沉影池。盼求君临至，直至黯逝时。.html",
    "text/第五章『我（私）』是迪亚布罗・西斯.html",
    "text/后记.html",
]

VOL2_FILES = [
    "text/第二卷.html",
    "text/第二卷-第一章-再掀挑战.html",
    "text/第二卷-第二章-谁才是奴隷.html",
    "text/第二卷-第三章-第四位同伴.html",
    "text/第二卷-第四章-队伍.html",
    "text/第二卷-第五章-分岐点『前祭』.html",
    "text/第二卷-后记.html",
]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_book(epub_path: Path):
    book = epub.read_epub(str(epub_path))
    items = {}
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()
        try:
            content = item.get_content().decode("utf-8", errors="replace")
        except Exception:
            content = item.get_content().decode("latin-1", errors="replace")
        items[name] = html_to_text(content)
    return items, book


def write_volume(items: dict, files: list, out_path: Path, title: str):
  parts = [f"{'=' * 60}\n{title}\n{'=' * 60}\n"]
  for f in files:
      if f in items:
          chapter_name = Path(f).stem
          parts.append(f"\n\n--- {chapter_name} ---\n\n")
          parts.append(items[f])
      else:
          parts.append(f"\n\n[缺失: {f}]\n\n")
  out_path.write_text("".join(parts), encoding="utf-8")
  print(f"Wrote {out_path} ({out_path.stat().st_size // 1024} KB)")


def main():
    items, book = extract_book(EPUB_PATH)

    # Full text in spine order
    full_parts = []
    for item in book.spine:
        idref = item[0] if isinstance(item, tuple) else item
        for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            if doc.id == idref:
                name = doc.get_name()
                if name in items and items[name]:
                    full_parts.append(f"\n\n{'=' * 40}\n{name}\n{'=' * 40}\n\n")
                    full_parts.append(items[name])
                break

    full_path = OUTPUT_DIR / "异世界迷宫最深部为目标_全文.txt"
    full_path.write_text("".join(full_parts), encoding="utf-8")
    print(f"Wrote {full_path} ({full_path.stat().st_size // 1024} KB)")

    write_volume(items, VOL1_FILES, OUTPUT_DIR / "异世界迷宫最深部为目标_第一卷.txt", "第一卷")
    write_volume(items, VOL2_FILES, OUTPUT_DIR / "异世界迷宫最深部为目标_第二卷.txt", "第二卷")


if __name__ == "__main__":
    main()
