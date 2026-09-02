# WinCustomizer Studio

**WinCustomizer** is an automated system for debloating, tweaking, and customizing official Windows installation ISO images (`Windows 10` and `Windows 11`).

---

## Capabilities & Features

1. **ISO Mounting & Inspection**:
   - Automatically extracts ISO files and inspects WIM/ESD metadata (Editions, Indices, Architecture, Size).
   - Converts `install.esd` to `install.wim` if required for offline modification.

2. **AppX Package Debloating**:
   - Preset profiles (*Minimal*, *Gaming & Performance*, *Maximum Privacy*, *Custom*).
   - Removes provisioned telemetry bloat, Bing apps, promo packages, Xbox overlays, Solitaire, etc.

3. **Offline Registry Injection (`reg.exe load`)**:
   - **Windows 11 Hardware Check Bypass**: `BypassTPMCheck`, `BypassRAMCheck`, `BypassSecureBootCheck`, `BypassCPUCheck`, `BypassStorageCheck`.
   - **Bypass Internet Setup**: `BypassNRO` (allow offline local account creation).
   - **Classic Context Menu**: Restores Windows 10 full right-click context menu in Windows 11.
   - **Privacy & Telemetry**: Disables telemetry, Bing Search in Start Menu, Advertising ID.
   - **Explorer Tweaks**: Shows file extensions, shows hidden files, defaults to "This PC".
   - **Dark Mode**: Sets dark theme mode by default.

4. **Unattended Answer File (`autounattend.xml`)**:
   - Auto-generates answer files to skip OOBE privacy screens, EULA, region setup, and auto-logon into local accounts.

5. **Bootable ISO Rebuilder**:
   - Re-packages customized files into a bootable Windows ISO using native IMAPI2 COM API or `oscdimg.exe`.
   - Adheres to build versioning rules (e.g. `WinCustom_v1.iso`, `WinCustom_v2.iso`).

6. **Dual User Interfaces**:
   - **Web UI Dashboard**: Modern glassmorphism UI with real-time SSE execution log streaming at `http://localhost:5000`.
   - **Interactive CLI**: Rich terminal wizard for power users.

---

## How to Run

### Option A: Web UI Mode (Default)
```bash
python main.py
```
This launches the Web Server at `http://localhost:5000` and automatically opens your default browser.

### Option B: Interactive CLI Wizard Mode
```bash
python main.py --cli
```

---

## Requirements & Elevation
- **Operating System**: Windows 10 / 11.
- **Admin Rights**: Modifying WIM files via `DISM` and mounting offline registry hives requires Administrator privileges. Run your terminal or Python prompt as Administrator when executing customization jobs.
