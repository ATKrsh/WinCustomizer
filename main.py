"""
WinCustomizer - Windows ISO Customization Suite Entrypoint
"""

import sys
import os
import argparse
import webbrowser

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from web.server import run_server
from cli import run_cli_wizard

def main():
    parser = argparse.ArgumentParser(description="WinCustomizer - Windows ISO Customization Suite")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI wizard mode instead of Web UI")
    parser.add_argument("--port", type=int, default=5000, help="Web UI server port (default: 5000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    args = parser.parse_args()

    if args.cli:
        run_cli_wizard()
    else:
        url = f"http://localhost:{args.port}"
        if not args.no_browser:
            print(f"Opening Web UI browser window at {url}...")
            webbrowser.open(url)
        run_server(port=args.port)

if __name__ == "__main__":
    main()
