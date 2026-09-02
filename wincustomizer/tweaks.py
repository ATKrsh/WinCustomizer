"""
Tweaks Module for WinCustomizer
Manages offline registry hive loading, injection of Win11 bypasses, privacy, telemetry, and UI tweaks.
"""

import os
import subprocess
import logging
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("WinCustomizer.Tweaks")

class RegistryTweaker:
    def __init__(self, mount_dir: str):
        self.mount_dir = os.path.abspath(mount_dir)
        self.software_hive = os.path.join(self.mount_dir, "Windows", "System32", "config", "SOFTWARE")
        self.system_hive = os.path.join(self.mount_dir, "Windows", "System32", "config", "SYSTEM")
        self.default_hive = os.path.join(self.mount_dir, "Windows", "System32", "config", "DEFAULT")
        self.ntuser_hive = os.path.join(self.mount_dir, "Users", "Default", "NTUSER.DAT")

        self.loaded_hives = {}

    def load_hives(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Loads offline registry hives into HKLM under temporary mount points.
        """
        hives = [
            ("OFFLINE_SOFTWARE", self.software_hive),
            ("OFFLINE_SYSTEM", self.system_hive),
            ("OFFLINE_DEFAULT", self.default_hive),
            ("OFFLINE_NTUSER", self.ntuser_hive),
        ]

        for key_name, hive_path in hives:
            if not os.path.exists(hive_path):
                if progress_callback:
                    progress_callback(f"Warning: Registry hive not found: {hive_path}")
                continue

            if progress_callback:
                progress_callback(f"Loading registry hive {key_name}...")

            cmd = ["reg.exe", "load", f"HKLM\\{key_name}", hive_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                self.loaded_hives[key_name] = True
            else:
                if progress_callback:
                    progress_callback(f"Failed to load hive {key_name}: {res.stderr.strip()}")

        return len(self.loaded_hives) > 0

    def unload_hives(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Unloads loaded offline registry hives safely.
        """
        for key_name in list(self.loaded_hives.keys()):
            if progress_callback:
                progress_callback(f"Unloading registry hive {key_name}...")

            cmd = ["reg.exe", "unload", f"HKLM\\{key_name}"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                del self.loaded_hives[key_name]
            else:
                if progress_callback:
                    progress_callback(f"Failed to unload hive {key_name}: {res.stderr.strip()}")

    def reg_add(self, key: str, value_name: str, value_type: str, data: str) -> bool:
        """
        Executes reg add command on loaded offline hive.
        """
        cmd = ["reg.exe", "add", key, "/v", value_name, "/t", value_type, "/d", data, "/f"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def reg_add_default(self, key: str, data: str) -> bool:
        """
        Sets default value for a registry key.
        """
        cmd = ["reg.exe", "add", key, "/ve", "/d", data, "/f"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0

    def apply_tweaks(self, selected_tweaks: Dict[str, bool], progress_callback: Optional[Callable[[str], None]] = None):
        """
        Applies requested tweaks to the loaded registry hives.
        """
        if not self.loaded_hives:
            raise RuntimeError("Registry hives are not loaded.")

        # 1. Windows 11 Bypass Hardware & OOBE
        if selected_tweaks.get("win11_bypass", True):
            if progress_callback:
                progress_callback("Applying Windows 11 hardware check bypasses (TPM, RAM, CPU, SecureBoot, Storage, OOBE NRO)...")

            lab_key = r"HKLM\OFFLINE_SYSTEM\Setup\LabConfig"
            self.reg_add(lab_key, "BypassTPMCheck", "REG_DWORD", "1")
            self.reg_add(lab_key, "BypassRAMCheck", "REG_DWORD", "1")
            self.reg_add(lab_key, "BypassSecureBootCheck", "REG_DWORD", "1")
            self.reg_add(lab_key, "BypassCPUCheck", "REG_DWORD", "1")
            self.reg_add(lab_key, "BypassStorageCheck", "REG_DWORD", "1")

            oobe_key = r"HKLM\OFFLINE_SOFTWARE\Microsoft\Windows\CurrentVersion\OOBE"
            self.reg_add(oobe_key, "BypassNRO", "REG_DWORD", "1")

        # 2. Classic Context Menu
        if selected_tweaks.get("classic_context_menu", True):
            if progress_callback:
                progress_callback("Restoring classic Windows 10 full context menu in Windows 11...")
            
            ctx_key = r"HKLM\OFFLINE_NTUSER\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
            self.reg_add_default(ctx_key, "")

        # 3. Disable Telemetry & Tracking
        if selected_tweaks.get("disable_telemetry", True):
            if progress_callback:
                progress_callback("Disabling telemetry, tracking, and diagnostic logs...")

            dc_policy = r"HKLM\OFFLINE_SOFTWARE\Policies\Microsoft\Windows\DataCollection"
            self.reg_add(dc_policy, "AllowTelemetry", "REG_DWORD", "0")

            dc_cv = r"HKLM\OFFLINE_SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
            self.reg_add(dc_cv, "AllowTelemetry", "REG_DWORD", "0")

            ad_key = r"HKLM\OFFLINE_NTUSER\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo"
            self.reg_add(ad_key, "Enabled", "REG_DWORD", "0")

        # 4. Disable Bing Search in Start Menu
        if selected_tweaks.get("disable_bing_start", True):
            if progress_callback:
                progress_callback("Disabling Bing web search integration in Start menu...")

            search_pol = r"HKLM\OFFLINE_SOFTWARE\Policies\Microsoft\Windows\Windows Search"
            self.reg_add(search_pol, "DisableSearchBoxSuggestions", "REG_DWORD", "1")

            search_user = r"HKLM\OFFLINE_NTUSER\Software\Microsoft\Windows\CurrentVersion\Search"
            self.reg_add(search_user, "BingSearchEnabled", "REG_DWORD", "0")

        # 5. Explorer Enhancements
        if selected_tweaks.get("explorer_tweaks", True):
            if progress_callback:
                progress_callback("Enabling File Explorer enhancements (show file extensions, show hidden files, open to This PC)...")

            exp_adv = r"HKLM\OFFLINE_NTUSER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
            self.reg_add(exp_adv, "HideFileExt", "REG_DWORD", "0")
            self.reg_add(exp_adv, "Hidden", "REG_DWORD", "1")
            self.reg_add(exp_adv, "LaunchTo", "REG_DWORD", "1")

        # 6. Default Dark Mode
        if selected_tweaks.get("enable_dark_mode", False):
            if progress_callback:
                progress_callback("Enabling dark theme mode by default...")

            pers_key = r"HKLM\OFFLINE_NTUSER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            self.reg_add(pers_key, "AppsUseLightTheme", "REG_DWORD", "0")
            self.reg_add(pers_key, "SystemUsesLightTheme", "REG_DWORD", "0")

        # 7. Taskbar Left Alignment
        if selected_tweaks.get("taskbar_align_left", False):
            if progress_callback:
                progress_callback("Aligning taskbar icons to the left...")

            exp_adv = r"HKLM\OFFLINE_NTUSER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
            self.reg_add(exp_adv, "TaskbarAl", "REG_DWORD", "0")

        # 8. Disable Windows Copilot
        if selected_tweaks.get("disable_copilot", True):
            if progress_callback:
                progress_callback("Disabling Windows Copilot...")

            copilot_pol = r"HKLM\OFFLINE_SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot"
            self.reg_add(copilot_pol, "TurnOffWindowsCopilot", "REG_DWORD", "1")

            copilot_user = r"HKLM\OFFLINE_NTUSER\Software\Policies\Microsoft\Windows\WindowsCopilot"
            self.reg_add(copilot_user, "TurnOffWindowsCopilot", "REG_DWORD", "1")
