import ctypes
import subprocess
import os

user32 = ctypes.windll.user32

def find_onenote_window():
    pids = []
    out = subprocess.check_output('tasklist /FI "IMAGENAME eq ONENOTE.EXE" /FO CSV /NH', shell=True).decode()
    for line in out.strip().splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            pids.append(int(parts[1]))
    
    hwnds = []
    def enum_cb(hwnd, lp):
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            hwnds.append((hwnd, buff.value))
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return hwnds

def activate_onenote():
    windows = find_onenote_window()
    print("Found OneNote windows:", windows)
    for hwnd, title in windows:
        # Restore and bring to foreground
        user32.ShowWindow(hwnd, 9) # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        print(f"Brought window {hwnd} ('{title}') to foreground")
        return True
    return False

if __name__ == "__main__":
    activate_onenote()
