"""
ISO Handler Module for WinCustomizer
Manages ISO mounting, extraction, WIM/ESD detection, and image info parsing.
"""

import os
import re
import shutil
import subprocess
import logging
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("WinCustomizer.ISOHandler")

class ISOHandler:
    def __init__(self, work_dir: str):
        self.work_dir = os.path.abspath(work_dir)
        self.extracted_dir = os.path.join(self.work_dir, "extracted_iso")
        self.wim_path = ""
        os.makedirs(self.work_dir, exist_ok=True)

    def extract_iso(self, iso_path: str, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Extracts ISO file to work_dir/extracted_iso using PowerShell Mount-DiskImage or 7z.
        """
        iso_path = os.path.abspath(iso_path)
        if not os.path.exists(iso_path):
            raise FileNotFoundError(f"ISO file not found: {iso_path}")

        if progress_callback:
            progress_callback(f"Preparing extraction directory: {self.extracted_dir}")

        if os.path.exists(self.extracted_dir):
            if progress_callback:
                progress_callback("Cleaning previous extracted files...")
            shutil.rmtree(self.extracted_dir, ignore_errors=True)
        os.makedirs(self.extracted_dir, exist_ok=True)

        if progress_callback:
            progress_callback(f"Mounting ISO: {iso_path}...")

        # Powershell mount and copy
        ps_cmd = f"""
        $iso = '{iso_path}'
        $target = '{self.extracted_dir}'
        $mountResult = Mount-DiskImage -ImagePath $iso -PassThru
        $driveLetter = ($mountResult | Get-Volume).DriveLetter
        if (-not $driveLetter) {{
            throw "Failed to get drive letter for mounted ISO."
        }}
        $sourcePath = "$($driveLetter):\\*"
        Write-Host "Copying files from $sourcePath to $target..."
        Copy-Item -Path $sourcePath -Destination $target -Recurse -Force
        Dismount-DiskImage -ImagePath $iso | Out-Null
        """

        p = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
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
            raise RuntimeError(f"ISO extraction failed with code {p.returncode}")

        if progress_callback:
            progress_callback("ISO extracted successfully.")

        self.wim_path = self.find_install_image()
        return self.extracted_dir

    def find_install_image(self) -> str:
        """
        Locates install.wim or install.esd in extracted_iso/sources/
        """
        sources_dir = os.path.join(self.extracted_dir, "sources")
        if not os.path.exists(sources_dir):
            raise FileNotFoundError("Extracted ISO does not contain a 'sources' directory.")

        wim_candidate = os.path.join(sources_dir, "install.wim")
        esd_candidate = os.path.join(sources_dir, "install.esd")

        if os.path.exists(wim_candidate):
            return wim_candidate
        elif os.path.exists(esd_candidate):
            return esd_candidate

        raise FileNotFoundError("Neither install.wim nor install.esd found in ISO sources directory.")

    def get_image_info(self, image_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Queries DISM to get edition index, name, description, size, architecture.
        """
        target_path = image_path or self.wim_path
        if not target_path or not os.path.exists(target_path):
            raise FileNotFoundError(f"Install image file not found: {target_path}")

        cmd = ["dism", "/English", "/Get-WimInfo", f"/WimFile:{target_path}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        return self._parse_wim_info(result.stdout)

    def _parse_wim_info(self, raw_output: str) -> List[Dict[str, Any]]:
        """
        Parses dism /Get-WimInfo text output into structured list of dictionaries.
        """
        images = []
        current_img = {}

        for line in raw_output.splitlines():
            line = line.strip()
            if not line:
                continue

            index_match = re.match(r"^Index\s*:\s*(\d+)$", line, re.IGNORECASE)
            if index_match:
                if current_img:
                    images.append(current_img)
                current_img = {"index": int(index_match.group(1))}
                continue

            name_match = re.match(r"^Name\s*:\s*(.+)$", line, re.IGNORECASE)
            if name_match and current_img:
                current_img["name"] = name_match.group(1).strip()

            desc_match = re.match(r"^Description\s*:\s*(.+)$", line, re.IGNORECASE)
            if desc_match and current_img:
                current_img["description"] = desc_match.group(1).strip()

            size_match = re.match(r"^Size\s*:\s*(.+)$", line, re.IGNORECASE)
            if size_match and current_img:
                current_img["size"] = size_match.group(1).strip()

            arch_match = re.match(r"^Architecture\s*:\s*(.+)$", line, re.IGNORECASE)
            if arch_match and current_img:
                current_img["architecture"] = arch_match.group(1).strip()

            ver_match = re.match(r"^Version\s*:\s*(.+)$", line, re.IGNORECASE)
            if ver_match and current_img:
                current_img["version"] = ver_match.group(1).strip()

        if current_img:
            images.append(current_img)

        return images

    def convert_esd_to_wim(self, index: int = 1, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Converts install.esd to install.wim using DISM export-image if source is ESD.
        """
        if not self.wim_path.endswith(".esd"):
            return self.wim_path

        dest_wim = os.path.join(os.path.dirname(self.wim_path), "install.wim")
        if progress_callback:
            progress_callback(f"Converting ESD image index {index} to WIM: {dest_wim}...")

        cmd = [
            "dism", "/English", "/Export-Image",
            f"/SourceImageFile:{self.wim_path}",
            f"/SourceIndex:{index}",
            f"/DestinationImageFile:{dest_wim}",
            "/Compress:max",
            "/CheckIntegrity"
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
            raise RuntimeError(f"ESD to WIM conversion failed with code {p.returncode}")

        # Remove old ESD file and update wim_path
        os.remove(self.wim_path)
        self.wim_path = dest_wim
        return dest_wim
