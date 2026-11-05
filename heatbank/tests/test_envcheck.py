"""v0.6.1: a broken llvmlite/numba install must be diagnosed plainly and must never turn into a quiet 'safe' result."""
import os
import shutil
import struct
import tempfile
import unittest

from heatbank import envcheck
from heatbank.strain.phs_wrapper import StrainEngine
from heatbank import cli


def _write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def build_pe(imports):
    """A minimal, valid PE32+ DLL image that only has an import table (test helper, not a runnable program)."""
    names = b"".join(n.encode() + b"\0" for n in imports)
    desc_size = 20 * (len(imports) + 1)
    sect_rva, sect_raw = 0x1000, 0x200
    name_rva = sect_rva + desc_size
    desc = b""
    pos = name_rva
    for n in imports:
        desc += struct.pack("<IIIII", 0, 0, 0, pos, 0)
        pos += len(n) + 1
    desc += b"\0" * 20
    body = desc + names
    dos = b"MZ" + b"\0" * 0x3A + struct.pack("<I", 0x40)
    coff = struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, 0xF0, 0x2000)
    opt = struct.pack("<H", 0x20B) + b"\0" * 106 + struct.pack("<I", 16)     # magic, 106 bytes to offset 108, NumberOfRvaAndSizes
    dirs = b"\0" * 8 + struct.pack("<II", sect_rva, len(desc)) + b"\0" * (8 * 14)
    opt += dirs
    assert len(opt) == 0xF0
    sect = struct.pack("<8sIIIIIIHHI", b".idata", len(body), sect_rva, len(body), sect_raw, 0, 0, 0, 0, 0x40000040)
    head = dos + b"PE\0\0" + coff + opt + sect
    return head + b"\0" * (sect_raw - len(head)) + body


def make_site(imports, libs_files=()):
    root = tempfile.mkdtemp()
    pkg = os.path.join(root, "llvmlite"); os.makedirs(os.path.join(pkg, "binding"))
    _write(os.path.join(pkg, "binding", "llvmlite.dll"), build_pe(imports))
    libs = os.path.join(root, "llvmlite.libs"); os.makedirs(libs)
    for n in libs_files:
        _write(os.path.join(libs, n), b"x")
    return root, pkg


VENDORED = "msvcp140-8f141b4454fa78db34bc1f28c571b4da.dll"
IMPORTS = ["KERNEL32.dll", "api-ms-win-crt-heap-l1-1-0.dll", "VCRUNTIME140.dll", VENDORED]


class PeReader(unittest.TestCase):
    def test_reads_import_names_in_order(self):
        root, pkg = make_site(IMPORTS)
        try:
            self.assertEqual(envcheck.pe_imports(os.path.join(pkg, "binding", "llvmlite.dll")), IMPORTS)
        finally:
            shutil.rmtree(root)

    def test_rejects_non_pe_files(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "x.dll"); _write(p, b"not a dll at all, just text" * 10)
            with self.assertRaises(ValueError):
                envcheck.pe_imports(p)
        finally:
            shutil.rmtree(d)

    def test_real_llvmlite_dll_if_present(self):
        """On a machine with a Windows llvmlite install this reads the real file; elsewhere it is skipped."""
        d = envcheck._find_dir("llvmlite")
        dll = os.path.join(d, "binding", "llvmlite.dll") if d else ""
        if not os.path.isfile(dll):
            self.skipTest("no Windows llvmlite.dll here")
        names = envcheck.pe_imports(dll)
        self.assertTrue(any(n.lower() == "kernel32.dll" for n in names))


