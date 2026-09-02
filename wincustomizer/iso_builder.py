"""
ISO Builder Module for WinCustomizer
Rebuilds bootable Windows ISO files using PowerShell IMAPI2 COM API or oscdimg.
Includes versioned output naming adhering to workspace rules.
"""

import os
import glob
import subprocess
import logging
from typing import Optional, Callable

logger = logging.getLogger("WinCustomizer.ISOBuilder")

class ISOBuilder:
    def __init__(self, extracted_dir: str, output_dir: str):
        self.extracted_dir = os.path.abspath(extracted_dir)
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def get_next_version_path(self, prefix: str = "WinCustom", extension: str = ".iso") -> str:
        """
        Determines the next versioned filename (e.g., WinCustom_v1.iso, WinCustom_v2.iso).
        """
        existing_files = glob.glob(os.path.join(self.output_dir, f"{prefix}_v*{extension}"))
        max_ver = 0
        for f in existing_files:
            basename = os.path.basename(f)
            # Match version index
            parts = basename.replace(prefix + "_v", "").replace(extension, "")
            if parts.isdigit():
                max_ver = max(max_ver, int(parts))

        next_ver = max_ver + 1
        return os.path.join(self.output_dir, f"{prefix}_v{next_ver}{extension}")

    def build_iso(self, output_file: Optional[str] = None, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Builds bootable ISO using oscdimg if available, or PowerShell IMAPI2 script fallback.
        """
        if not os.path.exists(self.extracted_dir):
            raise FileNotFoundError(f"Extracted ISO directory not found: {self.extracted_dir}")

        if not output_file:
            output_file = self.get_next_version_path()

        if progress_callback:
            progress_callback(f"Target ISO build path: {output_file}")

        # Check for oscdimg
        oscdimg_path = shutil_which("oscdimg.exe")
        if oscdimg_path:
            return self._build_with_oscdimg(oscdimg_path, output_file, progress_callback)
        else:
            return self._build_with_powershell(output_file, progress_callback)

    def _build_with_oscdimg(self, oscdimg_exe: str, output_file: str, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Builds ISO using oscdimg.exe with dual BIOS/UEFI boot options.
        """
        if progress_callback:
            progress_callback("Building bootable ISO using oscdimg.exe (BIOS + UEFI dual boot support)...")

        etfsboot = os.path.join(self.extracted_dir, "boot", "etfsboot.com")
        efisys = os.path.join(self.extracted_dir, "efi", "microsoft", "boot", "efisys.bin")

        boot_data = f'2#p0,e,b"{etfsboot}"#pEF,e,b"{efisys}"'

        cmd = [
            oscdimg_exe,
            "-m", "-o", "-u2", "-udfver102",
            f"-bootdata:{boot_data}",
            self.extracted_dir,
            output_file
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
            raise RuntimeError(f"oscdimg build failed with code {p.returncode}")

        if progress_callback:
            progress_callback(f"ISO built successfully: {output_file}")
        return output_file

    def _build_with_powershell(self, output_file: str, progress_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Builds ISO using PowerShell IMAPI2 COM API script fallback.
        """
        if progress_callback:
            progress_callback("Building ISO using native Windows IMAPI2 PowerShell engine...")

        ps_script = f"""
        $sourceDir = '{self.extracted_dir}'
        $targetIso = '{output_file}'

        # Function to create ISO using IMAPI2
        function New-IsoFile {{
            param(
                [string]$Source,
                [string]$TargetPath
            )
            $image = New-Object -ComObject IMAPI2FS.MsftFileSystemImage
            $image.ChooseImageDefaultsForMediaType(12) # DVD media
            $image.FileSystemsToCreate = 3 # ISO9660 + Joliet + UDF
            $image.Root.AddTree($Source, $false)
            
            $resultImage = $image.CreateResultImage()
            $stream = $resultImage.ImageStream

            $fileStream = [System.IO.File]::Create($TargetPath)
            $buffer = New-Object byte[] (64 * 1024)
            while (($bytesRead = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {{
                $fileStream.Write($buffer, 0, $bytesRead)
            }}
            $fileStream.Close()
        }}

        New-IsoFile -Source $sourceDir -TargetPath $targetIso
        Write-Host "ISO file successfully created."
        """

        p = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
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
            raise RuntimeError(f"PowerShell ISO build failed with code {p.returncode}")

        if progress_callback:
            progress_callback(f"ISO built successfully: {output_file}")
        return output_file

def shutil_which(cmd: str) -> Optional[str]:
    import shutil
    return shutil.which(cmd)
