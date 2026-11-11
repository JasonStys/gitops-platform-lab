"""Build the complete real offline workbench as one Windows portable executable. Jason Stys.

No publication, installation, shortcut change, host collection or Docker action.
"""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 42
# definition: main — line 46
# variable: version — line 60
# variable: source — line 65
# variable: dirty — line 68
# variable: output — line 73
# variable: release — line 73
# variable: distribution — line 79
# variable: licenses — line 80
# variable: entry — line 82
# variable: raw_license — line 87
# variable: resource_paths — line 96
# variable: name — line 108
# variable: metadata — line 110
# variable: name — line 118
# variable: path — line 118
# variable: command — line 124
# variable: name — line 145
# variable: path — line 145
# variable: command — line 148
# variable: command — line 149
# variable: executable — line 163
# variable: stream — line 164
# variable: digest — line 165
# END CODE MAP

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from native_common import icon, notices

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    """Freeze exact allowlisted public resources and bind actual source/dirty state without publishing."""
    if sys.platform != "win32" or sys.version_info[:3] != (3, 14, 10):
        raise RuntimeError(
            "This portable recipe requires patched Windows CPython3.14.10"
        )
    import importlib.metadata

    import yaml
    from yaml import _yaml

    from lab import desktop_project as project
    from lab.desktop_io import read_bytes

    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf8"))[
        "project"
    ]["version"]
    if version != project.VERSION:
        raise ValueError("Native version coherence failed")
    source = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        ).strip()
    )
    release, output = ROOT / "release", ROOT / "out"
    release.mkdir(exist_ok=True)
    output.mkdir(exist_ok=True)
    notices(release / "notices.txt")
    if yaml.__version__ != "6.0.3":
        raise ValueError("Review actual PyYAML runtime before packaging")
    distribution = importlib.metadata.distribution("PyYAML")
    licenses = [
        entry
        for entry in distribution.files or []
        if str(entry).replace("\\", "/").endswith("/licenses/LICENSE")
    ]
    if len(licenses) != 1:
        raise ValueError("Actual PyYAML license inventory changed")
    raw_license = Path(distribution.locate_file(licenses[0])).read_bytes()
    if not 100 <= len(raw_license) <= 65536:
        raise ValueError("Actual PyYAML license size changed")
    (release / "notices.txt").write_bytes(
        (release / "notices.txt").read_bytes()
        + b"\n\nPyYAML6.0.3 original MIT license\n"
        + raw_license
    )
    icon(output / "app.ico")
    resource_paths = {
        name: (
            release / name
            if name == "notices.txt"
            else output / name
            if name == "app.ico"
            else Path(sys.base_prefix) / name
            if name == "python314.dll"
            else Path(_yaml.__file__)
            if name == "yaml/_yaml.cp314-win_amd64.pyd"
            else ROOT / name
        )
        for name in project.RESOURCES
    }
    metadata = {
        "schema": 1,
        "product": project.PRODUCT,
        "version": version,
        "source": source,
        "source_dirty": dirty,
        "resources": {
            name: hashlib.sha256(read_bytes(path, 32 * 1024 * 1024)).hexdigest()
            for name, path in resource_paths.items()
        },
    }
    (release / "native-release.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf8"
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--icon",
        str(output / "app.ico"),
        "--name",
        "GitOpsPlatformLab",
        "--distpath",
        "release/portable",
        "--workpath",
        "out/native-build",
        "--specpath",
        "out",
        "--paths",
        str(ROOT),
    ]
    for name, path in resource_paths.items():
        if name in ("python314.dll", "yaml/_yaml.cp314-win_amd64.pyd"):
            continue  # PyInstaller collects the actual interpreter DLL as a binary, not duplicate data.
        command += ["--add-data", str(path) + os.pathsep + Path(name).parent.as_posix()]
    command += [
        "--add-data",
        str(release / "native-release.json") + os.pathsep + ".",
        "scripts/native_entry.py",
    ]
    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        env={
            **os.environ,
            "PYINSTALLER_CONFIG_DIR": str(output / "native-freezer-cache"),
        },
    )
    executable = release / "portable/GitOpsPlatformLab.exe"
    with executable.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    executable.with_name(executable.name + ".sha256").write_text(
        digest + "  " + executable.name + "\n", encoding="ascii"
    )
    print(
        "Portable candidate built; source_dirty="
        + str(dirty)
        + "; not published or installed"
    )


if __name__ == "__main__":
    main()
