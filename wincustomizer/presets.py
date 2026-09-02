"""
Debloat and Tweak Presets for WinCustomizer
"""

APPX_CATALOG = {
    "telemetry_bing": {
        "name": "Bing & Telemetry Apps",
        "description": "Bing News, Weather, Finance, Sports, Maps, Feedback Hub, Content Delivery Manager",
        "packages": [
            "Microsoft.BingNews",
            "Microsoft.BingWeather",
            "Microsoft.BingFinance",
            "Microsoft.BingSports",
            "Microsoft.BingSearch",
            "Microsoft.WindowsMaps",
            "Microsoft.WindowsFeedbackHub",
            "Microsoft.GetHelp",
            "Microsoft.Getstarted",
            "Microsoft.MicrosoftSolitaireCollection",
            "Microsoft.People",
            "Microsoft.YourPhone",
            "Microsoft.ZuneVideo",
            "Microsoft.ZuneMusic",
        ]
    },
    "gaming": {
        "name": "Xbox & Gaming Apps",
        "description": "Xbox Game Overlay, Xbox Speech, Game Pass App, Gaming Services (Optional for non-gamers)",
        "packages": [
            "Microsoft.XboxApp",
            "Microsoft.XboxGameOverlay",
            "Microsoft.XboxGamingOverlay",
            "Microsoft.XboxIdentityProvider",
            "Microsoft.XboxSpeechToTextOverlay",
            "Microsoft.GamingApp",
        ]
    },
    "bloatware_thirdparty": {
        "name": "Third-Party & Trial Bloatware",
        "description": "Preinstalled promo apps (Spotify, Disney+, TikTok, Netflix promos, Candy Crush)",
        "packages": [
            "SpotifyAB.SpotifyMusic",
            "Disney.DisneyPlus",
            "Clipchamp.Clipchamp",
            "Microsoft.54998164FB63E",  # Cortana
            "Microsoft.Office.OneNote",
            "Microsoft.MicrosoftOfficeHub",
            "Microsoft.SkypeApp",
            "Microsoft.Todos",
            "Microsoft.PowerAutomateDesktop",
        ]
    },
    "utilities": {
        "name": "Non-Essential Utilities",
        "description": "Sound Recorder, Sticky Notes, Paint 3D, 3D Builder, Quick Assist, Mail & Calendar",
        "packages": [
            "Microsoft.WindowsSoundRecorder",
            "Microsoft.MicrosoftStickyNotes",
            "Microsoft.MSPaint",
            "Microsoft.3DBuilder",
            "Microsoft.Print3D",
            "Microsoft.QuickAssist",
            "microsoft.windowscommunicationsapps", # Mail & Calendar
            "Microsoft.WindowsAlarms",
        ]
    }
}

TWEAK_PRESETS = {
    "win11_bypass": {
        "name": "Windows 11 Hardware & OOBE Bypasses",
        "description": "Bypass TPM 2.0, SecureBoot, RAM (4GB), CPU, Storage checks & Bypass Internet Account setup (BypassNRO).",
        "default": True
    },
    "classic_context_menu": {
        "name": "Restore Classic Context Menu",
        "description": "Restores the Windows 10 full right-click context menu in Windows 11 (disables show more options).",
        "default": True
    },
    "disable_telemetry": {
        "name": "Disable Telemetry & Tracking",
        "description": "Disables Telemetry (DiagTrack), Advertising ID, Activity History, and Customer Experience Improvement Program.",
        "default": True
    },
    "disable_bing_start": {
        "name": "Disable Bing Search in Start Menu",
        "description": "Prevents Start menu search from querying web Bing results, making search faster and private.",
        "default": True
    },
    "explorer_tweaks": {
        "name": "File Explorer Enhancements",
        "description": "Show hidden files, show file extensions, open File Explorer to 'This PC' instead of Quick Access.",
        "default": True
    },
    "enable_dark_mode": {
        "name": "Default Dark Mode",
        "description": "Sets system and applications theme to Dark Mode by default.",
        "default": False
    },
    "taskbar_align_left": {
        "name": "Align Taskbar to Left (Win 11)",
        "description": "Aligns Windows 11 taskbar icons to the left like classic Windows.",
        "default": False
    },
    "disable_copilot": {
        "name": "Disable Windows Copilot",
        "description": "Disables Windows Copilot icon and AI integration on desktop.",
        "default": True
    }
}

DEBLOAT_PROFILES = {
    "minimal": {
        "name": "Minimal Debloat",
        "description": "Removes only Bing promos, feedback hub, and non-essential third party ads.",
        "categories": ["telemetry_bing", "bloatware_thirdparty"]
    },
    "gaming": {
        "name": "Gaming & Performance",
        "description": "Removes all non-essential apps while keeping essential gaming drivers. Retains Xbox app if selected.",
        "categories": ["telemetry_bing", "bloatware_thirdparty", "utilities"]
    },
    "max_privacy": {
        "name": "Maximum Privacy & Clean",
        "description": "Removes all provisioned AppX bloatware, Xbox overlays, Bing telemetry, and promos.",
        "categories": ["telemetry_bing", "gaming", "bloatware_thirdparty", "utilities"]
    }
}
