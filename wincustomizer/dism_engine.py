"""
DISM Engine Module for WinCustomizer
Manages DISM operations: Mounting WIM, AppX bloatware removal, feature toggles, driver injection, unmounting.
"""

import os
import re
import subprocess
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger("WinCustomizer.DISMEngine")

class DISMEngine:
    def __init__(self, work_dir: str):
        self.work_dir = os.path.abspath(work_dir)
        self.mount_dir = os.path.join(self.work_dir, "mount")
        os.makedirs(self.mount_dir, exist_ok=True)
        self.is_mounted = False

    def mount_wim(self, wim_path: str, index: int = 1, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Mounts a WIM image index to mount_dir using DISM.
        """
        wim_path = os.path.abspath(wim_path)
        if not os.path.exists(wim_path):
            raise FileNotFoundError(f"WIM file not found: {wim_path}")

        if progress_callback:
            progress_callback(f"Mounting WIM image index {index} to {self.mount_dir}...")

        cmd = [
            "dism", "/English", "/Mount-Wim",
            f"/WimFile:{wim_path}",
            f"/Index:{index}",
            f"/MountDir:{self.mount_dir}"
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in p.stdout:
            line_str = line.strip()
            if line_str and progress_callback:
                progress_callback(line_str)

        p.wait()
        if p.returncode != 0:
            raise RuntimeError(f"DISM Mount-Wim failed with code {p.returncode}")

        self.is_mounted = True
        if progress_callback:
            progress_callback("WIM image mounted successfully.")
        return self.mount_dir

    def get_provisioned_appx_packages(self) -> List[Dict[str, str]]:
        """
        Retrieves all provisioned AppX packages installed in the mounted WIM.
        """
        if not self.is_mounted:
            raise RuntimeError("No WIM image currently mounted.")

        cmd = ["dism", "/English", f"/Image:{self.mount_dir}", "/Get-ProvisionedAppxPackages"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        packages = []
        current_pkg = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            name_match = re.match(r"^DisplayName\s*:\s*(.+)$", line, re.IGNORECASE)
            if name_match:
                if current_pkg:
                    packages.append(current_pkg)
                current_pkg = {"display_name": name_match.group(1).strip()}
                continue

            pkg_name_match = re.match(r"^PackageName\s*:\s*(.+)$", line, re.IGNORECASE)
            if pkg_name_match and current_pkg:
                current_pkg["package_name"] = pkg_name_match.group(1).strip()

        if current_pkg:
            packages.append(current_pkg)

        return packages

    def remove_appx_packages(self, package_patterns: List[str], progress_callback: Optional[Callable[[str], None]] = None) -> List[str]:
        """
        Removes provisioned AppX packages matching given name patterns.
        """
        if not self.is_mounted:
            raise RuntimeError("No WIM image currently mounted.")

        installed_packages = self.get_provisioned_appx_packages()
        removed_packages = []

        for pkg in installed_packages:
            display_name = pkg.get("display_name", "")
            full_pkg_name = pkg.get("package_name", "")

            should_remove = False
            for pattern in package_patterns:
                if pattern.lower() in display_name.lower() or pattern.lower() in full_pkg_name.lower():
                    should_remove = True
                    break

            if should_remove and full_pkg_name:
                if progress_callback:
                    progress_callback(f"Removing AppX package: {display_name} ({full_pkg_name})...")

                cmd = [
                    "dism", "/English", f"/Image:{self.mount_dir}",
                    "/Remove-ProvisionedAppxPackage",
                    f"/PackageName:{full_pkg_name}"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    removed_packages.append(full_pkg_name)
                    if progress_callback:
                        progress_callback(f"Successfully removed {display_name}.")
                else:
                    if progress_callback:
                        progress_callback(f"Failed to remove {display_name}: {res.stderr.strip()}")

        return removed_packages

    def enable_feature(self, feature_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Enables an optional Windows Feature in mounted image.
        """
        if not self.is_mounted:
            raise RuntimeError("No WIM image currently mounted.")

        if progress_callback:
            progress_callback(f"Enabling feature: {feature_name}...")

        cmd = [
            "dism", "/English", f"/Image:{self.mount_dir}",
            "/Enable-Feature", f"/FeatureName:{feature_name}", "/All"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def add_drivers(self, drivers_dir: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Injects INF drivers into mounted WIM image.
        """
        if not self.is_mounted:
            raise RuntimeError("No WIM image currently mounted.")

        if not os.path.exists(drivers_dir):
            if progress_callback:
                progress_callback(f"Drivers directory does not exist: {drivers_dir}")
            return False

        if progress_callback:
            progress_callback(f"Injecting drivers from: {drivers_dir}...")

        cmd = [
            "dism", "/English", f"/Image:{self.mount_dir}",
            "/Add-Driver", f"/Driver:{drivers_dir}", "/Recurse"
        ]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in p.stdout:
            line_str = line.strip()
            if line_str and progress_callback:
                progress_callback(line_str)

        p.wait()
        return p.returncode == 0

    def unmount_wim(self, commit: bool = True, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Unmounts WIM image and commits or discards changes.
        """
        if not self.is_mounted:
            if progress_callback:
                progress_callback("WIM is not mounted. Skipping unmount.")
            return True

        action_flag = "/Commit" if commit else "/Discard"
        if progress_callback:
            progress_callback(f"Unmounting WIM image ({action_flag})... This may take a few minutes.")

        cmd = ["dism", "/English", "/Unmount-Wim", f"/MountDir:{self.mount_dir}", action_flag]

        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in p.stdout:
            line_str = line.strip()
            if line_str and progress_callback:
                progress_callback(line_str)

        p.wait()
        if p.returncode == 0:
            self.is_mounted = False
            if progress_callback:
                progress_callback("WIM image unmounted successfully.")
            return True
        else:
            if progress_callback:
                progress_callback(f"DISM Unmount failed with return code {p.returncode}.")
            return False
