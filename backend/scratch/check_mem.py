import os
import sys
sys.path.insert(0, ".")

# Get memory in MB on Windows
import ctypes
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('cb', ctypes.c_ulong),
        ('PageFaultCount', ctypes.c_ulong),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t)
    ]

def get_ram_mb():
    p = PROCESS_MEMORY_COUNTERS()
    p.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(p), p.cb)
    return p.WorkingSetSize / (1024 * 1024)

print(f"1. Start: {get_ram_mb():.1f} MB")
import torch
print(f"2. After import torch: {get_ram_mb():.1f} MB")
from app.vision.feature_extractor import ColorInvariantFeatureExtractor
print(f"3. After import extractor: {get_ram_mb():.1f} MB")
ext = ColorInvariantFeatureExtractor()
m = ext.model
print(f"4. After model load: {get_ram_mb():.1f} MB")
