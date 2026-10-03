import uuid
import struct

file_path = r"C:\Users\jiyav\AppData\Local\Microsoft\OneNote\16.0\Backup\My Notebook\New Section 2 (On 25-09-2026).one"
with open(file_path, "rb") as f:
    data = f.read()

# Let's inspect the area around position 5142 where "Saree designs" was found
p = 5142
# Look 512 bytes before and after
chunk = data[p-512:p+512]

# Search for any 16-byte sequences that look like GUIDs (non-zero, random-looking)
print(f"Scanning for GUIDs near page title at offset {p}...")
found_guids = []
for i in range(0, len(chunk)-16, 4):
    cand = chunk[i:i+16]
    # Check if not all zeros or all 0xFF
    if cand.count(b'\x00') < 10 and cand.count(b'\xff') < 10:
        try:
            g = uuid.UUID(bytes_le=cand)
            found_guids.append((p-512+i, str(g)))
        except:
            pass

print(f"Found {len(found_guids)} candidate GUIDs near title:")
for offset, g in found_guids[:15]:
    print(f"  Offset {offset}: {g}")
