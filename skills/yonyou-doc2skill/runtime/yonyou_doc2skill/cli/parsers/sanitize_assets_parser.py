"""Sanitize delivery assets subcommand parser."""

from .base import SubcommandParser
from yonyou_doc2skill.cli.sanitize_assets_command import add_arguments


class SanitizeAssetsParser(SubcommandParser):
    """Parser for sanitize-assets subcommand."""

    @property
    def name(self) -> str:
        return "sanitize-assets"

    @property
    def help(self) -> str:
        return "Sanitize delivery asset packages before sharing"

    @property
    def description(self) -> str:
        return "Sanitize Office documents, archives, images, and text files in delivery assets"

    def add_arguments(self, parser):
        """Add sanitize-assets-specific arguments."""
        add_arguments(parser)
