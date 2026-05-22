"""IKM subcommand parser."""

from .base import SubcommandParser
from yonyou_doc2skill.cli.arguments.ikm import add_ikm_arguments


class IKMParser(SubcommandParser):
    """Parser for ikm subcommand."""

    @property
    def name(self) -> str:
        return "ikm"

    @property
    def help(self) -> str:
        return "Extract from iKM knowledge assets"

    @property
    def description(self) -> str:
        return "Extract iKM knowledge maps, assets, and attachments into a skill"

    def add_arguments(self, parser):
        add_ikm_arguments(parser)

