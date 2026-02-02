import os

# UTF-16 LE bytes for "protection violation"
pattern = bytes([
     0x70,0x00,0x72,0x00,0x6F,0x00,0x74,0x00,0x65,0x00,0x63,0x00,0x74,0x00,0x69,0x00,0x6F,0x00,0x6E,0x00,0x20,0x00,0x76,0x00,0x69,0x00,0x6F,0x00,0x6C,0x00,0x61,0x00,0x74,0x00,0x69,0x00,0x6F,0x00,0x6E,0x00])

# IMPORTANT: use raw string for Windows path
root_dir = r"D:\DevTools\Crack\SprutCAM X Robot 17"

for root, dirs, files in os.walk(root_dir):
    for name in files:
        if name.lower().endswith(".dll"):
            path = os.path.join(root, name)
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    offset = data.find(pattern)
                    if offset != -1:
                        print(f"[FOUND] {path} @ offset 0x{offset:X}")
            except Exception as e:
                print(f"[ERROR] {path}: {e}")
