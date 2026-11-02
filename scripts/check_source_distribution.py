"""Run the packaged source tests in a new directory outside the checkout."""

import argparse
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile


def check_source_distribution(source, destination):
    if source.is_dir():
        source, = source.glob("*.tar.gz")
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(source) as archive:
        members = archive.getmembers()
        prefixes = set()
        for member in members:
            parts = PurePosixPath(member.name).parts
            target = destination.joinpath(*parts).resolve()
            if not parts or not target.is_relative_to(destination) or ".." in parts:
                raise ValueError(f"Unsafe source path: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"Unexpected source member type: {member.name}")
            prefixes.add(parts[0])
        if len(prefixes) != 1:
            raise ValueError("Source archive must have one top-level directory")
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    root = destination / prefixes.pop()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("GEONORMPY_AUDIT_WHEEL", None)
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q"], cwd=root, env=env, check=True,
    )
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--extract-to", type=Path, required=True)
    args = parser.parse_args()
    print(check_source_distribution(args.source, args.extract_to))
