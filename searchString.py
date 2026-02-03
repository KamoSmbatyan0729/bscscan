import os
from typing import Iterable, Tuple

def get_patterns(text: str, mode: str) -> Iterable[Tuple[str, bytes]]:
    """
    Returns (label, bytes_pattern) to search for.
    mode:
      - "plain"   : UTF-8 bytes (matches ASCII too)
      - "utf16le" : UTF-16 LE bytes
      - "both"    : search both encodings
    """
    mode = mode.lower().strip()
    if mode == "plain":
        return [("plain(utf-8)", text.encode("utf-8", errors="strict"))]
    if mode == "utf16le":
        return [("utf16le", text.encode("utf-16-le", errors="strict"))]
    if mode == "both":
        return [
            ("plain(utf-8)", text.encode("utf-8", errors="strict")),
            ("utf16le", text.encode("utf-16-le", errors="strict")),
        ]
    raise ValueError('mode must be "plain", "utf16le", or "both"')


def search_text_in_dlls(root_dir: str, text: str, mode: str = "plain"):
    patterns = list(get_patterns(text, mode))

    print(f'Folder: {root_dir}')
    print(f'Text: "{text}"')
    print(f"Mode: {mode}\n")

    for root, dirs, files in os.walk(root_dir):
        for name in files:

            path = os.path.join(root, name)
            try:
                with open(path, "rb") as f:
                    data = f.read()

                for label, pat in patterns:
                    offset = data.find(pat)
                    if offset != -1:
                        print(f"[FOUND:{label}] {path} @ offset 0x{offset:X}")

            except Exception as e:
                print(f"[ERROR] {path}: {e}")


# ====== CONFIG ======
ROOT_DIR = r"D:\DevTools\Crack\SprutCAM X Robot 17"
SEARCH_TEXT = "Last time start was in the future"
MODE = "both"   # "plain" or "utf16le" or "both"
# ====================

search_text_in_dlls(ROOT_DIR, SEARCH_TEXT, MODE)
