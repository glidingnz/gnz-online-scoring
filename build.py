#!/usr/bin/env python3
"""Build script for WeGlide NZ client."""

import shutil
import subprocess
import sys
import time
from pathlib import Path


def main():
    project_root = Path(__file__).parent
    dist_folder = project_root / "dist"
    release_folder = project_root / "release"

    print("Building WeGlide NZ Client...")

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

    # Copy executable from build_output folder
    exe_source = project_root / "build_output" / "gnz-online-scoring.exe"
    exe_dest = release_folder / "gnz-online-scoring.exe"
    shutil.copy2(exe_source, exe_dest)

    # Copy config
    config_source = project_root / "config.yaml"
    config_dest = release_folder / "config.yaml"
    shutil.copy2(config_source, config_dest)

    # Copy README
    readme_source = project_root / "README.md"
    readme_dest = release_folder / "README.md"
    shutil.copy2(readme_source, readme_dest)

    # Copy output folder (for GUI)
    output_source = project_root / "output"
    if output_source.exists():
        output_dest = release_folder / "output"
        shutil.copytree(output_source, output_dest, dirs_exist_ok=True)
        print(f"  Copied output/ folder")

    print("\n[3/3] Done!")
    print(f"\nRelease package created at: {release_folder}")
    print(f"\nTo run:")
    print(f"  cd {release_folder}")
    print("  .\\gnz-online-scoring.exe")


if __name__ == "__main__":
    main()