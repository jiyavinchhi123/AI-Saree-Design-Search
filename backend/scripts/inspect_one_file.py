import os
import re

file_path = r"C:\Users\jiyav\AppData\Local\Microsoft\OneNote\16.0\Backup\My Notebook\New Section 2 (On 25-09-2026).one"
print("Reading file:", file_path)
with open(file_path, "rb") as f:
    data = f.read()

print("File size:", len(data))

# Search for "Saree designs" in utf-16le and utf-8
utf16_title = "Saree designs".encode("utf-16le")
pos = 0
found_positions = []
while True:
    pos = data.find(utf16_title, pos)
    if pos == -1:
        break
    found_positions.append(pos)
    pos += len(utf16_title)

print(f"Found 'Saree designs' in utf-16 at {len(found_positions)} positions:", found_positions[:5])

# Extract all GUIDs in the file
# A GUID is 16 bytes. Let's look around the positions where Saree designs appears!
for p in found_positions[:3]:
    chunk = data[max(0, p-256):p+256]
    # Check for GUID patterns or hex representations
    print(f"\nContext around {p}:")
    # Printable strings in this chunk
    printable = "".join([chr(b) if 32 <= b < 127 else "." for b in chunk])
    print(printable)
