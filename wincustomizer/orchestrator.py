"""
Orchestrator Module for WinCustomizer
Executes end-to-end Windows ISO customization pipeline with real-time log callbacks.
"""

import os
import shutil
import logging
from typing import Dict, List, Any, Optional, Callable

from .iso_handler import ISOHandler
from .dism_engine import DISMEngine
from .tweaks import RegistryTweaker
from .autounattend import AutounattendGenerator
from .iso_builder import ISOBuilder
from .presets import DEBLOAT_PROFILES, APPX_CATALOG, TWEAK_PRESETS

logger = logging.getLogger("WinCustomizer.Orchestrator")

class CustomizationOrchestrator:
    def __init__(self, work_dir: str = "work", output_dir: str = "dist"):
        self.work_dir = os.path.abspath(work_dir)
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        self.iso_handler = ISOHandler(self.work_dir)
        self.dism_engine = DISMEngine(self.work_dir)

    def run_pipeline(
        self,
        iso_path: str,
        edition_index: int = 1,
        debloat_profile: Optional[str] = "max_privacy",
        custom_appx: Optional[List[str]] = None,
        tweaks: Optional[Dict[str, bool]] = None,
        unattended_config: Optional[Dict[str, Any]] = None,
        drivers_dir: Optional[str] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Executes complete customization workflow:
        ISO Extraction -> ESD Conversion (if needed) -> WIM Mount -> Debloat -> Tweaks -> Unattended -> Rebuild ISO
        """
        def log(msg: str):
            logger.info(msg)
            if log_callback:
                log_callback(msg)

        log("==========================================")
        log("   Starting WinCustomizer Execution Engine")
        log("==========================================")
        log(f"Input ISO: {iso_path}")
        log(f"Edition Index: {edition_index}")

        # Step 1: Extract ISO
        log("\n[Step 1/6] Extracting ISO content...")
        extracted_dir = self.iso_handler.extract_iso(iso_path, progress_callback=log)

        # Step 2: Inspect & Prepare WIM
        log("\n[Step 2/6] Inspecting image metadata...")
        wim_path = self.iso_handler.wim_path
        if wim_path.endswith(".esd"):
            log("Source installation file is install.esd. Converting to install.wim...")
            wim_path = self.iso_handler.convert_esd_to_wim(index=edition_index, progress_callback=log)

        # Step 3: Mount WIM
        log(f"\n[Step 3/6] Mounting WIM image index {edition_index}...")
        mount_dir = self.dism_engine.mount_wim(wim_path, index=edition_index, progress_callback=log)

        # Step 4: Debloat AppX Packages
        log("\n[Step 4/6] Processing AppX package debloating...")
        package_patterns = []
        if debloat_profile in DEBLOAT_PROFILES:
            profile = DEBLOAT_PROFILES[debloat_profile]
            log(f"Applying Debloat Profile: {profile['name']} - {profile['description']}")
            for cat_key in profile["categories"]:
                if cat_key in APPX_CATALOG:
                    package_patterns.extend(APPX_CATALOG[cat_key]["packages"])

        if custom_appx:
            package_patterns.extend(custom_appx)

        if package_patterns:
            # Deduplicate
            package_patterns = list(set(package_patterns))
            removed = self.dism_engine.remove_appx_packages(package_patterns, progress_callback=log)
            log(f"Debloat complete. Total packages removed: {len(removed)}")
        else:
            log("No AppX debloat patterns selected. Skipping AppX removal.")

        # Step 4b: Inject Drivers if provided
        if drivers_dir and os.path.exists(drivers_dir):
            log(f"\n[Step 4b/6] Injecting drivers from {drivers_dir}...")
            self.dism_engine.add_drivers(drivers_dir, progress_callback=log)

        # Step 5: Apply Registry Tweaks
        log("\n[Step 5/6] Applying offline registry tweaks...")
        tweaker = RegistryTweaker(mount_dir)
        if tweaker.load_hives(progress_callback=log):
            selected_tweaks = tweaks or {k: v["default"] for k, v in TWEAK_PRESETS.items()}
            tweaker.apply_tweaks(selected_tweaks, progress_callback=log)
            tweaker.unload_hives(progress_callback=log)

        # Unmount WIM and commit changes
        log("\nCommiting changes and unmounting WIM image...")
        self.dism_engine.unmount_wim(commit=True, progress_callback=log)

        # Step 6: Generate autounattend.xml answer file
        log("\n[Step 6/6] Generating autounattend.xml answer file...")
        unattended_gen = AutounattendGenerator(unattended_config or {})
        autounattend_path = os.path.join(extracted_dir, "autounattend.xml")
        unattended_gen.save_to_file(autounattend_path)
        log(f"Created answer file: {autounattend_path}")

        # Step 7: Build final customized ISO
        log("\n[Final Step] Rebuilding bootable Windows ISO...")
        iso_builder = ISOBuilder(extracted_dir, self.output_dir)
        output_iso = iso_builder.build_iso(progress_callback=log)

        log("==========================================")
        log("   Customization Completed Successfully!")
        log(f"   Output ISO: {output_iso}")
        log("==========================================")

        return output_iso
