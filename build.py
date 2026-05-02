#!/usr/bin/env python3
"""Build script for WeGlide NZ client."""

import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_version():
    """Read version from pyproject.toml."""
    import tomllib
    project_root = Path(__file__).parent
    pyproject = project_root / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}).get("version", "0.0.0")


def main():
    project_root = Path(__file__).parent
    version = get_version()
    release_folder = project_root / "release"

    print(f"Building WeGlide NZ Client v{version}...")

    # Wait a moment to let any processes release the dist folder
    time.sleep(1)

    # Run PyInstaller to a temp build folder
    print("\n[1/3] Building executable with PyInstaller...")
    result = subprocess.run(
        ["pyinstaller", "gnz_online_scoring.spec", "--clean", "--distpath", "build_output"],
        cwd=project_root,
    )
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)

    # Create release folder 
    print("\n[2/3] Creating release package...")
    if release_folder.exists():
        shutil.rmtree(release_folder)
    release_folder.mkdir(exist_ok=True)

    # Copy executable with version in filename
    exe_source = project_root / "build_output" / "gnz-online-scoring.exe"
    exe_dest = release_folder / f"gnz-online-scoring-v{version}.exe"
    shutil.copy2(exe_source, exe_dest)

    # Copy README
    readme_source = project_root / "README.md"
    readme_dest = release_folder / "README.md"
    shutil.copy2(readme_source, readme_dest)

    print("\n[3/3] Done!")
    print(f"\nRelease package created at: {release_folder}")
    print("\nTo run:")
    print(f"  cd {release_folder}")
    print(f"  .\\gnz-online-scoring-v{version}.exe")


if __name__ == "__main__":
    main()