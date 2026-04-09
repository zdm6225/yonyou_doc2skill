"""
Interactive Setup Wizard for Yonyou Doc2Skill

Guides users through installation options on first run.
"""

from pathlib import Path


def show_installation_guide():
    """Show installation options"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              Yonyou Doc2Skill Setup Guide                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Choose your installation profile:

1️⃣  CLI Only (Skill Generation)
   pip install yonyou-doc2skill

   Features:
   • Scrape documentation websites
   • Analyze GitHub repositories
   • Extract from PDFs
   • Package skills for all platforms

2️⃣  MCP Integration (Claude Code, Cursor, Windsurf)
   pip install yonyou-doc2skill[mcp]

   Features:
   • Everything from CLI Only
   • MCP server for Claude Code
   • One-command skill installation
   • HTTP/stdio transport modes

3️⃣  Multi-LLM Support (Gemini, OpenAI)
   pip install yonyou-doc2skill[all-llms]

   Features:
   • Everything from CLI Only
   • Google Gemini support
   • OpenAI ChatGPT support
   • Enhanced AI features

4️⃣  Everything
   pip install yonyou-doc2skill[all]

   Features:
   • All features enabled
   • Maximum flexibility

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current installation: pip install yonyou-doc2skill
Upgrade with: pip install -U yonyou-doc2skill[mcp]

For configuration wizard:
  yonyou-doc2skill config

For help:
  yonyou-doc2skill --help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def check_first_run():
    """Check if this is first run"""
    flag_file = Path.home() / ".config" / "yonyou-doc2skill" / ".setup_shown"

    if not flag_file.exists():
        show_installation_guide()

        # Create flag to not show again
        flag_file.parent.mkdir(parents=True, exist_ok=True)
        flag_file.touch()

        input("\nPress Enter to continue...")
        return True

    return False


def main():
    """Show wizard"""
    show_installation_guide()


if __name__ == "__main__":
    main()
