"""Sanitize subcommand parser."""

from .base import SubcommandParser
from yonyou_doc2skill.cli.sanitize_command import add_arguments


class SanitizeParser(SubcommandParser):
    """Parser for sanitize subcommand."""

    @property
    def name(self) -> str:
        return "sanitize"

    @property
    def help(self) -> str:
        return "Sanitize generated skills before sharing"

    @property
    def description(self) -> str:
        return "Remove or redact sensitive text and image regions from generated skill output"

    def add_arguments(self, parser):
        """Add sanitize-specific arguments."""
        add_arguments(parser)
