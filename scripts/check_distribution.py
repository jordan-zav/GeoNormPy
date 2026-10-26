"""Verify release metadata and regression resources in built distributions."""

import argparse
import ast
import email
import json
import re
import tarfile
import zipfile
from pathlib import Path


def check_distribution(directory):
    wheel, = directory.glob("*.whl")
    source, = directory.glob("*.tar.gz")
    with zipfile.ZipFile(wheel) as archive:
        metadata_path, = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        metadata = email.message_from_bytes(archive.read(metadata_path))
        version_code = ast.parse(archive.read("geonormpy/_version.py").decode("utf-8"))
        runtime_version, = [ast.literal_eval(node.value) for node in version_code.body
                            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__version__" for t in node.targets)]
        if metadata["Version"] != runtime_version:
            raise ValueError("Wheel runtime and distribution versions disagree")
        if metadata["License-Expression"] != "GPL-3.0-or-later":
            raise ValueError("Unexpected wheel license")
        for name in ("geonormpy/norms/revised.py", "geonormpy/norms/profiles.py", "geonormpy/core/iron.py"):
            archive.getinfo(name)
    with tarfile.open(source) as archive:
        prefix = f"geonormpy-{runtime_version}/"
        required = ("PKG-INFO", "LICENSE", "pyproject.toml", "CITATION.cff", "data/test_data.csv",
                    "config/workflow.yaml", "tests/fixtures/legacy_profile_reference.json",
                    "tests/test_profile_properties.py", "docs/PERFILES_CIPW.md",
                    "benchmarks/benchmark_profiles.py", "benchmarks/benchmark_accessories.py",
                    "benchmarks/results/cipw_profiles_20261026.json", "scripts/check_distribution.py")
        for name in required:
            archive.getmember(prefix + name)
        source_metadata = email.message_from_bytes(archive.extractfile(prefix + "PKG-INFO").read())
        if source_metadata["Version"] != runtime_version or source_metadata["License-Expression"] != "GPL-3.0-or-later":
            raise ValueError("Source metadata disagrees with wheel")
        citation = archive.extractfile(prefix + "CITATION.cff").read().decode("utf-8")
        if not any(re.fullmatch(r'version: "' + re.escape(runtime_version) + r'"', line) for line in citation.splitlines()):
            raise ValueError("Citation version disagrees with distribution")
        forbidden = {".git", ".env", ".devresources", "__pycache__", "AGENTS.md", "auth.json"}
        for member in archive.getmembers():
            if forbidden.intersection(Path(member.name).parts):
                raise ValueError(f"Local-only file included in source: {member.name}")
    return {"version": runtime_version, "license": metadata["License-Expression"],
            "wheel": wheel.name, "sdist": source.name, "required_source_files": len(required)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(check_distribution(parser.parse_args().directory), indent=2))
