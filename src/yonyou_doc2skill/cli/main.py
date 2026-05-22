#!/usr/bin/env python3
"""
Yonyou Doc2Skill - Unified CLI Entry Point

Convert documentation, codebases, and repositories into AI skills.

Usage:
    yonyou-doc2skill <command> [options]

Commands:
    create               Create skill from any source (auto-detects type)
    enhance              AI-powered enhancement (auto: API or LOCAL mode)
    enhance-status       Check enhancement status (for background/daemon modes)
    package              Package skill into .zip file
    upload               Upload skill to target platform
    install              One-command workflow (scrape + enhance + package + upload)
    install-agent        Install skill to AI agent directories
    estimate             Estimate page count before scraping
    extract-test-examples Extract usage examples from test files
    resume               Resume interrupted scraping job
    config               Configure GitHub tokens, API keys, and settings
    doctor               Health check for dependencies and configuration

Examples:
    yonyou-doc2skill create https://react.dev
    yonyou-doc2skill create owner/repo
    yonyou-doc2skill create ./document.pdf
    yonyou-doc2skill create configs/unity-spine.json
    yonyou-doc2skill create configs/unity-spine.json --enhance-workflow unity-game-dev
    yonyou-doc2skill enhance output/react/
    yonyou-doc2skill package output/react/
"""

import argparse
import importlib
import sys

from yonyou_doc2skill.cli import __version__


# Command module mapping (command name -> module path)
COMMAND_MODULES = {
    # Skill creation — unified entry point for all 18 source types
    "create": "yonyou_doc2skill.cli.create_command",
    # Enhancement & packaging
    "enhance": "yonyou_doc2skill.cli.enhance_command",
    "enhance-status": "yonyou_doc2skill.cli.enhance_status",
    "package": "yonyou_doc2skill.cli.package_skill",
    "upload": "yonyou_doc2skill.cli.upload_skill",
    "install": "yonyou_doc2skill.cli.install_skill",
    "install-agent": "yonyou_doc2skill.cli.install_agent",
    # Utilities
    "estimate": "yonyou_doc2skill.cli.estimate_pages",
    "extract-test-examples": "yonyou_doc2skill.cli.test_example_extractor",
    "resume": "yonyou_doc2skill.cli.resume_command",
    "quality": "yonyou_doc2skill.cli.quality_metrics",
    "sanitize": "yonyou_doc2skill.cli.sanitize_command",
    "sanitize-assets": "yonyou_doc2skill.cli.sanitize_assets_command",
    # Configuration & workflows
    "config": "yonyou_doc2skill.cli.config_command",
    "confluence": "yonyou_doc2skill.cli.confluence_scraper",
    "ikm": "yonyou_doc2skill.cli.ikm_scraper",
    "chat": "yonyou_doc2skill.cli.chat_scraper",
    "doctor": "yonyou_doc2skill.cli.doctor",
    "workflows": "yonyou_doc2skill.cli.workflows_command",
    "sync-config": "yonyou_doc2skill.cli.sync_config",
    # Advanced (less common)
    "stream": "yonyou_doc2skill.cli.streaming_ingest",
    "update": "yonyou_doc2skill.cli.incremental_updater",
    "multilang": "yonyou_doc2skill.cli.multilang_support",
}


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    from yonyou_doc2skill.cli.parsers import register_parsers

    parser = argparse.ArgumentParser(
        prog="yonyou-doc2skill",
        description="Convert documentation, GitHub repos, and PDFs into AI skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create skill from documentation (auto-detects source type)
  yonyou-doc2skill create https://docs.react.dev --name react

  # Create skill from GitHub repository
  yonyou-doc2skill create microsoft/TypeScript --name typescript

  # Create skill from PDF file
  yonyou-doc2skill create ./documentation.pdf --name mydocs

  # AI-powered enhancement
  yonyou-doc2skill enhance output/react/

  # Package and upload
  yonyou-doc2skill package output/react/
  yonyou-doc2skill upload output/react.zip

For more information: https://docs.yonyou.example/yonyou-doc2skill
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available Yonyou Doc2Skill commands",
        help="Command to run",
    )

    # Register all subcommand parsers
    register_parsers(subparsers)

    return parser


def _reconstruct_argv(command: str, args: argparse.Namespace) -> list[str]:
    """Reconstruct sys.argv from args namespace for command module.

    DEPRECATED: Use ExecutionContext instead. This function is kept for
    backward compatibility and will be removed in a future version.

    Args:
        command: Command name
        args: Parsed arguments namespace

    Returns:
        List of command-line arguments for the command module
    """
    argv = [f"{command}_command.py"]

    # Convert args to sys.argv format
    for key, value in vars(args).items():
        if key == "command":
            continue

        # Handle internal/progressive help flags for create command
        # Convert _help_web to --help-web etc.
        if key.startswith("_help_"):
            if value:
                # Convert _help_web -> --help-web
                help_flag = key.replace("_help_", "help-")
                argv.append(f"--{help_flag}")
            continue

        # Handle positional arguments (no -- prefix)
        if key in [
            "source",  # create command
            "directory",
            "file",
            "job_id",
            "skill_directory",
            "zip_file",
            "input_file",
            "input_path",
            "mode_or_input",
        ]:
            if value is not None and value != "":
                argv.append(str(value))
            continue

        # Handle flags and options
        arg_name = f"--{key.replace('_', '-')}"

        if isinstance(value, bool):
            if value:
                argv.append(arg_name)
        elif isinstance(value, list):
            for item in value:
                argv.extend([arg_name, str(item)])
        elif value is not None:
            argv.extend([arg_name, str(value)])

    return argv


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the unified CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Note: ExecutionContext is initialized by individual commands (e.g., create_command,
    # enhance_command) with the correct config_path and source_info. Do NOT initialize
    # it here — commands need to set config_path which requires source detection first.

    # Get command module
    module_name = COMMAND_MODULES.get(args.command)
    if not module_name:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        parser.print_help()
        return 1

    # create command: call directly with parsed args (no argv reconstruction)
    if args.command == "create":
        # Handle --help-* flags before execute (no source needed for help)
        from yonyou_doc2skill.cli.arguments.create import add_create_arguments

        help_modes = {
            "_help_web": "web",
            "_help_github": "github",
            "_help_local": "local",
            "_help_pdf": "pdf",
            "_help_word": "word",
            "_help_video": "video",
            "_help_config": "config",
            "_help_advanced": "advanced",
            "_help_all": "all",
        }
        for attr, mode in help_modes.items():
            if getattr(args, attr, False):
                help_parser = argparse.ArgumentParser(
                    prog="yonyou-doc2skill create",
                    description=f"Create skill — {mode} options",
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                )
                add_create_arguments(help_parser, mode=mode)
                help_parser.print_help()
                return 0

        from yonyou_doc2skill.cli.create_command import CreateCommand

        command = CreateCommand(args)
        return command.execute()

    # Standard delegation for all other commands
    try:
        # Import and execute command module
        module = importlib.import_module(module_name)

        # Reconstruct sys.argv for command module
        original_argv = sys.argv.copy()
        sys.argv = _reconstruct_argv(args.command, args)

        # Execute command
        try:
            result = module.main()
            return result if result is not None else 0
        finally:
            sys.argv = original_argv

    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        error_msg = str(e) if str(e) else f"{type(e).__name__} occurred"
        print(f"Error: {error_msg}", file=sys.stderr)

        # Show traceback in verbose mode
        import traceback

        if hasattr(args, "verbose") and getattr(args, "verbose", False):
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
