"""
Interactive Command-Line Interface for WinCustomizer
"""

import os
import sys
import argparse
from typing import List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from wincustomizer.iso_handler import ISOHandler
from wincustomizer.orchestrator import CustomizationOrchestrator
from wincustomizer.presets import DEBLOAT_PROFILES, TWEAK_PRESETS

console = Console()

def run_cli_wizard():
    console.print(Panel.fit(
        "[bold cyan]WinCustomizer CLI Wizard[/bold cyan]\n"
        "[dim]Automated Windows 10/11 ISO Debloat, Tweak & Customization Suite[/dim]",
        border_style="cyan"
    ))

    # Input ISO Path
    while True:
        iso_path = Prompt.ask("[bold yellow]Enter absolute path to Windows Installation ISO[/bold yellow]")
        iso_path = iso_path.strip('"').strip("'")
        if os.path.exists(iso_path):
            break
        console.print(f"[bold red]File not found: {iso_path}. Please enter a valid ISO file path.[/bold red]")

    # Inspect ISO
    console.print("\n[cyan]Extracting & Inspecting ISO metadata...[/cyan]")
    handler = ISOHandler(work_dir="work")
    
    def log_cb(msg):
        console.print(f"[dim]{msg}[/dim]")

    handler.extract_iso(iso_path, progress_callback=log_cb)
    editions = handler.get_image_info()

    if not editions:
        console.print("[bold red]No editions found in ISO image.[/bold red]")
        return

    # Render Editions Table
    table = Table(title="Available Windows Editions in ISO", border_style="cyan")
    table.add_column("Index", style="bold green", justify="center")
    table.add_column("Edition Name", style="bold white")
    table.add_column("Architecture", style="dim")
    table.add_column("Size", style="dim")

    for ed in editions:
        table.add_row(
            str(ed.get("index")),
            ed.get("name", "Windows Edition"),
            ed.get("architecture", "x64"),
            ed.get("size", "N/A")
        )

    console.print(table)

    edition_indices = [str(e["index"]) for e in editions]
    selected_index = int(Prompt.ask(
        "[bold yellow]Select Edition Index to customize[/bold yellow]",
        choices=edition_indices,
        default=edition_indices[0]
    ))

    # Debloat Profile Choice
    console.print("\n[bold cyan]Debloat Profile Options:[/bold cyan]")
    for k, profile in DEBLOAT_PROFILES.items():
        console.print(f"  - [bold yellow]{k}[/bold yellow]: {profile['name']} ({profile['description']})")

    debloat_profile = Prompt.ask(
        "[bold yellow]Select Debloat Profile[/bold yellow]",
        choices=list(DEBLOAT_PROFILES.keys()),
        default="max_privacy"
    )

    # Tweaks Configuration
    console.print("\n[bold cyan]System & Registry Tweaks:[/bold cyan]")
    tweaks = {}
    for tweak_key, tweak in TWEAK_PRESETS.items():
        enabled = Confirm.ask(f"Enable tweak: {tweak['name']}?", default=tweak["default"])
        tweaks[tweak_key] = enabled

    # Unattended XML Config
    console.print("\n[bold cyan]Unattended Answer File Settings:[/bold cyan]")
    username = Prompt.ask("Default Administrator Username", default="Admin")
    password = Prompt.ask("User Password (press enter for no password)", default="", password=True)
    computer_name = Prompt.ask("Computer Name", default="WinCustom-PC")
    skip_oobe = Confirm.ask("Skip OOBE Privacy & Region Screens?", default=True)

    unattended_config = {
        "username": username,
        "password": password,
        "computer_name": computer_name,
        "skip_oobe": skip_oobe,
        "auto_logon": True
    }

    # Drivers directory optional
    drivers_dir = Prompt.ask("Drivers Directory (optional, press enter to skip)", default="")
    drivers_dir = drivers_dir.strip('"').strip("'") if drivers_dir else None

    # Confirm and run
    if not Confirm.ask("\n[bold green]Start ISO Customization pipeline now?[/bold green]", default=True):
        console.print("[yellow]Customization cancelled.[/yellow]")
        return

    console.print("\n[bold cyan]=====================================================[/bold cyan]")
    console.print("[bold cyan] Executing WinCustomizer Engine... [/bold cyan]")
    console.print("[bold cyan]=====================================================[/bold cyan]\n")

    orchestrator = CustomizationOrchestrator(work_dir="work", output_dir="dist")
    try:
        output_iso = orchestrator.run_pipeline(
            iso_path=iso_path,
            edition_index=selected_index,
            debloat_profile=debloat_profile,
            tweaks=tweaks,
            unattended_config=unattended_config,
            drivers_dir=drivers_dir,
            log_callback=log_cb
        )
        console.print(f"\n[bold green]Success! Customized ISO saved at: {output_iso}[/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]Pipeline error: {str(e)}[/bold red]")

if __name__ == "__main__":
    run_cli_wizard()
