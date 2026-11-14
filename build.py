
"""
SafeNote Windows Build & MSI Installer
Shoriu Foundation

Builds:
1. Standalone application using PyInstaller
2. Windows x64 MSI installer using WiX Toolset v4+

Run:
    python build.py

Optional version override:
    $env:SAFENOTE_VERSION = "1.0.1"
    python build.py
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

APP_NAME = "SafeNote"
MANUFACTURER = "Shoriu Foundation"
APP_VERSION = os.getenv("SAFENOTE_VERSION", "1.0.0")

# IMPORTANT:
# Keep this GUID unchanged between all releases.
UPGRADE_CODE = "{8C7F0F6A-9D21-4D7B-A3E5-6B1C2F9A7401}"


def run_command(command, description):
    print(f"\n[BUILD] {description}")
    print(" ".join(map(str, command)))

    result = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        check=False
    )

    if result.returncode != 0:
        print(f"[ERROR] {description} failed (exit code {result.returncode}).")
        return False

    return True


def validate_version():
    if not re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION):
        print(
            "[ERROR] SAFENOTE_VERSION must use "
            "MAJOR.MINOR.PATCH format (example: 1.0.0)."
        )
        return False

    parts = [int(part) for part in APP_VERSION.split(".")]

    if any(part > 65535 for part in parts):
        print("[ERROR] MSI version components cannot exceed 65535.")
        return False

    return True


def build_executable():
    print("\n" + "=" * 60)
    print("Building SafeNote standalone executable")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name=SafeNote",
        "--windowed",
        "--onedir",
        f"--distpath={BASE_DIR / 'dist'}",
        f"--workpath={BASE_DIR / 'build' / 'pyinstaller'}",
        f"--specpath={BASE_DIR / 'build'}",
        "--collect-all=PySide6",
        "--collect-all=sounddevice",
        "--collect-all=cryptography",
        "--collect-all=keyring",
        "--exclude-module=pytest",
        "--exclude-module=tests",
        str(BASE_DIR / "main.py"),
    ]

    if not run_command(cmd, "PyInstaller packaging"):
        return False

    exe_path = BASE_DIR / "dist" / "SafeNote" / "SafeNote.exe"

    if not exe_path.is_file():
        print(f"[ERROR] Executable not found: {exe_path}")
        return False

    print(f"\n[OK] Executable created: {exe_path}")
    return True



def generate_wix_source():
    """
    Generate WiX v4-compatible source for WiX Toolset 7.
    """

    build_dir = BASE_DIR / "build" / "installer"
    build_dir.mkdir(parents=True, exist_ok=True)

    source_dir = (BASE_DIR / "dist" / "SafeNote").resolve()

    if not source_dir.is_dir():
        raise FileNotFoundError(
            f"Application directory does not exist: {source_dir}"
        )

    source_path = source_dir.as_posix()

    wix_source = f'''<?xml version="1.0" encoding="utf-8"?>

<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">

    <Package
        Name="{APP_NAME}"
        Manufacturer="{MANUFACTURER}"
        Version="{APP_VERSION}"
        UpgradeCode="{UPGRADE_CODE}"
        Scope="perMachine">

        <MajorUpgrade
            DowngradeErrorMessage="A newer version of SafeNote is already installed."
            Schedule="afterInstallInitialize"/>

        <MediaTemplate EmbedCab="yes"/>

        <StandardDirectory Id="ProgramFiles64Folder">
            <Directory Id="INSTALLFOLDER" Name="{APP_NAME}"/>
        </StandardDirectory>

        <!-- Application files -->
        <ComponentGroup
            Id="AppFilesGroup"
            Directory="INSTALLFOLDER">

            <Files Include="$(var.SourceDir)\\**"/>

        </ComponentGroup>

        <!-- Start Menu shortcut -->
        <StandardDirectory Id="ProgramMenuFolder">
            <Directory Id="ProgramMenuDir" Name="{APP_NAME}">

                <Component
                    Id="StartMenuShortcut"
                    Guid="{{A7F19E34-2B65-4C8D-9F10-6E3A5D8B2C41}}">

                    <Shortcut
                        Id="SafeNoteStartMenuShortcut"
                        Name="{APP_NAME}"
                        Description="Your safety. Your privacy. Your choice."
                        Target="[INSTALLFOLDER]SafeNote.exe"
                        WorkingDirectory="INSTALLFOLDER"/>

                    <RemoveFolder
                        Id="RemoveSafeNoteStartMenuFolder"
                        On="uninstall"/>

                    <RegistryValue
                        Root="HKLM"
                        Key="Software\\Shoriu Foundation\\SafeNote"
                        Name="Installed"
                        Type="integer"
                        Value="1"
                        KeyPath="yes"/>

                </Component>
            </Directory>
        </StandardDirectory>

        <Feature
            Id="MainApplication"
            Title="{APP_NAME}"
            Level="1">

            <ComponentGroupRef Id="AppFilesGroup"/>
            <ComponentRef Id="StartMenuShortcut"/>

        </Feature>

    </Package>

</Wix>
'''

    wxs_path = build_dir / "SafeNote.wxs"
    wxs_path.write_text(wix_source, encoding="utf-8")

    print(f"[OK] WiX source generated: {wxs_path}")

    return wxs_path, source_path



def build_msi():
    print("\n" + "=" * 60)
    print("Building SafeNote Windows MSI Installer")
    print("=" * 60)

    wix = shutil.which("wix")

    if not wix:
        print("[ERROR] WiX Toolset was not found.")
        print("Install WiX Toolset using:")
        print("dotnet tool install --global wix")
        return False

    source_dir = BASE_DIR / "dist" / "SafeNote"

    if not (source_dir / "SafeNote.exe").is_file():
        print("[ERROR] PyInstaller output is missing.")
        return False

    wxs_path, source_path = generate_wix_source()

    msi_path = BASE_DIR / "dist" / "SafeNote-Setup-x64.msi"
    pdb_path = BASE_DIR / "build" / "installer" / "SafeNote.wixpdb"

    # Remove previous build outputs to avoid stale artifacts.
    for old_file in (msi_path, pdb_path):
        if old_file.exists():
            old_file.unlink()

    cmd = [
        wix,
        "build",
        "-arch",
        "x64",
        "-d",
        f"SourceDir={source_path}",
        "-o",
        str(msi_path),
        "-pdb",
        str(pdb_path),
        str(wxs_path),
    ]

    if not run_command(cmd, "WiX MSI generation"):
        return False

    if not msi_path.is_file():
        print("[ERROR] MSI file was not generated.")
        return False

    if msi_path.stat().st_size == 0:
        print("[ERROR] MSI file is empty.")
        return False

    print(f"\n[OK] MSI installer created: {msi_path}")
    print(
        f"[OK] Installer size: "
        f"{msi_path.stat().st_size / (1024 * 1024):.2f} MB"
    )

    return True


def build():
    print("=" * 60)
    print("SafeNote Windows Release Builder")
    print(f"Version: {APP_VERSION}")
    print(f"Manufacturer: {MANUFACTURER}")
    print("=" * 60)

    if sys.platform != "win32":
        print("[ERROR] This installer build currently targets Windows only.")
        return False

    if not validate_version():
        return False

    if not build_executable():
        return False

    if not build_msi():
        return False

    print("\n" + "=" * 60)
    print("SAFENOTE BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(
        f"Installer: "
        f"{BASE_DIR / 'dist' / 'SafeNote-Setup-x64.msi'}"
    )
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = build()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n[ABORTED] Build cancelled.")
        sys.exit(130)

    except Exception as exc:
        print(f"\n[ERROR] Unexpected build error: {exc}")
        sys.exit(1)
