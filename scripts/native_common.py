"""Actual patched Python/Tcl/Tk/PyInstaller runtime notices and authored portable icon. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 46
# definition: icon — line 49
# parameter: path — line 49
# variable: size — line 51
# variable: pixels — line 52
# variable: y — line 53
# variable: x — line 54
# variable: shield — line 55
# variable: check — line 61
# variable: color — line 67
# variable: bitmap — line 75
# definition: notices — line 89
# parameter: path — line 89
# variable: root — line 93
# variable: tcl_version — line 96
# variable: tk_version — line 97
# variable: value — line 100
# variable: runtime_notices — line 105
# variable: library — line 106
# variable: title — line 106
# variable: channel — line 110
# variable: raw — line 112
# variable: raw — line 116
# variable: sources — line 124
# variable: name — line 128
# variable: suffix — line 128
# variable: distribution — line 131
# variable: matches — line 132
# variable: entry — line 133
# variable: blocks — line 143
# variable: source — line 144
# variable: title — line 144
# variable: _ — line 146
# variable: data — line 146
# variable: data — line 149
# variable: title — line 149
# END CODE MAP

import importlib.metadata
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def icon(path: Path) -> None:
    """Generate an authored blue shield/check icon as build output, without shipping a graphics dependency."""
    size = 64
    pixels = bytearray()
    for y in reversed(range(size)):
        for x in range(size):
            shield = (
                8 <= x <= 55
                and 5 <= y <= 42
                or 42 < y <= 59
                and abs(x - 31.5) < (60 - y) * 1.4
            )
            check = (
                15 <= x <= 29
                and abs(y - (x + 8)) < 3
                or 27 <= x <= 48
                and abs(y - (65 - x)) < 3
            )
            color = (
                (255, 255, 255, 255)
                if shield and check
                else (220, 100, 24, 255)
                if shield
                else (0, 0, 0, 0)
            )
            pixels.extend(color)
    bitmap = (
        struct.pack(
            "<IIIHHIIIIII", 40, size, size * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0
        )
        + pixels
        + bytes(size * size // 8)
    )
    path.write_bytes(
        struct.pack("<HHH", 0, 1, 1)
        + struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(bitmap), 22)
        + bitmap
    )


def notices(path: Path) -> None:
    """Retain actual Python, Tcl/Tk and bootloader notices, including Tcl9 DLL-embedded resources."""
    import tkinter

    root = tkinter.Tk()
    root.withdraw()
    try:
        tcl_version = root.tk.call("info", "patchlevel")
        tk_version = root.tk.call("package", "require", "Tk")
        if not all(
            str(value).startswith(("8.6.", "9.0."))
            for value in (tcl_version, tk_version)
        ):
            raise ValueError(
                "Review a different Tcl/Tk runtime family before packaging"
            )
        runtime_notices = []
        for title, library in [
            ("Tcl " + str(tcl_version), root.tk.call("info", "library")),
            ("Tk " + str(tk_version), root.tk.eval("set tk_library")),
        ]:
            channel = root.tk.call("open", str(library) + "/license.terms", "rb")
            try:
                raw = root.tk.call("read", channel, 65537)
            finally:
                root.tk.call("close", channel)
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            if not isinstance(raw, bytes) or not 100 < len(raw) <= 65536:
                raise ValueError(
                    "Actual runtime notice is missing or outside its byte bound"
                )
            runtime_notices.append((title, raw))
    finally:
        root.destroy()
    sources = [
        ("Authored application — MIT", ROOT / "LICENSE"),
        ("Python runtime", Path(sys.base_prefix) / "LICENSE.txt"),
    ]
    for name, suffix in [
        ("pyinstaller", "licenses/COPYING.txt"),
    ]:
        distribution = importlib.metadata.distribution(name)
        matches = [
            entry for entry in distribution.files or [] if str(entry).endswith(suffix)
        ]
        if len(matches) != 1:
            raise ValueError("Review runtime license inventory before packaging")
        sources.append(
            (
                name + " license and applicable exception",
                Path(distribution.locate_file(matches[0])),
            )
        )
    blocks = [
        (title, source.read_bytes()) for title, source in sources
    ] + runtime_notices
    if any(len(data) > 2 * 1024 * 1024 for _, data in blocks):
        raise ValueError("Bundled license exceeds byte bound")
    path.write_bytes(
        b"\n\n".join(title.encode("utf-8") + b"\n" + data for title, data in blocks)
    )
