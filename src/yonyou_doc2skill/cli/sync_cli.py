#!/usr/bin/env python3
"""
Documentation sync CLI.

Monitor documentation for changes and automatically update skills.
"""

import sys
import argparse
import signal
from pathlib import Path

from ..sync import SyncMonitor


def handle_signal(_signum, _frame):
    """Handle interrupt signals."""
    print("\n🛑 Stopping sync monitor...")
    sys.exit(0)


def start_command(args):
    """Start monitoring."""
    monitor = SyncMonitor(
        config_path=args.config, check_interval=args.interval, auto_update=args.auto_update
    )

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        monitor.start()

        print(f"\n📊 Monitoring {args.config}")
        print(f"   Check interval: {args.interval}s ({args.interval // 60}m)")
        print(f"   Auto-update: {'✅ enabled' if args.auto_update else '❌ disabled'}")
        print("\nPress Ctrl+C to stop\n")

        # Keep running
        while True:
            import time

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        monitor.stop()


def check_command(args):
    """Check for changes once."""
    monitor = SyncMonitor(
        config_path=args.config,
        check_interval=3600,  # Not used for single check
    )

    print(f"🔍 Checking {args.config} for changes...")

    report = monitor.check_now(generate_diffs=args.diff)

    print(f"\n📊 Results:")
    print(f"   Total pages: {report.total_pages}")
    print(f"   Added: {len(report.added)}")
    print(f"   Modified: {len(report.modified)}")
    print(f"   Deleted: {len(report.deleted)}")
    print(f"   Unchanged: {report.unchanged}")

    if report.has_changes:
        print(f"\n✨ Detected {report.change_count} changes!")

        if args.verbose:
            if report.added:
                print("\n✅ Added pages:")
                for change in report.added:
                    print(f"   • {change.url}")

            if report.modified:
                print("\n✏️  Modified pages:")
                for change in report.modified:
                    print(f"   • {change.url}")
                    if change.diff and args.diff:
                        print(f"      Diff preview (first 5 lines):")
                        for line in change.diff.split("\n")[:5]:
                            print(f"        {line}")

            if report.deleted:
                print("\n❌ Deleted pages:")
                for change in report.deleted:
                    print(f"   • {change.url}")
    else:
        print("\n✅ No changes detected")


def stats_command(args):
    """Show monitoring statistics."""
    monitor = SyncMonitor(config_path=args.config, check_interval=3600)

    stats = monitor.stats()

    print(f"\n📊 Statistics for {stats['skill_name']}:")
    print(f"   Status: {stats['status']}")
    print(f"   Last check: {stats['last_check'] or 'Never'}")
    print(f"   Last change: {stats['last_change'] or 'Never'}")
    print(f"   Total checks: {stats['total_checks']}")
    print(f"   Total changes: {stats['total_changes']}")
    print(f"   Tracked pages: {stats['tracked_pages']}")
    print(f"   Running: {'✅ Yes' if stats['running'] else '❌ No'}")


def reset_command(args):
    """Reset monitoring state."""
    state_file = Path(f"{args.skill_name}_sync.json")

    if state_file.exists():
        if args.force or input(f"⚠️  Reset state for {args.skill_name}? [y/N]: ").lower() == "y":
            state_file.unlink()
            print(f"✅ State reset for {args.skill_name}")
        else:
            print("❌ Reset cancelled")
    else:
        print(f"ℹ️  No state file found for {args.skill_name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor documentation for changes and update skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start monitoring (checks every hour)
  yonyou-doc2skill-sync start --config configs/react.json

  # Start with custom interval (10 minutes)
  yonyou-doc2skill-sync start --config configs/react.json --interval 600

  # Start with auto-update
  yonyou-doc2skill-sync start --config configs/react.json --auto-update

  # Check once (no continuous monitoring)
  yonyou-doc2skill-sync check --config configs/react.json

  # Check with diffs
  yonyou-doc2skill-sync check --config configs/react.json --diff -v

  # Show statistics
  yonyou-doc2skill-sync stats --config configs/react.json

  # Reset state
  yonyou-doc2skill-sync reset --skill-name react
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start continuous monitoring")
    start_parser.add_argument("--config", required=True, help="Path to skill config file")
    start_parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=3600,
        help="Check interval in seconds (default: 3600 = 1 hour)",
    )
    start_parser.add_argument(
        "--auto-update", action="store_true", help="Automatically rebuild skill on changes"
    )

    # Check command
    check_parser = subparsers.add_parser("check", help="Check for changes once")
    check_parser.add_argument("--config", required=True, help="Path to skill config file")
    check_parser.add_argument("--diff", "-d", action="store_true", help="Generate content diffs")
    check_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show monitoring statistics")
    stats_parser.add_argument("--config", required=True, help="Path to skill config file")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset monitoring state")
    reset_parser.add_argument("--skill-name", required=True, help="Skill name")
    reset_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "start":
            start_command(args)
        elif args.command == "check":
            check_command(args)
        elif args.command == "stats":
            stats_command(args)
        elif args.command == "reset":
            reset_command(args)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
