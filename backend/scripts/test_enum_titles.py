import ctypes

user32 = ctypes.windll.user32
hwnds = []

def enum_cb(hwnd, lp):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        hwnds.append((hwnd, buff.value))
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

for h, title in hwnds:
    if any(k in title.lower() for k in ["onenote", "saree", "note", "search"]):
        print(f"HWND: {h}, Title: {title}")
