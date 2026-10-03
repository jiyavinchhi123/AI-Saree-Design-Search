import uuid

file_path = r"C:\Users\jiyav\AppData\Local\Microsoft\OneNote\16.0\Backup\My Notebook\New Section 2 (On 25-09-2026).one"
with open(file_path, "rb") as f:
    header = f.read(1024)

# [MS-ONESTORE] FileHeader:
# 0..16: guidFileType
# 16..32: guidFile
# 32..48: guidLegacyFileVersion
# 48..64: guidFileFormat
guid_file_type = uuid.UUID(bytes_le=header[0:16])
guid_file = uuid.UUID(bytes_le=header[16:32])
guid_legacy = uuid.UUID(bytes_le=header[32:48])
guid_format = uuid.UUID(bytes_le=header[48:64])

print("guidFileType:", guid_file_type)
print("guidFile (Section GUID):", guid_file)
print("guidLegacy:", guid_legacy)
print("guidFormat:", guid_format)
