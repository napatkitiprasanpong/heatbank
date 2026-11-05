"""Environment doctor (v0.6.1). Standard library only, and it never imports llvmlite or numba to inspect them, because importing
them is exactly what fails when their DLLs are broken.

Why it exists: pythermalcomfort's PHS model is compiled by numba through llvmlite. On Windows llvmlite.dll imports a vendored,
hash-named copy of the C++ runtime (msvcp140-<32 hex>.dll) that pip places in site-packages/llvmlite.libs/. If that folder is
empty (a venv that was zipped, committed to git or cleaned by antivirus), Windows reports only "Could not find/load shared
object file llvmlite.dll", which hides the real cause. This module reads the DLL's import table and names the missing file.

This module does not touch model results. A failed model call is still MODEL_ERROR and still ends in Red (principle P2).
"""
import importlib.util
import mmap
import os
import platform
import re
import struct
import sys
from typing import List, Optional, Tuple

REPAIR_STEPS = (
    "Repair (run inside the activated venv):\n"
    "  python -m pip install --force-reinstall --no-deps --no-cache-dir llvmlite==0.50.0 numba==0.68.1\n"
    "If it still fails, install the Microsoft Visual C++ Redistributable 2015-2022 (x64) from Microsoft, then repeat.\n"
    "Last resort, a clean venv (do not copy or zip a venv between folders or machines):\n"
    "  py -3.12 -m venv .venv-new && .venv-new\\Scripts\\activate && pip install -r requirements.txt && pip install -e .")

_VENDORED = re.compile(r"^[\w.+\-]+-[0-9a-fA-F]{32}\.dll$")        # delvewheel / auditwheel style: name-<hash>.dll
_ALWAYS_PRESENT = re.compile(r"^(api-ms-win-.*|kernel32|advapi32|ntdll|user32|ws2_32|shell32|ole32|bcrypt|crypt32)\.dll$", re.I)
_RUNTIME = re.compile(r"^(vcruntime140(_1)?|msvcp140(_1|_2)?|ucrtbase|concrt140)\.dll$", re.I)  # shipped by the VC++ Redistributable


def hint_for_error(text: str) -> Optional[str]:
    """If an error message looks like a native-library load failure, return a one-paragraph pointer to the doctor. Else None."""
    t = (text or "").lower()
    if any(k in t for k in ("llvmlite", "numba", "shared object file", "dll load failed", "could not find/load")):
        return ("ENVIRONMENT PROBLEM, not a model or weather problem: a native library (llvmlite/numba, used by pythermalcomfort) "
                "did not load. Run `heatbank doctor` (or `python -m heatbank.cli doctor`) to see which file is missing, then repair "
                "with: python -m pip install --force-reinstall --no-deps --no-cache-dir llvmlite==0.50.0 numba==0.68.1")
    return None


# ---------------------------------------------------------------------------------------------------------------- PE reader
def pe_imports(path: str) -> List[str]:
    """Names of the DLLs a Windows PE file imports (its import table). Raises ValueError for anything that is not a PE file."""
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        if len(m) < 0x40 or m[:2] != b"MZ":
            raise ValueError("not a PE file (no MZ header)")
        pe = struct.unpack_from("<I", m, 0x3C)[0]
        if pe + 24 > len(m) or m[pe:pe + 4] != b"PE\0\0":
            raise ValueError("not a PE file (no PE signature)")
        n_sections, = struct.unpack_from("<H", m, pe + 6)
        opt_size, = struct.unpack_from("<H", m, pe + 20)
        opt = pe + 24
        magic, = struct.unpack_from("<H", m, opt)
        if magic not in (0x10B, 0x20B):
            raise ValueError("unknown optional header")
        dd = opt + (112 if magic == 0x20B else 96)                 # start of the data directories
        n_dirs, = struct.unpack_from("<I", m, dd - 4)
        if n_dirs < 2:
            return []
        imp_rva, imp_size = struct.unpack_from("<II", m, dd + 8)   # directory 1 = import table
        if imp_rva == 0:
            return []
        secs = []
        sec0 = opt + opt_size
        for i in range(n_sections):
            name, vsize, va, rawsize, rawptr = struct.unpack_from("<8sIIII", m, sec0 + 40 * i)
            secs.append((va, max(vsize, rawsize), rawptr))

        def off(rva):
            for va, size, raw in secs:
                if va <= rva < va + size:
                    return raw + (rva - va)
            raise ValueError(f"RVA {rva:#x} is outside every section")

        def cstr(o):
            end = m.find(b"\0", o, o + 512)
            if end < 0:
                raise ValueError("unterminated name")
            return m[o:end].decode("ascii", "replace")

        names, o = [], off(imp_rva)
        for _ in range(2000):                                       # sanity cap
            _oft, _ts, _fwd, name_rva, _ft = struct.unpack_from("<IIIII", m, o)
            if name_rva == 0:
                break
            names.append(cstr(off(name_rva)))
            o += 20
        return names


