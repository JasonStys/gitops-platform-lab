"""Install explicit hash-pinned official tools without shell installers or unsafe extraction. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 47
# variable: ALLOWED — line 48
# variable: CAP — line 55
# definition: install — line 58
# parameter: name — line 58
# variable: entry — line 60
# variable: output — line 65
# variable: temporary — line 67
# variable: archive — line 68
# variable: hasher — line 69
# variable: size — line 70
# variable: response — line 72
# variable: target — line 73
# variable: chunk — line 75
# variable: size — line 76
# variable: binary — line 83
# variable: member — line 84
# variable: bundle — line 88
# variable: info — line 89
# variable: source — line 92
# variable: target — line 92
# variable: bundle — line 95
# variable: info — line 96
# variable: source — line 99
# variable: target — line 102
# definition: main — line 109
# variable: parser — line 111
# variable: args — line 113
# END CODE MAP

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "helm-linux": "https://get.helm.sh/helm-v3.22.0-linux-amd64.tar.gz",
    "helm-windows": "https://get.helm.sh/helm-v3.22.0-windows-amd64.zip",
    "flux-linux": "https://github.com/fluxcd/flux2/releases/download/v2.9.6/flux_2.9.6_linux_amd64.tar.gz",
    "k3d-linux": "https://github.com/k3d-io/k3d/releases/download/v5.9.0/k3d-linux-amd64",
    "kubectl-linux": "https://dl.k8s.io/release/v1.35.7/bin/linux/amd64/kubectl",
}
CAP = 256 * 1024 * 1024


def install(name: str) -> Path:
    """Fetch a fixed official URL, verify SHA256 before extraction, and atomically publish one regular binary."""
    entry = json.loads((ROOT / "tools.lock.json").read_text(encoding="utf-8"))["tools"][
        name
    ]
    if entry["url"] != ALLOWED[name]:
        raise ValueError("tool URL is not allowlisted")
    output = ROOT / ".tools"
    output.mkdir(mode=0o700, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        archive = Path(temporary) / "download"
        hasher = hashlib.sha256()
        size = 0
        with (
            urllib.request.urlopen(entry["url"], timeout=30) as response,
            archive.open("wb") as target,
        ):
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > CAP:
                    raise ValueError("download too large")
                hasher.update(chunk)
                target.write(chunk)
        if hasher.hexdigest() != entry["sha256"]:
            raise ValueError("tool digest mismatch; not executed")
        binary = Path(temporary) / entry["binary"]
        member = entry["member"]
        if member is None:
            shutil.copyfile(archive, binary)
        elif entry["url"].endswith(".zip"):
            with zipfile.ZipFile(archive) as bundle:
                info = bundle.getinfo(member)
                if info.file_size > CAP or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError("invalid ZIP member")
                with bundle.open(info) as source, binary.open("wb") as target:
                    shutil.copyfileobj(source, target)
        else:
            with tarfile.open(archive, "r:gz") as bundle:
                info = bundle.getmember(member)
                if not info.isfile() or info.size > CAP:
                    raise ValueError("invalid tar member")
                source = bundle.extractfile(info)
                if source is None:
                    raise ValueError("missing binary")
                with source, binary.open("wb") as target:
                    shutil.copyfileobj(source, target)
        os.chmod(binary, 0o700)
        os.replace(binary, output / entry["binary"])
    return output / entry["binary"]


def main() -> int:
    """Install one explicit tool; no host configuration, credentials or unreviewed archive code is invoked."""
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=sorted(ALLOWED))
    args = parser.parse_args()
    print(install(args.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