class LibsCheck(unittest.TestCase):
    def test_empty_libs_folder_is_reported_with_the_missing_file_name(self):        # the exact situation in the uploaded zip
        root, pkg = make_site(IMPORTS)
        try:
            status, msgs = envcheck.check_llvmlite_files(pkg)
            self.assertEqual(status, "fail")
            self.assertTrue(any(VENDORED in m and "0 files" in m for m in msgs), msgs)
        finally:
            shutil.rmtree(root)

    def test_present_vendored_dll_passes(self):
        root, pkg = make_site(IMPORTS, libs_files=[VENDORED])
        try:
            self.assertEqual(envcheck.check_llvmlite_files(pkg)[0], "ok")
        finally:
            shutil.rmtree(root)

    def test_system_runtime_checked_only_when_a_system_dir_is_given(self):
        root, pkg = make_site(IMPORTS, libs_files=[VENDORED]); sysdir = tempfile.mkdtemp()
        try:
            self.assertEqual(envcheck.check_llvmlite_files(pkg, None)[0], "ok")
            status, msgs = envcheck.check_llvmlite_files(pkg, sysdir)
            self.assertEqual(status, "fail"); self.assertTrue(any("VCRUNTIME140.dll" in m for m in msgs))
            _write(os.path.join(sysdir, "VCRUNTIME140.dll"), b"x")
            self.assertEqual(envcheck.check_llvmlite_files(pkg, sysdir)[0], "ok")
        finally:
            shutil.rmtree(root); shutil.rmtree(sysdir)

    def test_truncated_dll_is_reported_not_crashed(self):
        root, pkg = make_site(IMPORTS)
        try:
            p = os.path.join(pkg, "binding", "llvmlite.dll"); _write(p, b"MZ" + b"\0" * 100)
            self.assertEqual(envcheck.check_llvmlite_files(pkg)[0], "fail")
        finally:
            shutil.rmtree(root)

    def test_non_windows_install_is_skipped(self):
        root = tempfile.mkdtemp(); pkg = os.path.join(root, "llvmlite"); os.makedirs(pkg)
        try:
            self.assertEqual(envcheck.check_llvmlite_files(pkg)[0], "skip")
        finally:
            shutil.rmtree(root)


# the exact error text the user reported
USER_ERROR = ('OSError("Could not find/load shared object file \'llvmlite.dll\' from resource location: \'llvmlite.binding\'. '
              'This could mean that the library literally cannot be found...")')


def dll_missing_phs(*a, **k):
    raise OSError("Could not find/load shared object file 'llvmlite.dll' from resource location: 'llvmlite.binding'.")


class HintAndSafety(unittest.TestCase):
    def test_hint_recognises_the_reported_error_and_ignores_others(self):
        self.assertIn("heatbank doctor", envcheck.hint_for_error(USER_ERROR))
        self.assertIn("--force-reinstall", envcheck.hint_for_error("No module named 'numba'"))
        self.assertIsNone(envcheck.hint_for_error("model blew up"))
        self.assertIsNone(envcheck.hint_for_error(""))

    def test_smoke_test_message_points_to_the_install_and_the_run_is_still_refused(self):
        e = StrainEngine(dll_missing_phs)
        problems = e.smoke_test()
        self.assertEqual(len(problems), 1)
        self.assertIn("MODEL_ERROR", problems[0])              # the failure itself is unchanged
        self.assertIn("ENVIRONMENT PROBLEM", problems[0])      # plus the plain pointer
        self.assertGreater(e.model_errors, 0)

    def test_model_failure_still_ends_in_red_P2(self):
        """The fix must not make a broken environment look safe: a segment that cannot be computed is Red, never lower."""
        r = StrainEngine(dll_missing_phs).run_segment(35.0, 45.0, 1.0, 50.0, 230.0, 0.9, 2, 0, 1, duration_min=60)
        self.assertEqual(r.status, "MODEL_ERROR")
        self.assertTrue(r.fail_safe)                           # Part 2 treats fail_safe as Red

    def test_unrelated_model_error_gets_no_environment_hint(self):
        from tests import fakes
        problems = StrainEngine(fakes.boom_phs).smoke_test()
        self.assertTrue(problems and "ENVIRONMENT PROBLEM" not in problems[0])

    def test_doctor_command_is_registered_and_exits_nonzero_when_unhealthy(self):
        lines = []
        rc = envcheck.run_doctor(out=lines.append)
        if rc != 0:                        # in a sandbox without the real library: must say NOT OK and print the repair
            self.assertTrue(any("RESULT: NOT OK" in l for l in lines))
            self.assertTrue(any("--force-reinstall" in l for l in lines))
        with self.assertRaises(SystemExit) as cm:
            cli.main(["doctor"])
        self.assertIn(cm.exception.code, (0, 1))


if __name__ == "__main__":
    unittest.main()
