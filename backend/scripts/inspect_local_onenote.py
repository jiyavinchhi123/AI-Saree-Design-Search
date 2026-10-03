import os
import glob
import subprocess

def inspect_local():
    print("Checking OneNote running status...")
    out = subprocess.check_output('tasklist /FI "IMAGENAME eq ONENOTE.EXE" /FO CSV /NH', shell=True).decode()
    print("OneNote process:", out.strip())

    backup_root = os.path.expanduser(r"~\AppData\Local\Microsoft\OneNote\16.0\Backup")
    print("\nBackup folder:", backup_root, "Exists:", os.path.exists(backup_root))
    if os.path.exists(backup_root):
        for root, dirs, files in os.walk(backup_root):
            for f in files:
                if f.endswith(".one"):
                    print("  Found backup .one:", os.path.join(root, f))

    docs_roots = [
        os.path.expanduser(r"~\Documents\OneNote Notebooks"),
        os.path.expanduser(r"~\OneDrive\Documents\OneNote Notebooks"),
        os.path.expanduser(r"~\OneDrive\OneNote Notebooks"),
        os.path.expanduser(r"~\AppData\Local\Microsoft\OneNote\16.0\cache"),
    ]
    for d in docs_roots:
        print(f"\nChecking: {d} (Exists: {os.path.exists(d)})")
        if os.path.exists(d):
            for root, dirs, files in os.walk(d):
                for f in files:
                    if f.endswith(".one") or f.endswith(".onetoc2"):
                        print("  Found:", os.path.join(root, f))

if __name__ == "__main__":
    inspect_local()