# ------------------------------------------------------------------------------------------------------------------ checks
def _find_dir(pkg: str) -> Optional[str]:
    """Package directory WITHOUT importing the package."""
    try:
        spec = importlib.util.find_spec(pkg)
    except (ImportError, ValueError):
        return None
    if spec is None:
        return None
    if spec.submodule_search_locations:
        return list(spec.submodule_search_locations)[0]
    return os.path.dirname(spec.origin) if spec.origin else None


def check_llvmlite_files(pkg_dir: str, system_dir: Optional[str] = None) -> Tuple[str, List[str]]:
    """Inspect llvmlite's Windows DLL for missing dependencies. Returns (status, messages); status is "ok", "fail" or "skip".
    pkg_dir is the llvmlite package directory. system_dir is where the Visual C++ runtime DLLs live (System32 on Windows)."""
    dll = os.path.join(pkg_dir, "binding", "llvmlite.dll")
    if not os.path.isfile(dll):
        return "skip", [f"no {dll} (not a Windows install); file check skipped"]
    try:
        imports = pe_imports(dll)
    except (ValueError, OSError, struct.error) as e:
        return "fail", [f"{dll} cannot be read as a Windows DLL ({e}). It is truncated or damaged: reinstall llvmlite."]
    libs = os.path.join(os.path.dirname(pkg_dir), "llvmlite.libs")
    have = {n.lower() for n in os.listdir(libs)} if os.path.isdir(libs) else set()
    here = {n.lower() for n in os.listdir(os.path.dirname(dll))}
    msgs, missing = [f"llvmlite.dll ({os.path.getsize(dll) / 1e6:.0f} MB) imports {len(imports)} DLLs"], []
    for n in imports:
        low = n.lower()
        if _VENDORED.match(n):
            if low not in have and low not in here:
                missing.append(n)
                msgs.append(f"MISSING vendored DLL: {n}  (expected in {libs}; that folder has {len(have)} files)")
        elif _RUNTIME.match(n) and system_dir:
            if not os.path.isfile(os.path.join(system_dir, n)):
                missing.append(n)
                msgs.append(f"MISSING system runtime: {n}  (install the Microsoft Visual C++ Redistributable 2015-2022 x64)")
        # api-ms-win-*, kernel32 and friends are part of Windows itself: not checked
    return ("fail" if missing else "ok"), msgs


def _system32() -> Optional[str]:
    root = os.environ.get("SystemRoot")
    return os.path.join(root, "System32") if (platform.system() == "Windows" and root) else None


def run_doctor(out=print) -> int:
    """Print a diagnosis. Returns 0 if the model runs, 1 otherwise."""
    from . import __version__
    out(f"HeatBank {__version__} doctor | Python {platform.python_version()} | {platform.platform()}")
    if sys.prefix == sys.base_prefix:
        out("  [warn] not inside a virtual environment: activate .venv first (Windows: .venv\\Scripts\\activate)")
    problems = 0
    for pkg in ("llvmlite", "numba", "pythermalcomfort", "thermofeel"):
        d = _find_dir(pkg)
        out(f"  {pkg}: " + (f"found at {d}" if d else "NOT FOUND (pip install -e .)"))
        problems += d is None
    ll = _find_dir("llvmlite")
    if ll:
        status, msgs = check_llvmlite_files(ll, _system32())
        for m in msgs:
            out(f"    {m}")
        out(f"  llvmlite file check: {status.upper()}")
        problems += status == "fail"
    try:
        import llvmlite.binding as _b
        out("  import llvmlite.binding: OK")
    except Exception as e:                                          # noqa: BLE001 - we want the text of ANY failure
        out(f"  import llvmlite.binding: FAILED {e!r}")
        problems += 1
    try:
        from .strain.phs_wrapper import StrainEngine
        sm = StrainEngine().smoke_test()
        out("  model smoke test: " + ("OK" if not sm else "FAILED " + "; ".join(sm)))
        problems += bool(sm)
    except Exception as e:                                          # noqa: BLE001
        out(f"  model smoke test: could not run {e!r}")
        problems += 1
    out("RESULT: environment OK, the real model runs." if not problems else "RESULT: NOT OK.\n" + REPAIR_STEPS)
    return 0 if not problems else 1
