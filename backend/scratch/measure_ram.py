import ctypes
import os

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

def get_ram():
    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.windll.kernel32.GetCurrentProcess(),
        ctypes.byref(pmc),
        pmc.cb
    )
    return pmc.WorkingSetSize / (1024 * 1024)

m0 = get_ram()
from app.vision.feature_extractor import ColorInvariantFeatureExtractor
ext = ColorInvariantFeatureExtractor()
m_after_import = get_ram()
m = ext.model
m_after_model = get_ram()

print(f"Base RAM: {m0:.1f} MB")
print(f"After imports: {m_after_import:.1f} MB (Delta: {m_after_import - m0:.1f} MB)")
print(f"After model load: {m_after_model:.1f} MB (Delta: {m_after_model - m_after_import:.1f} MB)")
print(f"Total RAM: {m_after_model:.1f} MB")
