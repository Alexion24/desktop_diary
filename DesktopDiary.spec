# -*- mode: python ; coding: utf-8 -*-

from importlib.util import find_spec
from pathlib import Path

a = Analysis(["main.py"])

# The Python install can supply an older runtime than the Qt wheel needs.
# Use the Qt runtime at the bundle root so Python and Qt load the same version.
qt_dir = Path(find_spec("PySide6").origin).parent
runtime_names = {"vcruntime140.dll", "vcruntime140_1.dll"}
# Qt uses the Windows ICU ABI. Other tools on PATH can supply incompatible ICU DLLs.
a.binaries = [
    binary
    for binary in a.binaries
    if binary[0].lower() not in runtime_names | {"icuuc.dll", "icuin.dll"}
    and not binary[0].lower().startswith("icudt")
]
a.binaries.extend(
    (name, str(qt_dir / name), "BINARY") for name in sorted(runtime_names)
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DesktopDiary",
    console=False,
    upx=False,
)
